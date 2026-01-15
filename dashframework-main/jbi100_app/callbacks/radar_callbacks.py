# jbi100_app/callbacks/radar_callbacks.py
from __future__ import annotations

from dash import Input, Output, callback
import pandas as pd

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.plots.radar import build_radar_figure
from jbi100_app.state.selection_store import normalize_selection_store


def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    return DATA_INFO.copy()


@callback(
    Output("vis-radar-plot", "figure"),
    Input("vis-selected-attributes", "data"),
    Input("vis-selection-store", "data"),
)
def update_radar(attr_pool, selection_store):
    df = _safe_df()
    selection_store = normalize_selection_store(selection_store)

    dims_override = []
    if isinstance(attr_pool, list):
        dims_override = [str(x) for x in attr_pool if x][:8]
    elif isinstance(attr_pool, str) and attr_pool:
        dims_override = [attr_pool]

    return build_radar_figure(
        df=df,
        ui_category=None,
        selection_store=selection_store,
        dims_override=dims_override or None,
    )
