from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback, State

from jbi100_app.data.data_loader import DATA_INFO, CONTINENTS, REGIONS, normalize_country_key
from jbi100_app.plots.map import build_map_figure
from jbi100_app.data.geo_utils import geo_mask
from jbi100_app.plots.common import _pretty_attr_label


# ============================================================
# Geo-scope dropdown logic
# ============================================================
@callback(
    Output("vis-geo-scope-container", "style"),
    Output("vis-geo-scope-dd", "options"),
    Output("vis-geo-scope-dd", "value"),
    Input("vis-geo-scale", "value"),
)
def update_geo_scope_dropdown(geo_scale):
    if geo_scale == "continent":
        opts = sorted(CONTINENTS.keys())
        return (
            {"display": "block"},
            [{"label": c.title(), "value": c} for c in opts],
            opts[0] if opts else None,
        )

    if geo_scale == "region":
        opts = sorted(REGIONS.keys())
        return (
            {"display": "block"},
            [{"label": r.title(), "value": r} for r in opts],
            opts[0] if opts else None,
        )

    return {"display": "none"}, [], None


def _raw_countries_from_brush_store(brush_data) -> list[str]:
    """
    Accepts:
      - None
      - {"countries": [...], "constraints": {...}}
      - {"countries": [...]}  (scatter)
      - ["Netherlands", ...]  (older)
    Returns raw strings (un-normalized).
    """
    if brush_data is None:
        return []

    if isinstance(brush_data, dict):
        vals = brush_data.get("countries", [])
        if isinstance(vals, list):
            return [str(x) for x in vals if x]
        return []

    if isinstance(brush_data, list):
        return [str(x) for x in brush_data if x]

    return []


def _brush_countries_for_df(brush_data, df: pd.DataFrame) -> list[str]:
    """
    Convert brush store -> list of df['Country'] display names.
    Uses _CountryKey matching so case/spacing differences don't break filtering.
    """
    raw = _raw_countries_from_brush_store(brush_data)
    keys = {normalize_country_key(x) for x in raw}
    keys.discard("")

    if not keys or df is None or df.empty or "_CountryKey" not in df.columns:
        return []

    return df.loc[df["_CountryKey"].isin(keys), "Country"].astype(str).tolist()


# ============================================================
# Map update
# ============================================================
@callback(
    Output("vis-map", "figure"),
    Input("vis-metric", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-geo-scope-dd", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
)
def update_map(metric, geo_scale, geo_scope, selection_store, brush_data):
    if DATA_INFO is None or DATA_INFO.empty or metric is None:
        return build_map_figure(
            pd.DataFrame(),
            metric,
            geo_scale,
            pd.Series(dtype=bool),
            selection_store or [],
            [],
        )

    plot_df = DATA_INFO.copy()

    # Ensure Plotly location column exists
    if "_PLOTLY_NAME" not in plot_df.columns:
        plot_df["_PLOTLY_NAME"] = plot_df["Country"]

    # Base geo mask (existing behaviour; requires focus_country arg)
    base_mask = geo_mask(plot_df, geo_scale or "global", None)

    # Scope mask (controls continent/region focus)
    scope_mask = pd.Series(True, index=plot_df.index)

    if (geo_scale or "").lower() == "continent" and geo_scope in CONTINENTS:
        allowed = set(CONTINENTS[geo_scope])
        scope_mask = plot_df["_CountryKey"].isin(allowed)

    elif (geo_scale or "").lower() == "region" and geo_scope in REGIONS:
        allowed = set(REGIONS[geo_scope])
        scope_mask = plot_df["_CountryKey"].isin(allowed)

    in_mask = base_mask & scope_mask

    brush_countries = _brush_countries_for_df(brush_data, plot_df)

    return build_map_figure(
        plot_df,
        metric,
        geo_scale,
        in_mask,
        selection_store or [],
        brush_countries,
    )

# @callback(
#     Output("vis-metric", "options"),
#     Output("vis-metric", "value"),
#     Input("vis-selected-attributes", "data"),
#     State("vis-metric", "value"),
# )
# def refresh_map_metric_from_selected_attrs(selected_attrs, current_metric):
#     if not isinstance(selected_attrs, list) or not selected_attrs:
#         # No attributes selected → disable map metric
#         return [], None
#
#     attrs = [str(a) for a in selected_attrs if a]
#
#     options = [
#         {"label": _pretty_attr_label(a), "value": a}
#         for a in attrs
#     ]
#
#     # Preserve current selection if still valid
#     if current_metric not in attrs:
#         current_metric = attrs[0]
#
#     return options, current_metric
