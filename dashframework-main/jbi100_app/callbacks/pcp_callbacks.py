from __future__ import annotations

import numpy as np
import pandas as pd
from dash import Input, Output, State, callback, no_update, ctx

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims
from jbi100_app.plots.pcp import build_pcp_figure
from jbi100_app.state.filters import (
    parse_parcoords_constraintrange_patch,
    countries_from_parcoords_constraints,
)
from jbi100_app.state.selection_store import normalize_selection_store


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country"])
    return DATA_INFO.copy()


def _pcp_normalized_work(
    df: pd.DataFrame,
    dims_override: list[str] | None,
    max_dims: int = 8,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Recreate the normalized (0..1) values used by go.Parcoords so that
    constraintrange comparisons match what the user brushed.

    IMPORTANT: dims must match the PCP dims order used in build_pcp_figure().
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["Country"]), []

    # ✅ Use the same dim selection logic as the PCP plot
    if isinstance(dims_override, list) and len(dims_override) >= 2:
        dims = [str(d) for d in dims_override if d in df.columns][:max_dims]
    else:
        dims = pick_pcp_dims(df, ui_category=None, max_dims=max_dims)

    if len(dims) < 2:
        return pd.DataFrame(columns=["Country"]), []

    work = df[["Country"] + dims].copy()

    # normalize each dim to 0..1 (same as PCP plot)
    for c in dims:
        work[c] = coerce_numeric(work[c])
        med = work[c].median(skipna=True)
        work[c] = work[c].fillna(med)

        mn, mx = float(work[c].min()), float(work[c].max())
        if np.isfinite(mn) and np.isfinite(mx) and mx > mn:
            work[c] = (work[c] - mn) / (mx - mn)
        else:
            work[c] = 0.0

    return work, dims


def _brush_countries_from_store(brush_store) -> list[str]:
    if brush_store is None:
        return []
    if isinstance(brush_store, dict):
        vals = brush_store.get("countries", [])
        if isinstance(vals, list):
            return [str(x) for x in vals if x]
        return []
    if isinstance(brush_store, list):
        return [str(x) for x in brush_store if x]
    return []


def _normalize_prev_constraints(prev_store, dims: list[str]) -> dict[str, list[list[float]]]:
    """
    Support BOTH:
      - new format: {"gdp_per_capita_usd": [[lo,hi], ...], ...}
      - old format: {"2": [[lo,hi], ...], ...} (dimension indices)
    Convert everything to: { "<dim_name>": [[lo,hi], ...] }
    """
    out: dict[str, list[list[float]]] = {}
    if not isinstance(prev_store, dict):
        return out

    raw = prev_store.get("constraints")
    if not isinstance(raw, dict):
        return out

    for k, v in raw.items():
        if not isinstance(v, list):
            continue

        key = str(k)

        # old format: numeric index -> map to dim name
        if key.isdigit():
            try:
                idx = int(key)
            except Exception:
                continue
            if 0 <= idx < len(dims):
                out[dims[idx]] = v
            continue

        # new format: already dim name
        out[key] = v

    return out


# ---------------------------------------------------------------------
# PCP figure (visual)
# NOTE: do NOT listen to vis-pcp.restyleData here (avoid redraw loops)
# ---------------------------------------------------------------------
@callback(
    Output("vis-pcp", "figure"),
    Output("vis-population-text", "children"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
    Input("vis-geo-scale", "value"),
    Input("vis-geo-scope-dd", "value"),
    Input("vis-attr-pool", "value"),
    Input("vis-clear-all", "n_clicks"),  # bump uirevision to visually clear brush
    Input("vis-pcp-selected-only", "value"),
    prevent_initial_call=False,
)
def update_pcp(
    selection_store,
    brush_store,
    geo_scale,
    geo_scope,
    dims_override,
    clear_clicks,
    selected_only_toggle,
):
    df = _safe_df()
    if df.empty:
        return no_update, ""

    show_selected_only = "on" in (selected_only_toggle or [])

    selection_store = normalize_selection_store(selection_store)
    brush_countries = _brush_countries_from_store(brush_store)

    # keep persistence normally, but clearing filter must reset persisted brush constraints
    uirev = f"pcp:{int(clear_clicks or 0)}"

    fig = build_pcp_figure(
        df=df,
        ui_category=None,
        geo_scale=geo_scale or "global",
        in_mask=None,
        selection_store=selection_store,
        max_dims=8,
        brush_countries=brush_countries,
        uirevision=uirev,
        dims_override=dims_override,
        show_selected_only=show_selected_only,
    )

    pop_text = f"Population: {geo_scale or 'global'}"
    if (geo_scale or "").lower() in ("continent", "region") and geo_scope:
        pop_text += f" ({geo_scope})"

    return fig, pop_text


# ---------------------------------------------------------------------
# PCP brush + Clear button -> pcp-brush-store (SINGLE OWNER)
# Store schema:
#   {"countries": [...], "constraints": { "<dim_name>": [[lo,hi], ...], ... } }
# ---------------------------------------------------------------------
@callback(
    Output("pcp-brush-store", "data"),
    Input("vis-pcp", "restyleData"),
    Input("vis-clear-all", "n_clicks"),
    State("vis-attr-pool", "value"),
    State("pcp-brush-store", "data"),
    prevent_initial_call=True,
)
def pcp_store_from_brush_or_clear(restyle_data, clear_clicks, dims_override, prev_store):
    # Clear button wins
    if ctx.triggered_id == "vis-clear-all":
        return None

    # Brush update
    df = _safe_df()
    work_norm, dims = _pcp_normalized_work(df, dims_override, max_dims=8)
    if work_norm.empty or len(dims) < 2:
        return None

    # ✅ Normalize previous constraints to dim-name keyed (supports legacy index-keyed stores)
    prev_constraints = _normalize_prev_constraints(prev_store, dims=dims)

    patch, saw_constraint_key = parse_parcoords_constraintrange_patch(restyle_data)

    # not a constraint update -> ignore
    if not saw_constraint_key:
        return no_update

    # -----------------------------------------------------------------
    # ✅ Convert patch indices -> DIMENSION NAMES (so axis reordering is safe)
    # -----------------------------------------------------------------
    constraints = dict(prev_constraints)

    for dim_idx_str, ranges in patch.items():
        # parse index
        try:
            dim_idx = int(str(dim_idx_str))
        except Exception:
            continue

        if not (0 <= dim_idx < len(dims)):
            continue

        dim_name = dims[dim_idx]

        # cleared constraint for that dimension
        if not ranges:
            constraints.pop(dim_name, None)
        else:
            constraints[dim_name] = ranges

    # no constraints -> clear filter
    if not constraints:
        return None

    countries = countries_from_parcoords_constraints(
        work_norm,
        dims=dims,
        constraints=constraints,  # now keyed by dim name
    )

    return {"countries": countries, "constraints": constraints}
