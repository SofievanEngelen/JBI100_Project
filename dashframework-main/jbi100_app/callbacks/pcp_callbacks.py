from __future__ import annotations

import numpy as np
import pandas as pd
from dash import Input, Output, State, callback, no_update, ctx

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.geo_utils import geo_mask, CONTINENTS, REGIONS
from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims
from jbi100_app.plots.pcp import build_pcp_figure
from jbi100_app.state.filters import (
    parse_parcoords_constraintrange_patch,
    countries_from_parcoords_constraints,
)
from jbi100_app.state.selection_store import normalise_selection_store
from jbi100_app.data.attributes import attribute_display_label


MAX_PCP_DIMS = 8


# =============================================================================
# Helpers
# =============================================================================

def _safe_df() -> pd.DataFrame:
    """
    Return a safe copy of the global dataset.
    """
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country"])
    return DATA_INFO.copy()


def _choose_dims(
    df: pd.DataFrame,
    dims_override: list[str] | None,
    max_dims: int = MAX_PCP_DIMS,
) -> list[str]:
    """
    Choose PCP dimensions, preferring explicit user selection when valid.
    """
    if isinstance(dims_override, list) and len(dims_override) >= 2:
        return [str(d) for d in dims_override if d in df.columns][:max_dims]

    return pick_pcp_dims(df, max_dims=max_dims)


def _pcp_normalised_work(df: pd.DataFrame, dims: list[str]) -> pd.DataFrame:
    """
    Produce a 0–1 normalised working dataframe for PCP filtering.
    """
    if df is None or df.empty or len(dims) < 2:
        return pd.DataFrame(columns=["Country"])

    work = df[["Country"] + dims].copy()

    for col in dims:
        work[col] = coerce_numeric(work[col])
        median = work[col].median(skipna=True)
        work[col] = work[col].fillna(median)

        mn, mx = float(work[col].min()), float(work[col].max())
        if np.isfinite(mn) and np.isfinite(mx) and mx > mn:
            work[col] = (work[col] - mn) / (mx - mn)
        else:
            work[col] = 0.0

    return work


def _brush_countries_from_store(brush_store) -> list[str]:
    """
    Extract country names from the PCP brush store.
    """
    if brush_store is None:
        return []

    if isinstance(brush_store, dict):
        values = brush_store.get("countries", [])
        if isinstance(values, list):
            return [str(x) for x in values if x]
        return []

    if isinstance(brush_store, list):
        return [str(x) for x in brush_store if x]

    return []


def _normalise_prev_constraints(
    prev_store,
    dims: list[str],
) -> dict[str, list[list[float]]]:
    """
    Normalise previously stored PCP constraints.

    Supports both index-based (legacy) and name-based keys.
    """
    out: dict[str, list[list[float]]] = {}

    if not isinstance(prev_store, dict):
        return out

    raw = prev_store.get("constraints")
    if not isinstance(raw, dict):
        return out

    for key, value in raw.items():
        if not isinstance(value, list):
            continue

        key_str = str(key)

        if key_str.isdigit():
            idx = int(key_str)
            if 0 <= idx < len(dims):
                out[dims[idx]] = value
        else:
            out[key_str] = value

    return out


def _scope_mask(
    df: pd.DataFrame,
    geo_scale: str,
    geo_scope,
) -> pd.Series:
    """
    Compute continent / region scope mask, matching map behaviour.
    """
    if df is None or df.empty:
        return pd.Series(dtype=bool)

    geo_scale = (geo_scale or "global").lower().strip()

    base_mask = geo_mask(df, geo_scale, None)
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


# =============================================================================
# Callbacks
# =============================================================================

