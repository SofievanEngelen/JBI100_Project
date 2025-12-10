# jbi100_app/callbacks/data_callbacks.py

import dash
from dash import Input, Output, State, ALL, html, callback_context, no_update

from main import app
from jbi100_app.views.data_view import make_tag, make_geo_tag
from jbi100_app.data_loader import DATA_INFO, CATEGORY_ATTRIBUTES, ALL_COUNTRIES, DATASETS, COUNTRY_TO_CONTINENT, \
    COUNTRY_TO_REGION
from jbi100_app.views.data_tabs.tab_info import render_info_tab
from jbi100_app.views.data_tabs.tab_plots import render_plots_tab
from jbi100_app.views.data_tabs.tab_numbers import render_numbers_tab
from jbi100_app.views.data_tabs.tab_create import render_create_tab


# -------------------------------------------------------------
# 1. RENDER ATTRIBUTE TAGS IN BOX
# -------------------------------------------------------------
@app.callback(
    Output("attr-tags", "children"),
    Input("attribute-tags-store", "data")
)
def render_attribute_tags(tags):
    return [make_tag(t["label"], t["id"]) for t in tags]


# -------------------------------------------------------------
# 2. RENDER GEO TAGS IN BOX
# -------------------------------------------------------------
@app.callback(
    Output("selected-tags", "children"),
    Input("scale-tags-store", "data")
)
def render_geo_tags(tags):
    return [make_geo_tag(t["label"], t["id"]) for t in tags]


# -------------------------------------------------------------
# 3. POPUP OPEN / CLOSE (visual only)
# -------------------------------------------------------------
@app.callback(
    Output("popup-backdrop", "style"),
    Input("add-attribute", "n_clicks"),
    Input("popup-cancel", "n_clicks"),
    Input("popup-add", "n_clicks"),
    State("popup-backdrop", "style"),
    prevent_initial_call=True
)
def toggle_popup(add_click, cancel_click, add_confirm, style):
    ctx = callback_context

    # OPEN POPUP
    if ctx.triggered_id == "add-attribute":
        return {**style, "display": "flex"}

    # CLOSE POPUP
    return {**style, "display": "none"}


# -------------------------------------------------------------
# 4. POPUP CATEGORY + ATTRIBUTE CLEAN RESET + OPTION FILLING
# -------------------------------------------------------------
@app.callback(
    Output("popup-category-dropdown", "value"),
    Output("add-attribute-dropdown", "options"),
    Output("add-attribute-dropdown", "value"),

    Input("popup-backdrop", "style"),
    Input("popup-category-dropdown", "value"),

    prevent_initial_call=False
)
def reset_or_update_popup(popup_style, category_values):
    ctx = callback_context

    # ---------------------------
    # POPUP JUST OPENED
    # ---------------------------
    if ctx.triggered_id == "popup-backdrop":
        if popup_style.get("display") == "flex":
            # RESET EVERYTHING
            return None, [], None
        else:
            return no_update, no_update, no_update

    # ---------------------------
    # CATEGORY SELECTION CHANGED
    # ---------------------------
    if ctx.triggered_id == "popup-category-dropdown":
        if not category_values:
            return category_values, [], None

        options = []
        for cat in category_values:
            for attr in CATEGORY_ATTRIBUTES[cat]:
                options.append({
                    "label": f"{cat} – {attr}",
                    "value": f"{cat}::{attr}"
                })

        return category_values, options, None

    return no_update, no_update, no_update


# -------------------------------------------------------------
# 5. LOAD GEO OPTIONS BASED ON SCALE
# -------------------------------------------------------------
@app.callback(
    Output("scale-select-dropdown", "options"),
    Input("geo-scale", "value")
)
def load_geo_options(scale):
    if scale == "continent":
        return [{"label": c, "value": c}
                for c in sorted(set(COUNTRY_TO_CONTINENT.values()))]

    if scale == "region":
        return [{"label": r, "value": r}
                for r in sorted(set(COUNTRY_TO_REGION.values()))]

    if scale == "country":
        return [{"label": c, "value": c} for c in ALL_COUNTRIES]

    return []


# -------------------------------------------------------------
# 6. UPDATE GEO TAGS
# -------------------------------------------------------------
@app.callback(
    Output("scale-tags-store", "data"),
    Input("scale-select-dropdown", "value"),
    Input({"type": "delete-geo-tag", "index": ALL}, "n_clicks"),
    State("scale-tags-store", "data"),
    prevent_initial_call=True
)
def update_geo_tag_list(selected, delete_clicks, existing):
    ctx = callback_context

    # UPDATE FROM DROPDOWN
    if ctx.triggered_id == "scale-select-dropdown":
        if not selected:
            return []
        return [{"label": v, "id": v} for v in selected]

    # DELETE A TAG
    if isinstance(ctx.triggered_id, dict):
        remove_id = ctx.triggered_id["index"]
        return [t for t in existing if t["id"] != remove_id]

    return existing


@app.callback(
    Output("select-scale-block", "style"),
    Input("geo-scale", "value")
)
def hide_scale_block(scale):
    if scale == "global":
        return {"display": "none"}  # hide entire block
    return {"display": "block"}


@app.callback(
    Output("scale-select-title", "children"),
    Input("geo-scale", "value")
)
def update_scale_title(scale):
    if scale == "continent":
        return "Select Continent"
    if scale == "region":
        return "Select Region"
    if scale == "country":
        return "Select Country"
    return ""


