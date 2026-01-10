# jbi100_app/callbacks/selection_callbacks.py
from __future__ import annotations

import numpy as np
from dash import Input, Output, State, callback, html, no_update

from jbi100_app.data.data_loader import DATA_INFO, ALL_COUNTRIES, UN_COUNTRIES
from jbi100_app.state.selection_store import (
    merge_selection_store,
    names_from_store,
    normalize_selection_store,
    clamp_selection,
)


def _safe_df():
    import pandas as pd

    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    df = DATA_INFO.copy()
    for c in ("Country", "Region", "Continent"):
        if c not in df.columns:
            df[c] = "Unknown"
    df["Country"] = df["Country"].astype(str)
    # your existing UN filter behavior
    df["_UN_NAME"] = df["Country"].astype(str).str.strip().str.upper().str.replace(r"\s+", " ", regex=True)
    df = df[df["_UN_NAME"].isin(UN_COUNTRIES)].copy()
    return df


def _to_country_from_click(click_data) -> str | None:
    if not click_data or not isinstance(click_data, dict):
        return None
    pts = click_data.get("points", [])
    if not pts:
        return None
    cd = pts[0].get("customdata")
    if isinstance(cd, (list, tuple)) and len(cd) >= 1 and cd[0]:
        return str(cd[0])
    ht = pts[0].get("hovertext")
    if ht:
        return str(ht)
    txt = pts[0].get("text")
    if txt:
        return str(txt)
    return None


def _country_option_label(name: str, color: str | None):
    dot = html.Span(
        style={
            "width": "10px",
            "height": "10px",
            "borderRadius": "50%",
            "background": color or "rgba(148,163,184,0.9)",
            "display": "inline-block",
            "flex": "0 0 auto",
        }
    )
    return html.Span(
        [dot, html.Span(str(name).upper(), style={"fontWeight": 800, "letterSpacing": "0.02em"})],
        style={"display": "inline-flex", "alignItems": "center", "gap": "6px"},
    )


@callback(
    Output("vis-country", "value"),
    Output("vis-country", "options"),
    Output("vis-warnings", "children"),
    Output("vis-selection-store", "data"),
    Input("vis-country", "value"),
    State("vis-selection-store", "data"),
    prevent_initial_call=False,
)
def init_or_update_country_dropdown(vis_country_value, cur_sel_store):
    df = _safe_df()

    countries_all = (
        ALL_COUNTRIES
        if (ALL_COUNTRIES is not None and len(ALL_COUNTRIES) > 0)
        else (sorted(df["Country"].dropna().astype(str).unique().tolist()) if "Country" in df.columns else [])
    )

    cur_sel_store = normalize_selection_store(cur_sel_store)

    new_names = clamp_selection(vis_country_value if isinstance(vis_country_value, list) else ([vis_country_value] if vis_country_value else []))
    merged, ok = merge_selection_store(cur_sel_store, new_names)
    if not ok:
        merged = cur_sel_store

    color_map = {d["country_name"]: d["colour_rgb"] for d in merged}
    opts = [{"value": str(c), "label": _country_option_label(str(c), color_map.get(str(c)))} for c in countries_all]

    warn = ""
    if df.empty:
        warn = "Dataset is empty after UN filter. Check mun_dataset.csv loading and Country names."

    return names_from_store(merged), opts, warn, merged


@callback(
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-selection-store", "data", allow_duplicate=True),
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Input("vis-clear-all", "n_clicks"),
    prevent_initial_call=True,
)
def clear_all(n):
    if n and n > 0:
        return no_update, no_update, None   # ✅ keep selection, clear filter only
    return no_update, no_update, no_update

from dash import no_update

@callback(
    Output("vis-attr-pool", "value", allow_duplicate=True),
    Input("vis-attr-pool", "value"),
    prevent_initial_call=True,
)
def clamp_attr_pool(v):
    if v is None:
        return []
    if not isinstance(v, list):
        v = [v]
    v = [str(x) for x in v if x]
    if len(v) <= 8:
        return no_update
    return v[:8]



@callback(
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-selection-store", "data", allow_duplicate=True),
    Input("vis-map", "clickData"),
    State("vis-selection-store", "data"),
    prevent_initial_call=True,
)
def map_click_to_selection(clickData, current_sel_store):
    current_sel_store = normalize_selection_store(current_sel_store)
    selected_names = names_from_store(current_sel_store)

    country = _to_country_from_click(clickData)
    if not country:
        return no_update, no_update

    if country in selected_names:
        new_names = [c for c in selected_names if c != country]
        merged, ok = merge_selection_store(current_sel_store, new_names)
        return (names_from_store(merged), merged) if ok else (selected_names, current_sel_store)

    new_names = [country] + selected_names
    merged, ok = merge_selection_store(current_sel_store, new_names)
    return (names_from_store(merged), merged) if ok else (no_update, no_update)
