from __future__ import annotations

import pandas as pd
import numpy as np
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


# ============================================================
# Map update (scope greys out, does NOT filter)
# ============================================================
@callback(
    Output("vis-map", "figure"),
    Input("vis-metric", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-geo-scope-dd", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
)
def update_map(
    metric,
    geo_scale,
    geo_scope,
    selection_store,
    brush_countries,
):
    if DATA_INFO is None or DATA_INFO.empty or metric is None:
        return build_map_figure(
            pd.DataFrame(),
            metric,
            geo_scale,
            pd.Series(dtype=bool),
            selection_store,
            brush_countries,
        )

    plot_df = DATA_INFO.copy()

    # ------------------------------------------------------------
    # Base geo mask (existing behaviour)
    # ------------------------------------------------------------
    base_mask = geo_mask(plot_df, geo_scale, None)

    # ------------------------------------------------------------
    # Scope mask (continent / region)
    # ------------------------------------------------------------
    scope_mask = pd.Series(True, index=plot_df.index)

    if geo_scale == "continent" and geo_scope in CONTINENTS:
        allowed = set(CONTINENTS[geo_scope])
        scope_mask = plot_df["_CountryKey"].isin(allowed)

    elif geo_scale == "region" and geo_scope in REGIONS:
        allowed = set(REGIONS[geo_scope])
        scope_mask = plot_df["_CountryKey"].isin(allowed)

    # ------------------------------------------------------------
    # Combine masks: country is "in" only if BOTH are true
    # ------------------------------------------------------------
    in_mask = base_mask & scope_mask

    # Ensure Plotly column exists
    if "_PLOTLY_NAME" not in plot_df.columns:
        plot_df["_PLOTLY_NAME"] = plot_df["Country"]

    return build_map_figure(
        plot_df,
        metric,
        geo_scale,
        in_mask,
        selection_store,
        brush_countries,
    )