@app.callback(
    Output("scale-select-dropdown", "value", allow_duplicate=True),
    Input("scale-select-dropdown", "options"),
    Input("map-click", "data"),
    prevent_initial_call=True
)
def fill_country_after_options(options, clicked_country):
    # Do nothing unless both exist
    if not options or not clicked_country:
        return no_update

    option_values = [opt["value"] for opt in options]

    # Only fill once the clicked country appears in the options
    if clicked_country not in option_values:
        return no_update

    # NOW safe to apply the country
    return [clicked_country]


@app.callback(
    Output("scale-select-dropdown", "value", allow_duplicate=True),
    Input("geo-scale", "value"),
    prevent_initial_call=True
)
def clear_dropdown_when_scale_changes(scale):
    return []


# -------------------------------------------------------------
# 7. ATTRIBUTE TAG MANAGEMENT (ADD / DELETE / RESET)
# -------------------------------------------------------------
@app.callback(
    Output("attribute-tags-store", "data"),
    Output("reset-attributes", "disabled"),
    Output("reset-attributes", "className"),

    Input("popup-add", "n_clicks"),
    Input({"type": "delete-tag", "index": ALL}, "n_clicks"),
    Input("reset-attributes", "n_clicks"),

    State("add-attribute-dropdown", "value"),
    State("attribute-tags-store", "data"),

    prevent_initial_call=False
)
def manage_attributes(add_click, delete_clicks, reset_click, new_values, tags):
    ctx = callback_context

    # INITIAL LOAD
    if not ctx.triggered:
        return tags, True, "attr-btn disabled-btn"

    trigger = ctx.triggered_id

    # ---------------- RESET BUTTON ----------------
    if trigger == "reset-attributes" and reset_click:
        return [], True, "attr-btn disabled-btn"

    # ---------------- DELETE INDIV TAG ----------------
    if isinstance(trigger, dict) and trigger.get("type") == "delete-tag":
        idx = trigger["index"]
        updated = [t for t in tags if t["id"] != idx]
        disable = len(updated) == 0
        className = "attr-btn disabled-btn" if disable else "attr-btn"
        return updated, disable, className

    # ---------------- ADD NEW ----------------
    if trigger == "popup-add" and new_values:
        updated = tags.copy()
        for v in new_values:
            if not any(t["id"] == v for t in updated):
                cat, attr = v.split("::")
                updated.append({
                    "label": f"{cat} – {attr}",
                    "id": v
                })

        disable = len(updated) == 0
        className = "attr-btn disabled-btn" if disable else "attr-btn"
        return updated, disable, className

    # ---------------- DEFAULT ----------------
    disable = len(tags) == 0
    className = "attr-btn disabled-btn" if disable else "attr-btn"
    return tags, disable, className


# -------------------------------------------------------------
# 8. TAB CONTENT (INFO / PLOTS / NUMBERS / CREATE)
# -------------------------------------------------------------

def prepare_dataframe(attrs, geo_tags, geo_scale):
    """
    Returns a filtered dataframe based on:
    - selected attributes (to pick the right dataset category)
    - selected geo tags
    - selected geo scale
    """
    if not attrs:
        return None

    # Use the category of the FIRST selected attribute
    cat, _ = attrs[0]["id"].split("::")
    df = DATASETS[cat].copy()

    if geo_scale == "global" or not geo_tags:
        return df

    selected = [t["id"] for t in geo_tags]

    if geo_scale == "continent":
        df = df[df["Continent"].isin(selected)]

    elif geo_scale == "region":
        df = df[df["Region"].isin(selected)]

    elif geo_scale == "country":
        df = df[df["Country"].isin(selected)]

    return df


@app.callback(
    Output("content-panel-info", "children"),
    Output("content-panel-plots", "children"),
    Output("content-panel-numbers", "children"),
    Output("content-panel-create", "children"),
    Output("active-tab", "data"),

    Input({"type": "top-tab", "tab": ALL}, "n_clicks"),
    Input("scale-tags-store", "data"),
    State("attribute-tags-store", "data"),
    State("geo-scale", "value")
)
def update_tabs(clicks, geo_tags, attrs, geo_scale):
    ctx = callback_context
    tab = "info"

    if ctx.triggered and isinstance(ctx.triggered_id, dict):
        tab = ctx.triggered_id["tab"]

    info = plots = numbers = create = html.Div()

    if tab == "info":
        info = render_info_tab(attrs, geo_tags, geo_scale, DATA_INFO)

    elif tab == "plots":
        plots = render_plots_tab([])

    elif tab == "numbers":
        df = prepare_dataframe(attrs, geo_tags, geo_scale)
        numbers = render_numbers_tab(df)

    elif tab == "create":
        create = render_create_tab()

    return info, plots, numbers, create, tab


@app.callback(
    Output("content-panel-info", "style"),
    Output("content-panel-plots", "style"),
    Output("content-panel-numbers", "style"),
    Output("content-panel-create", "style"),
    Input("active-tab", "data")
)
def show_correct_tab(active):
    styles = {
        "info": {"display": "block"},
        "plots": {"display": "block"},
        "numbers": {"display": "block"},
        "create": {"display": "block"},
    }

    # Default hidden
    hidden = {"display": "none"}

    return (
        styles["info"] if active == "info" else hidden,
        styles["plots"] if active == "plots" else hidden,
        styles["numbers"] if active == "numbers" else hidden,
        styles["create"] if active == "create" else hidden,
    )


# -------------------------------------------------------------
# 9. STYLE ACTIVE TAB
# -------------------------------------------------------------
@app.callback(
    Output({"type": "top-tab", "tab": ALL}, "className"),
    Input("active-tab", "data"),
    State({"type": "top-tab", "tab": ALL}, "id")
)
def style_tabs(active, ids):
    out = []
    for tab in ids:
        if tab["tab"] == active:
            out.append("top-tab active")
        else:
            out.append("top-tab")
    return out
