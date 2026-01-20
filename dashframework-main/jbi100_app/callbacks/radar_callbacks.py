# jbi100_app/callbacks/radar_callbacks.py
from __future__ import annotations

import pandas as pd
from dash import Input, Output, State, callback

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.plots.radar import build_radar_figure
from jbi100_app.state.selection_store import normalise_selection_store


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


# =============================================================================
# Radar plot rendering
# =============================================================================

@callback(
    Output("vis-radar-plot", "figure"),
    Input("vis-selection-store", "data"),
    Input("vis-radar-attr", "value"),
    Input("theme-store", "data"),
)
def update_radar(
    selection_store,
    radar_attr,
    theme: str,
):
    """
    Update the radar plot based on selected countries and attributes.
    """
    df = _safe_df()
    selection_store = normalise_selection_store(selection_store)

    dims_override: list[str] = []

    if isinstance(radar_attr, list):
        dims_override = [str(x) for x in radar_attr if x][:8]
    elif isinstance(radar_attr, str) and radar_attr:
        dims_override = [radar_attr]

    return build_radar_figure(
        df=df,
        ui_category=None,
        selection_store=selection_store,
        dims_override=dims_override or None,
        theme=theme,
    )


# =============================================================================
# Radar attribute state + limits
# =============================================================================

MAX_RADAR_DIMS = 8


@callback(
    Output("radar-attr-store", "data"),
    Input("vis-radar-attr", "value"),
)
def store_radar_attrs(vals):
    """
    Persist the current radar attribute selection.
    """
    return vals or []


@callback(
    Output("vis-radar-attr", "value"),
    Output("radar-max-dims-dialog", "displayed"),
    Input("vis-radar-attr", "value"),
    State("vis-radar-attr", "value"),
    prevent_initial_call=True,
)
def limit_radar_attributes(new_vals, prev_vals):
    """
    Enforce a maximum number of radar attributes and show a warning dialog
    when the limit is exceeded.
    """
    if not new_vals:
        return new_vals, False

    if len(new_vals) > MAX_RADAR_DIMS:
        # Revert to previous selection and display warning
        return prev_vals[:MAX_RADAR_DIMS], True

    return new_vals, False
