from __future__ import annotations

import numpy as np
import pandas as pd
from dash import Input, Output, State, callback, no_update, ctx

from jbi100_app.data.data_loader import DATA_INFO, CONTINENTS, REGIONS
from jbi100_app.data.geo_utils import geo_mask
from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims, pretty_metric
from jbi100_app.plots.pcp import build_pcp_figure
from jbi100_app.state.filters import (
    parse_parcoords_constraintrange_patch,
    countries_from_parcoords_constraints,
)
from jbi100_app.state.selection_store import normalize_selection_store


def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country"])
    return DATA_INFO.copy()


def _choose_dims(df: pd.DataFrame, dims_override: list[str] | None, max_dims: int = 8) -> list[str]:
    if isinstance(dims_override, list) and len(dims_override) >= 2:
        return [str(d) for d in dims_override if d in df.columns][:max_dims]
    return pick_pcp_dims(df, ui_category=None, max_dims=max_dims)


def _pcp_normalized_work(df: pd.DataFrame, dims: list[str]) -> pd.DataFrame:
    if df is None or df.empty or len(dims) < 2:
        return pd.DataFrame(columns=["Country"])

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

    return work


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

        if key.isdigit():
            try:
                idx = int(key)
            except Exception:
                continue
            if 0 <= idx < len(dims):
                out[dims[idx]] = v
            continue

        out[key] = v

    return out


def _dims_from_current_figure(fig_obj, candidates: list[str]) -> list[str] | None:
    if not isinstance(fig_obj, dict):
        return None

    data = fig_obj.get("data")
    if not isinstance(data, list) or not data:
        return None

    trace0 = data[0]
    if not isinstance(trace0, dict):
        return None

    dims_payload = trace0.get("dimensions")
    if not isinstance(dims_payload, list) or len(dims_payload) < 2:
        return None

    label_to_metric = {pretty_metric(m): m for m in candidates if isinstance(m, str) and m}

    new_order: list[str] = []
    for d in dims_payload:
        if not isinstance(d, dict):
            continue
        lab = d.get("label")
        if not isinstance(lab, str):
            continue
        m = label_to_metric.get(lab)
        if m and m not in new_order:
            new_order.append(m)

    if len(new_order) >= 2:
        return new_order

    return None


def _scope_mask(df: pd.DataFrame, geo_scale: str, geo_scope) -> pd.Series:
    """
    Match map behaviour for continent/region.
    """
    if df is None or df.empty:
        return pd.Series(dtype=bool)

    geo_scale = (geo_scale or "global").lower().strip()

    base_mask = geo_mask(df, geo_scale or "global", None)
    scope_mask = pd.Series(True, index=df.index)

    if geo_scale == "continent" and geo_scope in CONTINENTS:
        allowed = set(CONTINENTS[geo_scope])
        if "_CountryKey" in df.columns:
            scope_mask = df["_CountryKey"].isin(allowed)

    elif geo_scale == "region" and geo_scope in REGIONS:
        allowed = set(REGIONS[geo_scope])
        if "_CountryKey" in df.columns:
            scope_mask = df["_CountryKey"].isin(allowed)

    return base_mask & scope_mask


