# jbi100_app/callbacks/distribution_callbacks.py
from __future__ import annotations

from dash import Input, Output, State, callback
import pandas as pd

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.geo_utils import geo_mask
from jbi100_app.plots.common import metric_cols_for_category, all_numeric_metrics, pretty_metric
from jbi100_app.plots.histogram import build_histogram_figure
from jbi100_app.plots.violin import build_violin_figure
from jbi100_app.state.selection_store import normalize_selection_store, names_from_store


def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    return DATA_INFO.copy()


@callback(
    Output("vis-hist-attr", "options"),
    Output("vis-hist-attr", "value"),
    Output("vis-violin-attr", "options"),
    Output("vis-violin-attr", "value"),
    Input("vis-category", "value"),
    State("vis-hist-attr", "value"),
    State("vis-violin-attr", "value"),
)
def refresh_single_attr_options(ui_category, cur_hist, cur_violin):
    df = _safe_df()
    cols = metric_cols_for_category(df, ui_category)
    if not cols:
        cols = all_numeric_metrics(df)

    opts = [{"label": pretty_metric(c), "value": c} for c in cols]
    if not cols:
        return [], None, [], None

    if cur_hist not in cols:
        cur_hist = cols[0]
    if cur_violin not in cols:
        cur_violin = cols[0]

    return opts, cur_hist, opts, cur_violin


@callback(
    Output("vis-filter-plot", "figure"),
    Output("vis-filter-text", "children"),
    Input("vis-hist-attr", "value"),
    Input("vis-hist-bins", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
)
def update_histogram(metric, bins, geo_scale, selection_store, brush_data):
    df = _safe_df()

    selection_store = normalize_selection_store(selection_store)
    selected_names = names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    brush = []
    if isinstance(brush_data, dict) and brush_data.get("countries"):
        brush = [str(x) for x in brush_data.get("countries", []) if x]

    in_mask = geo_mask(df, geo_scale or "global", focus) if not df.empty else None

    fig = build_histogram_figure(
        df=df,
        metric=metric,
        nbins=int(bins or 30),
        geo_scale=geo_scale or "global",
        in_mask=in_mask,
        selection_store=selection_store,
        brush_countries=brush,
    )

    scope_active = (geo_scale or "global") in ("continent", "region") and focus
    return fig, ("Continent/region active" if scope_active else "Global")


@callback(
    Output("vis-violin-plot", "figure"),
    Input("vis-violin-attr", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
)
def update_violin(metric, geo_scale, selection_store):
    df = _safe_df()

    selection_store = normalize_selection_store(selection_store)
    selected_names = names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    in_mask = geo_mask(df, geo_scale or "global", focus) if not df.empty else None

    return build_violin_figure(
        df=df,
        metric=metric,
        geo_scale=geo_scale or "global",
        in_mask=in_mask,
        selection_store=selection_store,
    )
