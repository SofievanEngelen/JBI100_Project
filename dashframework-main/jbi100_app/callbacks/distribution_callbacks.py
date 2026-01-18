from __future__ import annotations

from dash import Input, Output, State, callback, no_update
import pandas as pd

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.geo_utils import geo_mask, CONTINENTS, REGIONS
from jbi100_app.plots.histogram import build_histogram_figure
from jbi100_app.plots.violin import build_violin_figure
from jbi100_app.state.selection_store import normalize_selection_store, names_from_store
from jbi100_app.state.filters import apply_temp_region_filter
from jbi100_app.data.attributes import all_numeric_attributes, attribute_display_label


def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    return DATA_INFO.copy()


def _scope_mask(df: pd.DataFrame, geo_scale: str, geo_scope) -> pd.Series:
    """
    Match map behaviour:
      - global: all True
      - continent: only selected continent
      - region: only selected region
    """
    if df is None or df.empty:
        return pd.Series(dtype=bool)

    geo_scale = (geo_scale or "global").lower().strip()

    # base mask (kept for compatibility)
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
    Output("vis-hist-attr", "options"),
    Output("vis-hist-attr", "value"),
    Output("vis-violin-attr", "options"),
    Output("vis-violin-attr", "value"),
    Input("vis-geo-scale", "value"),
    State("vis-hist-attr", "value"),
    State("vis-violin-attr", "value"),
)
def refresh_single_attr_options(_geo_scale, cur_hist, cur_violin):
    df = _safe_df()
    cols = all_numeric_attributes(df)

    opts = [{"label": attribute_display_label(c), "value": c} for c in cols]
    if not cols:
        return [], None, [], None

    if cur_hist not in cols:
        cur_hist = cols[0]
    if cur_violin not in cols:
        cur_violin = cols[0]

    return opts, cur_hist, opts, cur_violin


@callback(
    Output("vis-filter-plot", "figure"),
    # Output("vis-filter-text", "children"),
    Input("vis-hist-attr", "value"),
    Input("vis-hist-bins", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-geo-scope-dd", "value"),  # ✅ NEW
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
    Input("theme-store", "data"),
)
def update_histogram(metric, bins, geo_scale, geo_scope, selection_store, brush_data, theme):
    """
    IMPORTANT: The histogram should NOT be filtered by the global brush,
    otherwise clicking a bin makes the histogram "zoom" (bins/range recompute).
    Instead we keep the full distribution and overlay the brush as a highlight.
    """
    df = _safe_df()

    selection_store = normalize_selection_store(selection_store)

    brush = []
    if isinstance(brush_data, dict) and brush_data.get("countries"):
        brush = [str(x) for x in brush_data.get("countries", []) if x]

    in_mask = _scope_mask(df, geo_scale or "global", geo_scope) if not df.empty else None

    fig = build_histogram_figure(
        df=df,
        metric=metric,
        nbins=int(bins or 30),
        geo_scale=geo_scale or "global",
        in_mask=in_mask,
        selection_store=selection_store,
        brush_countries=brush,  # overlay highlight, don't filter df
        theme=theme,
    )

    return fig


@callback(
    Output("vis-violin-plot", "figure"),
    Input("vis-violin-attr", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-geo-scope-dd", "value"),  # ✅ NEW (so violin scope matches)
    Input("vis-selection-store", "data"),
    Input("theme-store", "data"),
)
def update_violin(metric, geo_scale, geo_scope, selection_store, theme):
    df = _safe_df()

    selection_store = normalize_selection_store(selection_store)
    in_mask = _scope_mask(df, geo_scale or "global", geo_scope) if not df.empty else None

    return build_violin_figure(
        df=df,
        metric=metric,
        geo_scale=geo_scale or "global",
        in_mask=in_mask,
        selection_store=selection_store,
        theme=theme,
    )

# ---------------------------------------------------------------------
# Histogram bin click -> global filter (pcp-brush-store)
# ---------------------------------------------------------------------
@callback(
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Input("vis-filter-plot", "clickData"),
    prevent_initial_call=True,
)
def hist_bin_to_brush(clickData):
    if not isinstance(clickData, dict):
        return no_update
    pts = clickData.get("points", [])
    if not pts:
        return no_update

    cd = pts[0].get("customdata")
    if not isinstance(cd, dict):
        return no_update

    countries = cd.get("countries", [])
    if not isinstance(countries, list) or not countries:
        return no_update

    return {"countries": [str(x) for x in countries if x]}
