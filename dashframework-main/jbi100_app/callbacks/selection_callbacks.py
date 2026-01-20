from __future__ import annotations

import numpy as np
import pandas as pd
from dash import Input, Output, State, callback, html, no_update

from jbi100_app.data.data_loader import DATA_INFO, ALL_COUNTRIES
from jbi100_app.data.geo_utils import (
    UN_COUNTRIES,
    normalise_country_key,
    normalise_country_display,
)
from jbi100_app.state.selection_store import (
    merge_selection_store,
    names_from_store,
    normalise_selection_store,
)


# =============================================================================
# Limits
# =============================================================================

MAX_COUNTRIES = 6
MAX_ATTRS = 8


# =============================================================================
# Helpers
# =============================================================================

def _safe_df() -> pd.DataFrame:
    """
    Return a defensive copy of DATA_INFO with guaranteed geography columns,
    filtered to UN-recognised countries.
    """
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])

    df = DATA_INFO.copy()

    for col in ("Country", "Region", "Continent"):
        if col not in df.columns:
            df[col] = "Unknown"

    df["Country"] = df["Country"].astype(str)

    df["_UN_NAME"] = (
        df["Country"]
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )

    return df[df["_UN_NAME"].isin(UN_COUNTRIES)].copy()


def _to_country_from_click(click_data: dict | None) -> str | None:
    """
    Extract a country name from Plotly clickData payloads.
    """
    if not click_data or not isinstance(click_data, dict):
        return None

    points = click_data.get("points", [])
    if not points:
        return None

    point = points[0]

    custom = point.get("customdata")
    if isinstance(custom, (list, tuple)) and custom and custom[0]:
        return str(custom[0])

    if point.get("hovertext"):
        return str(point["hovertext"])

    if point.get("text"):
        return str(point["text"])

    return None


def _country_option_label(name: str, colour: str | None):
    """
    Build a dropdown label with a coloured dot for the country selector.
    """
    dot = html.Span(
        style={
            "width": "10px",
            "height": "10px",
            "borderRadius": "50%",
            "background": colour or "rgba(148,163,184,0.9)",
            "display": "inline-block",
            "flex": "0 0 auto",
        }
    )

    return html.Span(
        [
            dot,
            html.Span(
                name.upper(),
                style={
                    "fontWeight": 800,
                    "letterSpacing": "0.02em",
                },
            ),
        ],
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "gap": "6px",
        },
    )


# =============================================================================
# Country dropdown + selection store (colour-stable, capped at 6)
# =============================================================================

@callback(
    Output("vis-country", "value"),
    Output("vis-country", "options"),
    Output("vis-warnings", "children"),
    Output("vis-selection-store", "data"),
    Output("vis-country-limit-dialog", "message"),
    Output("vis-country-limit-dialog", "displayed"),
    Input("vis-country", "value"),
    State("vis-selection-store", "data"),
    prevent_initial_call=False,
)
def init_or_update_country_dropdown(vis_country_value, cur_sel_store):
    """
    Initialise or update the country dropdown and synchronise it with
    the colour-preserving selection store.
    """
    df = _safe_df()

    countries_all = (
        ALL_COUNTRIES
        if ALL_COUNTRIES
        else (
            sorted(df["Country"].dropna().astype(str).unique().tolist())
            if "Country" in df.columns
            else []
        )
    )

    cur_sel_store = normalise_selection_store(cur_sel_store)

    raw = (
        vis_country_value
        if isinstance(vis_country_value, list)
        else [vis_country_value] if vis_country_value else []
    )
    raw = [str(x) for x in raw if x]

    # Keep only recognised countries
    raw = [c for c in raw if c in countries_all]

    show_popup = False
    popup_msg = ""

    if len(raw) > MAX_COUNTRIES:
        raw = raw[:MAX_COUNTRIES]
        show_popup = True
        popup_msg = f"You can select at most {MAX_COUNTRIES} countries."

    merged, ok = merge_selection_store(cur_sel_store, raw)
    if not ok:
        merged = cur_sel_store

    colour_map = {
        d["country_name"]: d["colour_rgb"]
        for d in merged
    }

    options = [
        {
            "value": str(c),
            "label": _country_option_label(str(c), colour_map.get(str(c))),
        }
        for c in countries_all
    ]

    warning = ""
    if df.empty:
        warning = (
            "Dataset is empty after UN filtering. "
            "Check mun_dataset.csv loading and country names."
        )

    return (
        names_from_store(merged),
        options,
        warning,
        merged,
        popup_msg,
        show_popup,
    )


@callback(
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-selection-store", "data", allow_duplicate=True),
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Input("vis-clear-all", "n_clicks"),
    prevent_initial_call=True,
)
def clear_filter_only(n_clicks):
    """
    Clear temporary filters (e.g. PCP brush) without touching selection state.
    """
    if not n_clicks:
        return no_update, no_update, no_update

    return no_update, no_update, None


@callback(
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-selection-store", "data", allow_duplicate=True),
    Input("vis-map", "clickData"),
    State("vis-selection-store", "data"),
    prevent_initial_call=True,
)
def map_click_to_selection(click_data, current_sel_store):
    """
    Toggle country selection via map clicks.
    """
    current_sel_store = normalise_selection_store(current_sel_store)
    selected_names = names_from_store(current_sel_store)

    country = _to_country_from_click(click_data)
    if not country:
        return no_update, no_update

    # Toggle off
    if country in selected_names:
        new_names = [c for c in selected_names if c != country]
        merged, ok = merge_selection_store(current_sel_store, new_names)
        return (
            (names_from_store(merged), merged)
            if ok
            else (selected_names, current_sel_store)
        )

    # Toggle on (prepend)
    new_names = [country] + selected_names
    if len(new_names) > MAX_COUNTRIES:
        new_names = new_names[:MAX_COUNTRIES]

    merged, ok = merge_selection_store(current_sel_store, new_names)
    return (
        (names_from_store(merged), merged)
        if ok
        else (no_update, no_update)
    )


# =============================================================================
# Attribute selection cap at 8
# =============================================================================

@callback(
    Output("vis-selected-attributes", "value"),
    Output("vis-attr-limit-dialog", "message"),
    Output("vis-attr-limit-dialog", "displayed"),
    Input("vis-selected-attributes", "value"),
    prevent_initial_call=True,
)
def cap_attr_pool_to_8(selected):
    """
    Enforce a maximum of eight selected attributes.
    """
    if not isinstance(selected, list):
        return no_update, no_update, no_update

    selected = [str(x) for x in selected if x]

    if len(selected) <= MAX_ATTRS:
        return no_update, "", False

    capped = selected[:MAX_ATTRS]
    msg = f"You can select at most {MAX_ATTRS} attributes."
    return capped, msg, True


@callback(
    Output("vis-selected-attributes", "data"),
    Input("vis-selected-attributes", "value"),
)
def update_selected_attributes(attr_pool_value):
    """
    Authoritative attribute selection handler.
    Always returns a list[str].
    """
    if not attr_pool_value:
        return []

    if isinstance(attr_pool_value, list):
        return attr_pool_value

    return [attr_pool_value]
