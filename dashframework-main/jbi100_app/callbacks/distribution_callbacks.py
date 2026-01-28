from __future__ import annotations

import pandas as pd
from dash import Input, Output, State, callback, no_update

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.geo_utils import geo_mask, CONTINENTS, REGIONS
from jbi100_app.plots.histogram import build_histogram_figure
from jbi100_app.plots.violin import build_violin_figure
from jbi100_app.state.selection_store import normalise_selection_store
from jbi100_app.data.attributes import (
    all_numeric_attributes,
    attribute_display_label,
)


# =============================================================================
# Helpers
# =============================================================================

def _safe_df() -> pd.DataFrame:
    """
    Return a safe copy of the global dataset.
    """
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    return DATA_INFO.copy()


def _scope_mask(
    df: pd.DataFrame,
    geo_scale: str,
    geo_scope,
) -> pd.Series:
    """
    Compute the geographic scope mask, matching map behaviour:

      - global: all countries
      - continent: selected continent only
      - region: selected region only
    """
    if df is None or df.empty:
        return pd.Series(dtype=bool)

    geo_scale = (geo_scale or "global").lower().strip()

    # Base mask (retained for compatibility)
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


# =============================================================================
# Attribute dropdowns (single-attribute plots)
# =============================================================================

@callback(
    Output("vis-hist-attr", "options"),
    Output("vis-hist-attr", "value"),
    Output("vis-violin-attr", "options"),
    Output("vis-violin-attr", "value"),
    Input("vis-geo-scale", "value"),
    State("vis-hist-attr", "value"),
    State("vis-violin-attr", "value"),
)
def refresh_single_attr_options(
    _geo_scale,
    current_hist,
    current_violin,
):
    """
    Refresh histogram and violin attribute dropdowns.

    Both plots always use a single numeric attribute.
    """
    df = _safe_df()
    columns = all_numeric_attributes(df)

    options = [
        {"label": attribute_display_label(c), "value": c}
        for c in columns
    ]

    if not columns:
        return [], None, [], None

    if current_hist not in columns:
        current_hist = columns[0]

    if current_violin not in columns:
        current_violin = columns[0]

    return options, current_hist, options, current_violin


# =============================================================================
# Histogram
# =============================================================================

@callback(
    Output("vis-filter-plot", "figure"),
    Input("vis-hist-attr", "value"),
    Input("vis-hist-bins", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-geo-scope-dd", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
    Input("theme-store", "data"),
)
def update_histogram(
    metric,
    bins,
    geo_scale,
    geo_scope,
    selection_store,
    brush_data,
    theme,
):
    """
    Update the histogram.

    IMPORTANT:
    The histogram must NOT be filtered by the global brush,
    otherwise clicking a bin would recompute bins and ranges.
    Instead, the brush is shown as a visual overlay only.
    """
    df = _safe_df()
    selection_store = normalise_selection_store(selection_store)

    brush_countries: list[str] = []
    if isinstance(brush_data, dict) and brush_data.get("countries"):
        brush_countries = [
            str(x) for x in brush_data["countries"] if x
        ]

    in_mask = (
        _scope_mask(df, geo_scale or "global", geo_scope)
        if not df.empty
        else None
    )

    return build_histogram_figure(
        df=df,
        metric=metric,
        nbins=int(bins or 30),
        geo_scale=geo_scale or "global",
        in_mask=in_mask,
        selection_store=selection_store,
        brush_countries=brush_countries,
        theme=theme,
    )


# =============================================================================
# Violin
# =============================================================================

@callback(
    Output("vis-violin-plot", "figure"),
    Input("vis-violin-attr", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-geo-scope-dd", "value"),
    Input("vis-selection-store", "data"),
    Input("theme-store", "data"),
)
def update_violin(
    metric,
    geo_scale,
    geo_scope,
    selection_store,
    theme,
):
    """
    Update the violin plot.

    The violin respects geographic scope but is not affected by
    temporary brush filters.
    """
    df = _safe_df()
    selection_store = normalise_selection_store(selection_store)

    in_mask = (
        _scope_mask(df, geo_scale or "global", geo_scope)
        if not df.empty
        else None
    )

    return build_violin_figure(
        df=df,
        metric=metric,
        geo_scale=geo_scale or "global",
        geo_scope=geo_scope,
        in_mask=in_mask,
        selection_store=selection_store,
        theme=theme,
    )


# =============================================================================
# Histogram bin click → global brush
# =============================================================================

@callback(
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Input("vis-filter-plot", "clickData"),
    prevent_initial_call=True,
)
def histogram_bin_to_brush(click_data):
    """
    Convert a histogram bin click into a temporary global filter.
    """
    if not isinstance(click_data, dict):
        return no_update

    points = click_data.get("points", [])
    if not points:
        return no_update

    custom = points[0].get("customdata")
    if not isinstance(custom, dict):
        return no_update

    countries = custom.get("countries")
    if not isinstance(countries, list) or not countries:
        return no_update

    return {"countries": [str(c) for c in countries if c]}
