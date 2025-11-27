import json
import dash
from dash import html, dcc, Input, Output, State, ALL, callback_context

from jbi100_app.main import app
from jbi100_app.views.map_view import map_view_layout
from jbi100_app.views.data_view import (
    data_view_layout,
    make_tag,
    make_geo_tag,
)
from jbi100_app.data import CONTINENTS, REGIONS, COUNTRIES


# MAIN LAYOUT (page container + bottom navigation)
app.layout = html.Div(
    id="app-container",
    children=[
        html.Div(
            id="page-content",
            children=[
                html.Div(
                    id="map-view-wrapper",
                    style={"display": "none"},
                    children=map_view_layout()
                ),
                html.Div(
                    id="data-view-wrapper",
                    style={"display": "none"},
                    children=data_view_layout()
                ),
            ],
        ),

        # Current page store (default = data view)
        dcc.Store(id="current-page", data="data"),

        # Bottom-left navigation button
        html.Button(
            id="bottom-nav-button",
            children="Go to Map View",
            className="bottom-nav-btn"
        ),
    ],
)


# PAGE TOGGLE (bottom-left navigation)
@app.callback(
    Output("current-page", "data"),
    Input("bottom-nav-button", "n_clicks"),
    State("current-page", "data"),
    prevent_initial_call=True
)
def toggle_page(clicks: int, current: str) -> str:
    """
    Toggle between map and data views.

    :param clicks: Number of button clicks.
    :param current: Currently active page.
    :return: "map" or "data" depending on the toggle direction.
    """
    return "data" if current == "map" else "map"


@app.callback(
    Output("bottom-nav-button", "children"),
    Input("current-page", "data")
)
def update_bottom_button_text(page: str) -> str:
    """
    Update the navigation button text based on which page is active.

    :param page: The currently selected page.
    :return: Button label text.
    """
    return "Go to Data View" if page == "map" else "Go to Map View"


# PAGE RENDERING (show/hide map or data view)
@app.callback(
    Output("map-view-wrapper", "style"),
    Output("data-view-wrapper", "style"),
    Input("current-page", "data")
)
def show_page(page: str) -> tuple[dict, dict]:
    """
    Display the selected page (map or data).

    :param page: The currently active page.
    :return: A tuple of style dictionaries controlling visibility.
    """
    if page == "map":
        return {"display": "block"}, {"display": "none"}
    return {"display": "none"}, {"display": "block"}


# ATTRIBUTE TAG RENDERING
@app.callback(
    Output("attr-tags", "children"),
    Input("attribute-tags-store", "data")
)
def render_sidebar_attributes(tags: list[dict]) -> list[html.Div]:
    """
    Render attribute tags in the left sidebar.

    :param tags: List of attribute tag dicts.
    :return: A list of tag components.
    """
    return [make_tag(t["label"], t["id"]) for t in tags]


@app.callback(
    Output("content-attribute-tags", "children"),
    Input("attribute-tags-store", "data")
)
def render_content_attributes(tags: list[dict]) -> list[html.Div]:
    """
    Render attribute tags inside the main content panel.

    :param tags: List of attribute tag dicts.
    :return: A list of tag components.
    """
    return [make_tag(t["label"], t["id"]) for t in tags]


# ATTRIBUTE TAG LOGIC (add/delete)
@app.callback(
    Output("attribute-tags-store", "data"),
    Input({"type": "delete-tag", "index": ALL}, "n_clicks"),
    Input("popup-add", "n_clicks"),
    State("add-attribute-dropdown", "value"),
    State("attribute-tags-store", "data"),
    prevent_initial_call=True
)
def update_attribute_tags(delete_clicks: list[int],
                          add_clicks: int,
                          new_values: list[str],
                          existing: list[dict]) -> list[dict]:
    """
    Manage attribute tags (add new ones or delete existing ones).

    :param delete_clicks: Pattern-matching delete events.
    :param add_clicks: Clicks on the popup Add button.
    :param new_values: New attribute selections from dropdown.
    :param existing: Current list of attribute tag dicts.
    :return: Updated tag list.
    """
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # Delete tag
    if trigger.startswith("{"):
        obj = json.loads(trigger)
        delete_id = obj["index"]
        return [t for t in existing if t["id"] != delete_id]

    # Add new attributes
    if trigger == "popup-add" and new_values:
        updated = existing.copy()
        for val in new_values:
            if not any(t["id"] == val for t in updated):
                updated.append({"label": val, "id": val})
        return updated

    return existing


