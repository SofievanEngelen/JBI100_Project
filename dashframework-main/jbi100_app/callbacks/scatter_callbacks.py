# jbi100_app/callbacks/scatter_callbacks.py
from __future__ import annotations

from dash import Input, Output, State, callback
import pandas as pd

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.geo_utils import geo_mask
from jbi100_app.plots.common import metric_cols_for_category, all_numeric_metrics, pretty_metric
from jbi100_app.plots.scatter import build_scatter_figure
from jbi100_app.state.selection_store import normalize_selection_store, names_from_store


def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    return DATA_INFO.copy()


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


@callback(
    Output("vis-scatter-plot", "figure"),
    Input("vis-scatter-x", "value"),
    Input("vis-scatter-y", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
)
def update_scatter(x_metric, y_metric, geo_scale, selection_store):
    df = _safe_df()

    selection_store = normalize_selection_store(selection_store)
    selected_names = names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    in_mask = geo_mask(df, geo_scale or "global", focus) if not df.empty else None

    return build_scatter_figure(
        df=df,
        x_metric=x_metric,
        y_metric=y_metric,
        in_mask=in_mask,
        selection_store=selection_store,
    )
