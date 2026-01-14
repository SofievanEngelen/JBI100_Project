# jbi100_app/callbacks/onboarding_callbacks.py
from __future__ import annotations

from dash import Input, Output, State, callback, no_update, html

from jbi100_app.data.category_mapping import UI_CATEGORIES


def _as_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _unique_keep_order(xs):
    out = []
    for v in xs:
        if v is None:
            continue
        v = str(v)
        if v and v not in out:
            out.append(v)
    return out


def _cat_keys(cat_list) -> list[str]:
    if isinstance(cat_list, list):
        return [str(x) for x in cat_list if x is not None]
    if cat_list is None:
        return []
    return [str(cat_list)]


def _cat_attrs_for_key(key: str) -> list[str]:
    v = UI_CATEGORIES.get(key, [])
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v]
    if isinstance(v, dict):
        for k in ["indicators", "metrics", "attributes", "columns"]:
            if k in v and isinstance(v[k], (list, tuple)):
                return [str(x) for x in v[k]]
    return []


def _union_cat_attrs(keys: list[str]) -> list[str]:
    merged = []
    for k in keys:
        merged.extend(_cat_attrs_for_key(k))
    return _unique_keep_order(merged)


@callback(
    Output("session-store", "data"),
    Input("country-dd", "value"),
    Input("cat-radio", "value"),
    Input("all-attrs-dd", "value"),
    State("session-store", "data"),
)
def sync_onboarding_to_session(country, cat_list, all_attrs, prev_data):
    prev_data = prev_data or {}
    keys = _cat_keys(cat_list)

    # keep compatibility: store the first selected category as ui_category
    ui_category = keys[0] if keys else None

    return {
        "country": country if country is not None else prev_data.get("country"),
        "ui_category": ui_category if ui_category is not None else prev_data.get("ui_category"),
        "all_attributes": all_attrs if all_attrs is not None else prev_data.get("all_attributes"),
    }


@callback(
    Output("category-hint", "children"),
    Output("category-attrs-preview", "children"),
    Input("cat-radio", "value"),
)
def update_category_preview(cat_list):
    keys = _cat_keys(cat_list)
    if not keys:
        return "No category selected.", html.Div("Select one or more categories to see their attributes.", style={"fontSize": "12px", "color": "#6b778c"})

    attrs = sorted(_union_cat_attrs(keys), key=lambda s: s.lower())
    if not attrs:
        return "Category selected.", html.Div("No attributes found for the selected categories.", style={"fontSize": "12px", "color": "#6b778c"})

    pills = [
        html.Span(
            a,
            style={
                "display": "inline-block",
                "padding": "6px 10px",
                "borderRadius": "999px",
                "border": "1px solid rgba(15, 23, 42, 0.15)",
                "background": "white",
                "fontSize": "12px",
                "color": "#516074",
                "marginRight": "8px",
                "marginBottom": "8px",
                "whiteSpace": "nowrap",
            },
        )
        for a in attrs
    ]
    return "Category selected.", html.Div(pills, style={"display": "flex", "flexWrap": "wrap"})


@callback(
    Output("all-attrs-dd", "value", allow_duplicate=True),
    Input("cat-add-to-attrs", "n_clicks"),
    State("cat-radio", "value"),
    State("all-attrs-dd", "value"),
    prevent_initial_call=True,
)
def add_category_attributes_to_selected(n, cat_list, current_attrs):
    if not n:
        return no_update

    keys = _cat_keys(cat_list)
    if not keys:
        return no_update

    add = _union_cat_attrs(keys)
    merged = _unique_keep_order(_as_list(current_attrs) + add)
    return merged

from dash import Input, Output, State, callback, no_update

@callback(
    Output("onboarding-modal", "is_open"),
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-attr-pool", "value", allow_duplicate=True),
    Input("onboarding-confirm", "n_clicks"),
    State("onboarding-country", "value"),
    State("onboarding-attr", "value"),
    prevent_initial_call=True,
)
def apply_onboarding_selection(n_clicks, countries, attrs):
    """
    Push onboarding selections directly into the sidebar.
    """

    if not n_clicks:
        return no_update, no_update, no_update

    return (
        False,                 # close modal
        countries or [],       # populate country sidebar
        attrs or [],           # populate attribute sidebar
    )
