# jbi100_app/callbacks/onboarding_callbacks.py
from __future__ import annotations

from dash import Input, Output, State, callback


@callback(
    Output("session-store", "data"),
    Input("country-dd", "value"),
    Input("cat-radio", "value"),  # list from Checklist
    State("session-store", "data"),
)
def sync_onboarding_to_session(country, cat_list, prev_data):
    """
    Persist landing selections into session-store.

    Final report version:
      - Store only what is used by the visualisation (goal removed)
      - Keep stable dict shape
      - Enforce single-select semantics for category checklist
      - Do not overwrite existing non-empty values with None
    """
    prev_data = prev_data or {}

    ui_category = None
    if isinstance(cat_list, list) and len(cat_list) > 0:
        ui_category = cat_list[0]

    out = {
        "country": country if country is not None else prev_data.get("country"),
        "ui_category": ui_category if ui_category is not None else prev_data.get("ui_category"),
    }
    return out


@callback(
    Output("category-hint", "children"),
    Input("cat-radio", "value"),
)
def update_category_hint(cat_list):
    if not cat_list:
        return "No category selected. Visualisation will show all indicators by default."
    return "Category selected. Visualisation will prioritize indicators from this category."