# POPUP MENU BEHAVIOR
@app.callback(
    Output("popup-backdrop", "style"),
    Input("add-attribute", "n_clicks"),
    Input("popup-cancel", "n_clicks"),
    Input("popup-add", "n_clicks"),
    State("popup-backdrop", "style"),
    prevent_initial_call=True
)
def toggle_popup(open_click: int,
                 cancel_click: int,
                 add_click: int,
                 style: dict) -> dict:
    """
    Open or close the popup overlay for adding attributes.

    :param open_click: Clicks on open popup button.
    :param cancel_click: Clicks on cancel button.
    :param add_click: Clicks on add button.
    :param style: Current CSS style of the popup.
    :return: Updated style dictionary.
    """
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered_id

    # Open
    if trigger == "add-attribute":
        return {**style, "display": "flex"}

    # Close on cancel or add
    return {**style, "display": "none"}


# GEO SCALE CONTROLS (radio, dropdown, display)
@app.callback(
    Output("scale-select-title", "children"),
    Input("geo-scale", "value")
)
def update_scale_title(scale: str) -> str:
    """
    Update the dropdown title based on selected geographical scale.

    :param scale: One of global/continent/region/country.
    :return: A formatted title string.
    """
    return f"Select {scale.capitalize()}"


@app.callback(
    Output("current-scale-display", "children"),
    Input("geo-scale", "value")
)
def display_current_scale(scale: str) -> str:
    """
    Display a text summary of the current selected geo scale.

    :param scale: Geo scale selection.
    :return: Summary string.
    """
    return f"Current geographical scale: {scale.capitalize()}"


@app.callback(
    Output("select-scale-block", "style"),
    Input("geo-scale", "value")
)
def toggle_scale_block(scale: str) -> dict:
    """
    Show/hide the geo item dropdown when 'global' is selected.

    :param scale: Geo scale.
    :return: Style dict controlling visibility.
    """
    return {"display": "none"} if scale == "global" else {"display": "block"}


@app.callback(
    Output("scale-select-dropdown", "options"),
    Input("geo-scale", "value")
)
def populate_scale_dropdown(scale: str) -> list[dict]:
    """
    Populate the dropdown with items matching the selected geo scale.

    :param scale: One of continent/region/country.
    :return: A list of dropdown option dicts.
    """
    if scale == "continent":
        return [{"label": c, "value": c} for c in CONTINENTS]
    if scale == "region":
        return [{"label": r, "value": r} for r in REGIONS]
    if scale == "country":
        return [{"label": c, "value": c} for c in COUNTRIES]
    return []


# GEO TAG LOGIC (add/delete tags)
@app.callback(
    Output("scale-tags-store", "data"),
    Input("scale-select-dropdown", "value"),
    Input({"type": "delete-geo-tag", "index": ALL}, "n_clicks"),
    State("scale-tags-store", "data"),
    prevent_initial_call=True
)
def modify_geo_tags(drop_values: list[str],
                    delete_clicks: list[int],
                    existing: list[dict]) -> list[dict]:
    """
    Manage geographical selection tags based on dropdown and delete clicks.

    :param drop_values: Selected dropdown values.
    :param delete_clicks: Delete button clicks for geo tags.
    :param existing: Current list of geo tag dicts.
    :return: Updated geo tag list.
    """
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered_id

    # Dropdown selection
    if trigger == "scale-select-dropdown":
        if not drop_values:
            return []
        return [{"label": v, "id": v} for v in drop_values]

    # Delete tag
    if isinstance(trigger, dict):
        remove_id = trigger["index"]
        return [t for t in existing if t["id"] != remove_id]

    return existing


@app.callback(
    Output("selected-tags", "children"),
    Input("scale-tags-store", "data")
)
def render_geo_tags(tags: list[dict]) -> list[html.Div]:
    """
    Render selected geographical scale tags.

    :param tags: List of geo tag dictionaries.
    :return: List of tag components.
    """
    return [make_geo_tag(t["label"], t["id"]) for t in tags]



if __name__ == "__main__":
    app.run(debug=True)