@callback(
    Output("vis-pcp", "figure"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
    Input("vis-geo-scale", "value"),
    Input("vis-geo-scope-dd", "value"),
    Input("pcp-dims-store", "data"),
    Input("vis-clear-all", "n_clicks"),
    Input("vis-pcp-selected-only", "value"),
    Input("vis-pcp-color-first-axis", "value"),
    State("vis-pcp", "figure"),
    Input("theme-store", "data"),
    prevent_initial_call=False,
)
def update_pcp(
    selection_store,
    brush_store,
    geo_scale,
    geo_scope,
    dims_store,
    clear_clicks,
    selected_only_toggle,
    colour_first_axis_toggle,
    current_pcp_fig,
    theme,
):
    """
    Update the Parallel Coordinates Plot in response to UI changes.
    """
    df = _safe_df()
    if df.empty:
        return no_update

    selection_store = normalise_selection_store(selection_store)
    brush_countries = _brush_countries_from_store(brush_store)

    show_selected_only = "on" in (selected_only_toggle or [])
    colour_by_first_axis = "on" in (colour_first_axis_toggle or [])

    if isinstance(dims_store, list) and len(dims_store) >= 2:
        dims_to_use = [d for d in dims_store if d in df.columns][:MAX_PCP_DIMS]
    else:
        dims_to_use = pick_pcp_dims(df, max_dims=MAX_PCP_DIMS)

    in_mask = _scope_mask(df, geo_scale, geo_scope)
    uirevision = f"pcp:{int(clear_clicks or 0)}"

    return build_pcp_figure(
        df=df,
        ui_category=None,
        geo_scale=geo_scale or "global",
        in_mask=in_mask,
        selection_store=selection_store,
        max_dims=MAX_PCP_DIMS,
        brush_countries=brush_countries,
        uirevision=uirevision,
        dims_override=dims_to_use,
        show_selected_only=show_selected_only,
        colour_by_first_axis=colour_by_first_axis,
        theme=theme,
    )


@callback(
    Output("pcp-brush-store", "data"),
    Input("vis-pcp", "restyleData"),
    Input("vis-clear-all", "n_clicks"),
    State("vis-selected-attributes", "value"),
    State("pcp-dims-store", "data"),
    State("pcp-brush-store", "data"),
    prevent_initial_call=True,
)
def pcp_store_from_brush_or_clear(
    restyle_data,
    clear_clicks,
    dims_override,
    dims_store,
    prev_store,
):
    """
    Update PCP brush store from brushing or clear action.
    """
    if ctx.triggered_id == "vis-clear-all":
        return None

    df = _safe_df()
    if df.empty:
        return None

    dims: list[str] = []

    if isinstance(dims_store, list):
        dims = [str(x) for x in dims_store if x in df.columns][:MAX_PCP_DIMS]

    if len(dims) < 2:
        dims = _choose_dims(df, dims_override)

    if len(dims) < 2:
        return None

    work_norm = _pcp_normalised_work(df, dims)
    if work_norm.empty:
        return None

    prev_constraints = _normalise_prev_constraints(prev_store, dims)

    patch, saw_constraint_key = parse_parcoords_constraintrange_patch(restyle_data)
    if not saw_constraint_key:
        return no_update

    constraints = dict(prev_constraints)

    for dim_idx_str, ranges in patch.items():
        dim_idx = int(dim_idx_str)
        if 0 <= dim_idx < len(dims):
            dim_name = dims[dim_idx]
            if ranges:
                constraints[dim_name] = ranges
            else:
                constraints.pop(dim_name, None)

    if not constraints:
        return None

    countries = countries_from_parcoords_constraints(
        work_norm,
        dims=dims,
        constraints=constraints,
    )

    return {
        "countries": countries,
        "constraints": constraints,
    }


@callback(
    Output("pcp-dims-store", "data"),
    Output("pcp-attr-dd", "value"),
    Output("pcp-max-dims-dialog", "displayed"),
    Input("pcp-attr-dd", "value"),
)
def update_pcp_dims_from_dropdown(attrs):
    """
    Update PCP dimensions from the dropdown, enforcing the dimension cap.
    """
    if not attrs:
        return None, [], False

    if len(attrs) > MAX_PCP_DIMS:
        capped = attrs[:MAX_PCP_DIMS]
        return capped, capped, True

    return attrs, attrs, False
