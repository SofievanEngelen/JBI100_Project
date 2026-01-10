from __future__ import annotations

import pandas as pd
from dash import Input, Output, callback

from jbi100_app.data.data_loader import DATA_INFO, CONTINENTS, REGIONS
from jbi100_app.plots.map import build_map_figure
from jbi100_app.data.geo_utils import geo_mask


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


def _brush_countries_from_store(brush_data) -> list[str]:
    """
    pcp-brush-store can be:
      - None
      - {"countries": [...]}  (your scatter/pcp callbacks)
      - a raw list[str]       (some older code)
    Normalize to list[str].
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


# ============================================================
# Map update
# - scope dropdown controls "continent/region focus" (via in_mask)
# - brush store controls FILTER (white-out outside filter) in map.py
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

    # Scope mask (controls continent/region visibility WITHOUT removing others)
    scope_mask = pd.Series(True, index=plot_df.index)

    if (geo_scale or "").lower() == "continent" and geo_scope in CONTINENTS:
        allowed = set(CONTINENTS[geo_scope])
        scope_mask = plot_df["_CountryKey"].isin(allowed)

    elif (geo_scale or "").lower() == "region" and geo_scope in REGIONS:
        allowed = set(REGIONS[geo_scope])
        scope_mask = plot_df["_CountryKey"].isin(allowed)

    in_mask = base_mask & scope_mask

    # ✅ This is the FILTER list used by map.py to white-out outside filter
    brush_countries = _brush_countries_from_store(brush_data)

    return build_map_figure(
        plot_df,
        metric,
        geo_scale,
        in_mask,
        selection_store or [],
        brush_countries,
    )
