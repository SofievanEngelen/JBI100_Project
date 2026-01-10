from __future__ import annotations

from dash import Input, Output, State, callback, no_update
import pandas as pd

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.plots.pcp import build_pcp_figure
from jbi100_app.state.selection_store import normalize_selection_store


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame()
    return DATA_INFO.copy()


# ---------------------------------------------------------------------
# PCP figure update
# ---------------------------------------------------------------------
@callback(
    Output("vis-pcp", "figure"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
    Input("vis-geo-scope-dd", "value"),
    Input("vis-attr-pool", "value"),
    State("vis-country", "data"),
    State("url", "pathname"),
    prevent_initial_call=False,
)
def update_pcp(
    selection_store,
    brush_store,
    geo_scope,
    dims_override,
    country_store,
    pathname,
):
    df = _safe_df()
    if df.empty:
        return no_update

    selection_store = normalize_selection_store(selection_store)

    brush_countries = []
    if isinstance(brush_store, dict):
        brush_countries = brush_store.get("countries", []) or []

    fig = build_pcp_figure(
        df=df,
        ui_category=None,              # ❗ category REMOVED
        geo_scale=geo_scope,
        in_mask=None,                  # handled inside plot if needed
        selection_store=selection_store,
        max_dims=8,
        brush_countries=brush_countries,
        dims_override=dims_override,
        uirevision="pcp",
    )

    return fig