@callback(
    Output("vis-pcp", "figure"),
    Output("vis-population-text", "children"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
    Input("vis-geo-scale", "value"),
    Input("vis-geo-scope-dd", "value"),   # ✅ NEW
    Input("vis-attr-pool", "value"),
    Input("pcp-dims-store", "data"),
    Input("vis-clear-all", "n_clicks"),
    Input("vis-pcp-selected-only", "value"),
    Input("vis-pcp-color-first-axis", "value"),
    State("vis-pcp", "figure"),
    prevent_initial_call=False,
)
def update_pcp(
    selection_store,
    brush_store,
    geo_scale,
    geo_scope,
    dims_override,
    dims_store,
    clear_clicks,
    selected_only_toggle,
    color_first_axis_toggle,
    current_pcp_fig,
):
    df = _safe_df()
    if df.empty:
        return no_update, ""

    selection_store = normalize_selection_store(selection_store)
    brush_countries = _brush_countries_from_store(brush_store)

    show_selected_only = "on" in (selected_only_toggle or [])
    color_by_first_axis = "on" in (color_first_axis_toggle or [])

    # 1) Build base dims from sidebar (this is the source of truth for "which attrs exist")
    base_dims = _choose_dims(df, dims_override, max_dims=8)

    # helper: preserve order of `preferred` but only for items in `base`,
    # then append any new items from `base` not already present.
    def _merge_order(preferred: list[str], base: list[str], max_dims: int = 8) -> list[str]:
        base_set = set(base)
        out = [d for d in preferred if d in base_set]
        out_set = set(out)
        out.extend([d for d in base if d not in out_set])
        return out[:max_dims]  # ✅ cap to 8

    dims_to_use: list[str] = []

    # 2) If we have a stored order, merge it with base (keeps drag order but allows new attrs)
    if isinstance(dims_store, list) and base_dims:
        preferred = [str(x) for x in dims_store if x and str(x) in df.columns]
        dims_to_use = _merge_order(preferred, base_dims, max_dims=8)

    # 3) If no store, we *may* extract from current figure — BUT:
    #    if the trigger is vis-attr-pool, ALWAYS use base_dims (so it can grow beyond 2)
    if len(dims_to_use) < 2:
        if ctx.triggered_id == "vis-attr-pool":
            dims_to_use = base_dims
        else:
            extracted = _dims_from_current_figure(current_pcp_fig, candidates=base_dims)
            if extracted and len(extracted) >= 2:
                dims_to_use = _merge_order(extracted, base_dims, max_dims=8)

    # 4) Final fallback
    if len(dims_to_use) < 2:
        dims_to_use = base_dims

    # ✅ continent/region in-scope mask
    in_mask = _scope_mask(df, geo_scale or "global", geo_scope)

    uirev = f"pcp:{int(clear_clicks or 0)}"

    fig = build_pcp_figure(
        df=df,
        ui_category=None,
        geo_scale=geo_scale or "global",
        in_mask=in_mask,                 # ✅ NEW (now used)
        selection_store=selection_store,
        max_dims=8,
        brush_countries=brush_countries,
        uirevision=uirev,
        dims_override=dims_to_use,
        show_selected_only=show_selected_only,
        color_by_first_axis=color_by_first_axis,
    )

    pop_text = f"Population: {geo_scale or 'global'}"
    if (geo_scale or "").lower() in ("continent", "region") and geo_scope:
        pop_text += f" ({geo_scope})"

    return fig, pop_text


@callback(
    Output("pcp-brush-store", "data"),
    Input("vis-pcp", "restyleData"),
    Input("vis-clear-all", "n_clicks"),
    State("vis-attr-pool", "value"),
    State("pcp-dims-store", "data"),
    State("pcp-brush-store", "data"),
    prevent_initial_call=True,
)
def pcp_store_from_brush_or_clear(restyle_data, clear_clicks, dims_override, dims_store, prev_store):
    if ctx.triggered_id == "vis-clear-all":
        return None

    df = _safe_df()
    if df.empty:
        return None

    dims = []
    if isinstance(dims_store, list):
        dims = [str(x) for x in dims_store if x and str(x) in df.columns][:8]
    if len(dims) < 2:
        dims = _choose_dims(df, dims_override, max_dims=8)
    if len(dims) < 2:
        return None

    work_norm = _pcp_normalized_work(df, dims=dims)
    if work_norm.empty:
        return None

    prev_constraints = _normalize_prev_constraints(prev_store, dims=dims)

    patch, saw_constraint_key = parse_parcoords_constraintrange_patch(restyle_data)
    if not saw_constraint_key:
        return no_update

    constraints = dict(prev_constraints)

    for dim_idx_str, ranges in patch.items():
        try:
            dim_idx = int(str(dim_idx_str))
        except Exception:
            continue

        if not (0 <= dim_idx < len(dims)):
            continue

        dim_name = dims[dim_idx]

        if not ranges:
            constraints.pop(dim_name, None)
        else:
            constraints[dim_name] = ranges

    if not constraints:
        return None

    countries = countries_from_parcoords_constraints(
        work_norm,
        dims=dims,
        constraints=constraints,
    )

    return {"countries": countries, "constraints": constraints}
