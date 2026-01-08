# jbi100_app/callbacks/pcp_callbacks.py
from __future__ import annotations

from dash import Input, Output, State, callback
import pandas as pd

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.geo_utils import geo_mask
from jbi100_app.plots.pcp import build_pcp_figure
from jbi100_app.state.filters import extract_parcoords_brush_countries
from jbi100_app.state.selection_store import normalize_selection_store, names_from_store


def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    return DATA_INFO.copy()


@callback(
    Output("vis-pcp", "figure"),
    Output("vis-population-text", "children"),
    Output("pcp-brush-store", "data"),
    Input("vis-category", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
    Input("vis-pcp", "selectedData"),
    State("pcp-brush-store", "data"),
)
def update_pcp(ui_category, geo_scale, selection_store, selected_data, prev_brush):
    df = _safe_df()

    selection_store = normalize_selection_store(selection_store)
    selected_names = names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    in_mask = geo_mask(df, geo_scale or "global", focus) if not df.empty else None

    fig = build_pcp_figure(
        df=df,
        ui_category=ui_category,
        geo_scale=geo_scale or "global",
        in_mask=in_mask,
        selection_store=selection_store,
        max_dims=8,
    )

    pop_text = (
        "Population: global"
        if (geo_scale or "global") == "global"
        else f"Population: {geo_scale} (focus={focus or 'none'})"
    )

    brush_out = prev_brush if prev_brush is not None else None
    brushed = extract_parcoords_brush_countries(selected_data, df[["Country"]].join(df.drop(columns=["Country"], errors="ignore")))
    if brushed:
        brush_out = {"countries": brushed}

    return fig, pop_text, brush_out


@callback(
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Input("vis-clear-brush", "n_clicks"),
    prevent_initial_call=True,
)
def clear_brush(n):
    if n and n > 0:
        return None
    return no_update
