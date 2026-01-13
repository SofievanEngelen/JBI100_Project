from __future__ import annotations

import numpy as np
from dash import Input, Output, State, callback, html, no_update

from jbi100_app.data.data_loader import DATA_INFO, ALL_COUNTRIES, UN_COUNTRIES
from jbi100_app.state.selection_store import (
    merge_selection_store,
    names_from_store,
    normalize_selection_store,
)

# ============================================================
# Limits
# ============================================================
MAX_COUNTRIES = 6
MAX_ATTRS = 8


def _safe_df():
    import pandas as pd

    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    df = DATA_INFO.copy()
    for c in ("Country", "Region", "Continent"):
        if c not in df.columns:
            df[c] = "Unknown"
    df["Country"] = df["Country"].astype(str)
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


# ============================================================
# Country dropdown + selection store (keeps colours) + popup cap at 6
# ============================================================
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
    df = _safe_df()

    countries_all = (
        ALL_COUNTRIES
        if (ALL_COUNTRIES is not None and len(ALL_COUNTRIES) > 0)
        else (sorted(df["Country"].dropna().astype(str).unique().tolist()) if "Country" in df.columns else [])
    )

    cur_sel_store = normalize_selection_store(cur_sel_store)

    raw = vis_country_value if isinstance(vis_country_value, list) else ([vis_country_value] if vis_country_value else [])
    raw = [str(x) for x in raw if x]

    # keep only known countries
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

    # colour-aware dropdown labels
    color_map = {d["country_name"]: d["colour_rgb"] for d in merged}
    opts = [{"value": str(c), "label": _country_option_label(str(c), color_map.get(str(c)))} for c in countries_all]

    warn = ""
    if df.empty:
        warn = "Dataset is empty after UN filter. Check mun_dataset.csv loading and Country names."

    return names_from_store(merged), opts, warn, merged, popup_msg, show_popup


# ✅ Clear button: clears ONLY the PCP filter (brush), keeps selected countries
@callback(
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-selection-store", "data", allow_duplicate=True),
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Input("vis-clear-all", "n_clicks"),
    prevent_initial_call=True,
)
def clear_filter_only(n):
    if not n:
        return no_update, no_update, no_update
    return no_update, no_update, None


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

    # toggle-off
    if country in selected_names:
        new_names = [c for c in selected_names if c != country]
        merged, ok = merge_selection_store(current_sel_store, new_names)
        return (names_from_store(merged), merged) if ok else (selected_names, current_sel_store)

    # toggle-on (add to front)
    new_names = [country] + selected_names
    if len(new_names) > MAX_COUNTRIES:
        new_names = new_names[:MAX_COUNTRIES]
        # (popup handled only by dropdown callback; map-click stays silent)

    merged, ok = merge_selection_store(current_sel_store, new_names)
    return (names_from_store(merged), merged) if ok else (no_update, no_update)


# ============================================================
# Attribute selection cap at 8 + popup
# ============================================================
@callback(
    Output("vis-attr-pool", "value"),
    Output("vis-attr-limit-dialog", "message"),
    Output("vis-attr-limit-dialog", "displayed"),
    Input("vis-attr-pool", "value"),
    prevent_initial_call=True,
)
def cap_attr_pool_to_8(selected):
    if not isinstance(selected, list):
        return no_update, no_update, no_update

    selected = [str(x) for x in selected if x]

    if len(selected) <= MAX_ATTRS:
        return no_update, "", False

    capped = selected[:MAX_ATTRS]
    msg = f"You can select at most {MAX_ATTRS} attributes."
    return capped, msg, True
