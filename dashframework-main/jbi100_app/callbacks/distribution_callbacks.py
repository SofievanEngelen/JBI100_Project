# jbi100_app/callbacks/distribution_callbacks.py
from __future__ import annotations

from dash import Input, Output, State, callback, no_update
import pandas as pd

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.geo_utils import geo_mask
from jbi100_app.plots.common import metric_cols_for_category, all_numeric_metrics, pretty_metric
from jbi100_app.plots.histogram import build_histogram_figure
from jbi100_app.plots.violin import build_violin_figure
from jbi100_app.state.selection_store import normalize_selection_store, names_from_store
from jbi100_app.state.filters import apply_temp_region_filter


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
    """
    IMPORTANT: The histogram should NOT be filtered by the global brush,
    otherwise clicking a bin makes the histogram "zoom" (bins/range recompute).
    Instead we keep the full distribution and overlay the brush as a highlight.
    """
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
        brush_countries=brush,  # ✅ overlay highlight, don't filter df
    )

    scope_active = (geo_scale or "global") in ("continent", "region") and focus
    filter_txt = f"Filter: {len(brush)} countries" if brush else "Filter: none"
    return fig, (("Continent/region active | " if scope_active else "") + filter_txt)


@callback(
    Output("vis-violin-plot", "figure"),
    Input("vis-violin-attr", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
)
def update_violin(metric, geo_scale, selection_store, brush_data):
    """
    Violin SHOULD reflect the global brush filter (unlike histogram base distribution).
    """
    df = _safe_df()

    selection_store = normalize_selection_store(selection_store)
    selected_names = names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    brush = []
    if isinstance(brush_data, dict) and brush_data.get("countries"):
        brush = [str(x) for x in brush_data.get("countries", []) if x]

    # ✅ Apply global filter here
    df = apply_temp_region_filter(df, brush)

    in_mask = geo_mask(df, geo_scale or "global", focus) if not df.empty else None

    return build_violin_figure(
        df=df,
        metric=metric,
        geo_scale=geo_scale or "global",
        in_mask=in_mask,
        selection_store=selection_store,
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
