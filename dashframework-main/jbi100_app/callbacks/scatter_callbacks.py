# jbi100_app/callbacks/scatter_callbacks.py
from __future__ import annotations

from dash import Input, Output, State, callback, no_update
import pandas as pd

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.geo_utils import geo_mask
from jbi100_app.plots.common import metric_cols_for_category, all_numeric_metrics, pretty_metric
from jbi100_app.plots.scatter import build_scatter_figure


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    return DATA_INFO.copy()


def extract_scatter_brush_countries(selected_data, df: pd.DataFrame) -> list[str]:
    """
    Convert Plotly scatter selectedData -> list of country names.
    """
    if not isinstance(selected_data, dict):
        return []

    pts = selected_data.get("points", [])
    if not pts:
        return []

    idxs: list[int] = []
    for p in pts:
        i = p.get("pointIndex")
        if isinstance(i, int):
            idxs.append(i)

    if not idxs:
        return []

    idxs = [i for i in idxs if 0 <= i < len(df)]
    return df.iloc[idxs]["Country"].astype(str).tolist()


# ---------------------------------------------------------------------
# Attribute dropdowns
# ---------------------------------------------------------------------
@callback(
    Output("vis-scatter-x", "options"),
    Output("vis-scatter-y", "options"),
    Output("vis-scatter-x", "value"),
    Output("vis-scatter-y", "value"),
    Input("vis-category", "value"),
    State("vis-scatter-x", "value"),
    State("vis-scatter-y", "value"),
)
def refresh_scatter_attr_options(ui_category, cur_x, cur_y):
    df = _safe_df()

    cols = metric_cols_for_category(df, ui_category)
    if len(cols) < 2:
        cols = all_numeric_metrics(df)

    opts = [{"label": pretty_metric(c), "value": c} for c in cols]
    if not cols:
        return [], [], None, None

    if cur_x not in cols:
        cur_x = cols[0]
    if cur_y not in cols or cur_y == cur_x:
        cur_y = cols[1] if len(cols) > 1 else cols[0]

    return opts, opts, cur_x, cur_y


# ---------------------------------------------------------------------
# Scatter plot rendering (visually reflects PCP filter)
# ---------------------------------------------------------------------
@callback(
    Output("vis-scatter-plot", "figure"),
    Input("vis-scatter-x", "value"),
    Input("vis-scatter-y", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
)
def update_scatter(x_metric, y_metric, geo_scale, selection_store, brush_data):
    df = _safe_df()

    focus = None
    if isinstance(selection_store, list) and selection_store:
        focus = selection_store[0].get("country_name")

    in_mask = geo_mask(df, geo_scale or "global", focus) if not df.empty else None

    brush_countries: list[str] = []
    if isinstance(brush_data, dict) and brush_data.get("countries"):
        brush_countries = [str(x) for x in brush_data.get("countries", []) if x]

    return build_scatter_figure(
        df=df,
        x_metric=x_metric,
        y_metric=y_metric,
        in_mask=in_mask,
        selection_store=selection_store or [],
        brush_countries=brush_countries,
    )


# ---------------------------------------------------------------------
# Scatter selection → global brush (temporary region)
# ---------------------------------------------------------------------
@callback(
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Input("vis-scatter-plot", "selectedData"),
    prevent_initial_call=True,
)
def scatter_to_brush(selected_data):
    # ✅ IMPORTANT: when the figure re-renders, selectedData often becomes None.
    # Returning None here would clear the brush immediately.
    if selected_data is None:
        return no_update

    df = _safe_df()
    countries = extract_scatter_brush_countries(selected_data, df)

    # If user made an empty selection (or selection got wiped), don't clear the store.
    if not countries:
        return no_update

    return {"countries": countries}
