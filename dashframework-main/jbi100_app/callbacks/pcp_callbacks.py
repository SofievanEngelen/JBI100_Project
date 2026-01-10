# jbi100_app/callbacks/pcp_callbacks.py
from __future__ import annotations

from dash import Input, Output, State, callback, no_update
import pandas as pd
import numpy as np

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.geo_utils import geo_mask
from jbi100_app.plots.pcp import build_pcp_figure
from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims
from jbi100_app.state.filters import (
    parse_parcoords_constraintrange_patch,
    countries_from_parcoords_constraints,
)
from jbi100_app.state.selection_store import normalize_selection_store, names_from_store


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    return DATA_INFO.copy()


def _pcp_normalized_work(df: pd.DataFrame, ui_category: str | None, max_dims: int = 8) -> tuple[pd.DataFrame, list[str]]:
    """
    Recreate the normalized (0..1) values used by go.Parcoords so that
    constraintrange comparisons match what the user brushed.
    Returns (work_df, dims_in_order).
    """
    dims = pick_pcp_dims(df, ui_category, max_dims=max_dims)
    if df is None or df.empty or len(dims) < 2:
        return pd.DataFrame(columns=["Country"]), []

    work = df[["Country"] + dims].copy()
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


# ---------------------------------------------------------------------
# PCP figure callback (VISUAL ONLY)
# (Do NOT listen to restyleData here, so brushing doesn't trigger redraw loops.)
# ---------------------------------------------------------------------
@callback(
    Output("vis-pcp", "figure"),
    Output("vis-population-text", "children"),
    Input("vis-attr-pool", "value"),   # ✅ instead of vis-category
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),  # ✅ so PCP fades lines when filter exists
)
def update_pcp(attr_pool, geo_scale, selection_store, brush_data):
    df = _safe_df()

    # normalize pool -> list[str], max 8
    dims_override = []
    if isinstance(attr_pool, list):
        dims_override = [str(x) for x in attr_pool if x]
    elif isinstance(attr_pool, str) and attr_pool:
        dims_override = [attr_pool]
    dims_override = dims_override[:8]

    selection_store = normalize_selection_store(selection_store)
    selected_names = names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None
    in_mask = geo_mask(df, geo_scale or "global", focus) if not df.empty else None

    brush = []
    if isinstance(brush_data, dict) and brush_data.get("countries"):
        brush = [str(x) for x in brush_data.get("countries", []) if x]

    fig = build_pcp_figure(
        df=df,
        ui_category=None,                 # ignored when dims_override set
        geo_scale=geo_scale or "global",
        in_mask=in_mask,
        selection_store=selection_store,
        max_dims=8,
        brush_countries=brush,
        dims_override=dims_override or None,
    )

    pop_text = (
        "Population: global"
        if (geo_scale or "global") == "global"
        else f"Population: {geo_scale} (focus={focus or 'none'})"
    )
    return fig, pop_text



# ---------------------------------------------------------------------
# PCP BRUSH (restyleData) → TEMPORARY REGION FILTER STORE (ACCUMULATED)
# Store schema:
#   {"countries": [...], "constraints": { "<dim_idx>": [[lo,hi], [lo2,hi2], ...], ... } }
# ---------------------------------------------------------------------
@callback(
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Input("vis-pcp", "restyleData"),
    State("vis-category", "value"),
    State("pcp-brush-store", "data"),
    prevent_initial_call=True,
)
def pcp_brush_to_store(restyle_data, ui_category, prev_store):
    df = _safe_df()

    # Recreate PCP's normalized dataframe + dims order
    work_norm, dims = _pcp_normalized_work(df, ui_category, max_dims=8)
    if work_norm.empty or len(dims) < 2:
        return None

    # Previous accumulated constraints (if any)
    prev_constraints: dict[str, list[list[float]]] = {}
    if isinstance(prev_store, dict) and isinstance(prev_store.get("constraints"), dict):
        # keys stored as strings for JSON friendliness
        prev_constraints = {
            str(k): v for k, v in prev_store.get("constraints", {}).items()
            if isinstance(k, (str, int))
        }

    # Parse just the patch from this restyleData event
    patch, saw_constraint_key = parse_parcoords_constraintrange_patch(restyle_data)

    # If this restyleData event isn't about constraintrange, don't touch the store
    if not saw_constraint_key:
        return no_update

    # Merge patch into accumulated constraints
    # - If patch for a dim is None/[] => clear that dim constraint
    # - Else set/replace that dim's ranges
    constraints = dict(prev_constraints)
    for dim_idx_str, ranges in patch.items():
        if not ranges:
            constraints.pop(dim_idx_str, None)
        else:
            constraints[dim_idx_str] = ranges

    # If no constraints remain, clear the filter
    if not constraints:
        return None

    # Compute the accumulated brushed countries from ALL active constraints
    countries = countries_from_parcoords_constraints(
        work_norm,
        dims=dims,
        constraints=constraints,
    )

    # If constraints exist but produce no countries, keep the constraints anyway
    # (still reflects the user's brush state), but countries list will be empty.
    return {"countries": countries, "constraints": constraints}


# ---------------------------------------------------------------------
# Clear brush button (shared by PCP + scatter)
# ---------------------------------------------------------------------
@callback(
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Input("vis-clear-brush", "n_clicks"),
    prevent_initial_call=True,
)
def clear_brush(n):
    if n and n > 0:
        return None
    return no_update
