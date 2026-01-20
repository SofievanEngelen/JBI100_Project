# jbi100_app/callbacks/onboarding_callbacks.py
from __future__ import annotations

from typing import Any
from dash import Input, Output, State, callback, no_update, html


# =============================================================================
# Helpers
# =============================================================================

def _as_list(value: Any) -> list[Any]:
    """
    Coerce a value into a list while preserving None as empty.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _unique_keep_order(values: list[Any]) -> list[str]:
    """
    Remove duplicates while preserving insertion order.
    """
    out: list[str] = []
    for v in values:
        if v is None:
            continue
        s = str(v)
        if s and s not in out:
            out.append(s)
    return out


def _cat_keys(cat_list: Any) -> list[str]:
    """
    Normalise selected category values into a list of strings.
    """
    if isinstance(cat_list, list):
        return [str(x) for x in cat_list if x is not None]
    if cat_list is None:
        return []
    return [str(cat_list)]


def _cat_attrs_for_key(key: str) -> list[str]:
    """
    Return the list of attributes associated with a UI category key.
    """
    value = UI_CATEGORIES.get(key, [])

    if isinstance(value, (list, tuple)):
        return [str(x) for x in value]

    if isinstance(value, dict):
        for field in ("indicators", "metrics", "attributes", "columns"):
            if field in value and isinstance(value[field], (list, tuple)):
                return [str(x) for x in value[field]]

    return []


def _union_cat_attrs(keys: list[str]) -> list[str]:
    """
    Merge attributes across multiple categories, preserving order.
    """
    merged: list[str] = []
    for key in keys:
        merged.extend(_cat_attrs_for_key(key))
    return _unique_keep_order(merged)


# =============================================================================
# Onboarding → session synchronisation
# =============================================================================

@callback(
    Output("session-store", "data"),
    Input("country-dd", "value"),
    Input("cat-radio", "value"),
    Input("all-attrs-dd", "value"),
    State("session-store", "data"),
)
def sync_onboarding_to_session(
    country,
    cat_list,
    all_attrs,
    prev_data,
):
    """
    Synchronise onboarding selections into the session store.
    """
    prev_data = prev_data or {}
    keys = _cat_keys(cat_list)

    # Keep backward compatibility: first selected category is ui_category
    ui_category = keys[0] if keys else None

    return {
        "country": country if country is not None else prev_data.get("country"),
        "ui_category": ui_category if ui_category is not None else prev_data.get("ui_category"),
        "all_attributes": all_attrs if all_attrs is not None else prev_data.get("all_attributes"),
    }


# =============================================================================
# Category preview panel
# =============================================================================

@callback(
    Output("category-hint", "children"),
    Output("category-attrs-preview", "children"),
    Input("cat-radio", "value"),
)
def update_category_preview(cat_list):
    """
    Display a preview of attributes belonging to the selected categories.
    """
    keys = _cat_keys(cat_list)

    if not keys:
        return (
            "No category selected.",
            html.Div(
                "Select one or more categories to see their attributes.",
                style={"fontSize": "12px", "color": "#6b778c"},
            ),
        )

    attrs = sorted(_union_cat_attrs(keys), key=lambda s: s.lower())

    if not attrs:
        return (
            "Category selected.",
            html.Div(
                "No attributes found for the selected categories.",
                style={"fontSize": "12px", "color": "#6b778c"},
            ),
        )

    pills = [
        html.Span(
            attr,
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
        for attr in attrs
    ]

    return "Category selected.", html.Div(pills, style={"display": "flex", "flexWrap": "wrap"})


# =============================================================================
# Category → attribute selection helper
# =============================================================================

@callback(
    Output("all-attrs-dd", "value", allow_duplicate=True),
    Input("cat-add-to-attrs", "n_clicks"),
    State("cat-radio", "value"),
    State("all-attrs-dd", "value"),
    prevent_initial_call=True,
)
def add_category_attributes_to_selected(
    n_clicks,
    cat_list,
    current_attrs,
):
    """
    Add all attributes from the selected categories into the attribute dropdown.
    """
    if not n_clicks:
        return no_update

    keys = _cat_keys(cat_list)
    if not keys:
        return no_update

    to_add = _union_cat_attrs(keys)
    merged = _unique_keep_order(_as_list(current_attrs) + to_add)

    return merged


# =============================================================================
# Onboarding confirmation
# =============================================================================

@callback(
    Output("onboarding-modal", "is_open"),
    Output("vis-country", "value", allow_duplicate=True),
    Input("onboarding-confirm", "n_clicks"),
    State("onboarding-country", "value"),
    prevent_initial_call=True,
)
def apply_onboarding_selection(
    n_clicks: int | None,
    countries,
):
    """
    Apply onboarding selections directly to the sidebar and close the modal.
    """
    if not n_clicks:
        return no_update, no_update

    return (
        False,            # close modal
        countries or [],  # populate country selector
    )


@callback(
    Output("onboarding-confirm", "disabled"),
    Input("onboarding-country", "value"),
)
def enable_start_button(country) -> bool:
    """
    Enable the start button only once a country is selected.
    """
    return country is None
