from __future__ import annotations

import pandas as pd
from dash import Input, Output, State, callback, no_update

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.geo_utils import (
    geo_mask,
    CONTINENTS,
    REGIONS,
    normalise_country_key,
)
from jbi100_app.plots.scatter import build_scatter_figure
from jbi100_app.data.attributes import (
    all_numeric_attributes,
    attribute_display_label,
)


# =============================================================================
# Helpers
# =============================================================================

def _safe_df() -> pd.DataFrame:
    """
    Defensive accessor for the main dataset.
    """
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    return DATA_INFO.copy()


def _raw_countries_from_brush_store(brush_data) -> list[str]:
    """
    Extract raw country identifiers from the global brush store.
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
    Resolve brush-store country identifiers to display names present in df.
    """
    raw = _raw_countries_from_brush_store(brush_data)
    keys = {normalise_country_key(x) for x in raw}
    keys.discard("")

    if not keys or df is None or df.empty or "_CountryKey" not in df.columns:
        return []

    return (
        df.loc[df["_CountryKey"].isin(keys), "Country"]
        .astype(str)
        .tolist()
    )


def extract_scatter_brush_countries(
    selected_data,
    df: pd.DataFrame,
) -> list[str]:
    """
    Convert Plotly scatter selectedData into a list of country names.
    """
    if not isinstance(selected_data, dict):
        return []

    points = selected_data.get("points", [])
    if not points:
        return []

    indices: list[int] = []
    for p in points:
        idx = p.get("pointIndex")
        if isinstance(idx, int):
            indices.append(idx)

    indices = [i for i in indices if 0 <= i < len(df)]
    if not indices:
        return []

    return df.iloc[indices]["Country"].astype(str).tolist()


def _scatter_scope_mask(
    df: pd.DataFrame,
    geo_scale: str,
    geo_scope,
) -> pd.Series:
    """
    Build the in-scope mask for scatter plots, matching map behaviour.
    """
    if df is None or df.empty:
        return pd.Series(dtype=bool)

    geo_scale = (geo_scale or "global").lower().strip()

    # Base mask from geo_utils (kept for consistency)
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
# Scatter attribute dropdowns
# =============================================================================

@callback(
    Output("vis-scatter-x", "options"),
    Output("vis-scatter-y", "options"),
    Output("vis-scatter-x", "value"),
    Output("vis-scatter-y", "value"),
    Input("vis-geo-scale", "value"),
    State("vis-scatter-x", "value"),
    State("vis-scatter-y", "value"),
)
def refresh_scatter_attr_options(_geo_scale, cur_x, cur_y):
    """
    Populate scatter axis dropdowns with all numeric attributes.
    """
    df = _safe_df()
    cols = all_numeric_attributes(df)

    options = [
        {
            "label": attribute_display_label(c, include_category=False),
            "value": c,
        }
        for c in cols
    ]

    if len(cols) < 2:
        return options, options, None, None

    # Preserve existing selections where possible
    if cur_x not in cols:
        cur_x = cols[0]

    if cur_y not in cols or cur_y == cur_x:
        cur_y = cols[1]

    return options, options, cur_x, cur_y


# =============================================================================
# Scatter plot rendering
# =============================================================================

@callback(
    Output("vis-scatter-plot", "figure"),
    Input("vis-scatter-x", "value"),
    Input("vis-scatter-y", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-geo-scope-dd", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
    Input("theme-store", "data"),
)
def update_scatter(
    x_metric,
    y_metric,
    geo_scale,
    geo_scope,
    selection_store,
    brush_data,
    theme,
):
    """
    Render scatter plot reflecting:
      - geographic scope (continent / region)
      - PCP / histogram brush filters
      - explicit country selection
    """
    df = _safe_df()

    in_mask = _scatter_scope_mask(
        df,
        geo_scale or "global",
        geo_scope,
    )

    brush_countries = _brush_countries_for_df(brush_data, df)

    return build_scatter_figure(
        df=df,
        x_metric=x_metric,
        y_metric=y_metric,
        in_mask=in_mask,
        selection_store=selection_store or [],
        brush_countries=brush_countries,
        theme=theme,
    )


# =============================================================================
# Scatter selection → global brush
# =============================================================================

@callback(
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Output("vis-geo-scale", "value", allow_duplicate=True),
    Output("vis-geo-scope-dd", "value", allow_duplicate=True),
    Input("vis-scatter-plot", "selectedData"),
    prevent_initial_call=True,
)
def scatter_to_brush(selected_data):
    """
    Convert scatter lasso/box selection into a temporary global brush.
    Also resets map scope to global.
    """
    # When Plotly clears selection during redraw, selectedData becomes None.
    if selected_data is None:
        return no_update, no_update, no_update

    df = _safe_df()
    countries = extract_scatter_brush_countries(selected_data, df)

    if not countries:
        return no_update, no_update, no_update

    brush_payload = {"countries": countries}

    return brush_payload, "global", None
