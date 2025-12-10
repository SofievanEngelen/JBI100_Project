# jbi100_app/views/data_view.py
from dash import html, dcc
from jbi100_app.data_loader import CATEGORY_ATTRIBUTES
from jbi100_app.data_loader import COUNTRY_TO_CONTINENT, COUNTRY_TO_REGION, ALL_COUNTRIES


# ------------------------------
# COMPONENT HELPERS
# ------------------------------

def make_tag_component(label, id_type, id_suffix,
                       class_name="tag",
                       delete_class="delete-btn"):
    return html.Div(
        className=class_name,
        children=[
            html.Span(label),
            html.Button(
                "x",
                id={"type": id_type, "index": id_suffix},
                className=delete_class,
            )
        ]
    )


def make_tag(label, id_suffix):
    return make_tag_component(label, "delete-tag", id_suffix)


def make_geo_tag(label, id_suffix):
    return make_tag_component(label, "delete-geo-tag", id_suffix)


def make_tab(label):
    return html.Button(
        label,
        id={"type": "top-tab", "tab": label.lower()},
        className="top-tab",
        style={"borderRadius": "0"}
    )


# ------------------------------
# POPUP BUILDER
# ------------------------------

def make_popup():
    category_options = [
        {"label": c, "value": c} for c in CATEGORY_ATTRIBUTES.keys()
    ]

    return html.Div(
        id="popup-box",
        style={
            "width": "420px",
            "padding": "20px",
            "borderRadius": "10px",
            "backgroundColor": "white",
            "boxShadow": "0px 4px 12px rgba(0,0,0,0.2)",
            "display": "flex",
            "flexDirection": "column",
            "gap": "15px",
        },
        children=[
            html.H3("Select attributes to add"),

            html.Div([
                html.Label("Select Categories"),
                dcc.Dropdown(
                    id="popup-category-dropdown",
                    options=category_options,
                    multi=True,
                ),
                html.Br(),

                html.Label("Select Attributes"),
                dcc.Dropdown(
                    id="add-attribute-dropdown",
                    options=[],
                    multi=True,
                ),
            ]),

            html.Div(
                style={"display": "flex",
                       "justifyContent": "flex-end",
                       "gap": "10px"},
                children=[
                    html.Button("Cancel", id="popup-cancel", className="popup-btn"),
                    html.Button("Add", id="popup-add", className="popup-btn"),
                ],
            ),
        ],
    )


# ------------------------------
# DATA VIEW MAIN LAYOUT
# ------------------------------

def data_view_layout():
    return html.Div(
        id="data-view",
        style={"display": "flex", "height": "100vh"},
        children=[

            # LEFT PANEL
            html.Div(
                id="left-panel",
                style={
                    "width": "25%",
                    "backgroundColor": "#F2F2F2",
                    "padding": "20px",
                    "display": "flex",
                    "flexDirection": "column",
                    "position": "relative",
                    "overflowY": "auto",
                },
                children=[

                    html.H2("Data view", className="section-title"),

                    # --- ATTRIBUTE SELECTION ---
                    html.H4("Select Attributes", className="section-subtitle"),

                    # Attribute tag storage
                    dcc.Store(id="attribute-tags-store", data=[]),

                    # Empty box styled like screenshot
                    html.Div(
                        id="attr-tags",
                        className="attr-box",
                        children=[],
                    ),

                    # Buttons row
                    html.Div(
                        style={"display": "flex", "gap": "10px", "place-items": "center"},
                        children=[
                            # Reset (starts disabled)
                            html.Button(
                                "Reset",
                                id="reset-attributes",
                                className="attr-btn disabled-btn",
                                disabled=True
                            ),

                            # Add new (always enabled)
                            html.Button(
                                "+ Add new",
                                id="add-attribute",
                                className="attr-btn",
                                disabled=False
                            ),
                        ],
                    ),

                    html.Div(
                        id="popup-backdrop",
                        style={
                            "position": "fixed",
                            "top": 0, "left": 0,
                            "width": "100%", "height": "100%",
                            "backgroundColor": "rgba(0,0,0,0.4)",
                            "display": "none",
                            "justifyContent": "center",
                            "alignItems": "center",
                            "zIndex": 9999,
                        },
                        children=[make_popup()],
                    ),

                    # --- GEOGRAPHICAL SCALE ---
                    html.H4("Select Geographical Scale", className="section-subtitle"),

                    dcc.RadioItems(
                        id="geo-scale",
                        options=[
                            {"label": "Global", "value": "global"},
                            {"label": "Continent", "value": "continent"},
                            {"label": "Region", "value": "region"},
                            {"label": "Country", "value": "country"},
                        ],
                        value="global",
                        className="radio-group",
                    ),

                    dcc.Store(id="scale-tags-store", data=[]),

                    html.Div(
                        id="select-scale-block",
                        children=[
                            html.H4(id="scale-select-title", className="section-subtitle"),

                            dcc.Dropdown(
                                id="scale-select-dropdown",
                                options=[],
                                multi=True,
                                searchable=True,
                                placeholder="Select items…",
                                style={"marginBottom": "10px"},
                            ),
                            html.Div(id="selected-tags", className="tag-container"),
                        ],
                    ),

                    # --- BOTTOM NAV BUTTON ---
                    html.Div(
                        id="data-nav-button-container",
                        style={
                            "position": "absolute",
                            "bottom": "20px",
                            "left": "20px",
                            "right": "20px",
                        },
                        children=[
                            html.Button(
                                "Map view",
                                id="bottom-nav-button",
                                className="switch-view-button"
                            )
                        ]
                    ),
                ],
            ),

            # RIGHT PANEL
            html.Div(
                id="right-panel",
                style={
                    "flex": 1,
                    "display": "flex",
                    "flexDirection": "column",
                    "backgroundColor": "white",
                },
                children=[

                    # TOP TABS
                    html.Div(
                        id="top-tabs",
                        style={
                            "display": "flex",
                            "backgroundColor": "#4F4F4F",
                        },
                        children=[
                            make_tab("Info"),
                            make_tab("Plots"),
                            make_tab("Numbers"),
                            make_tab("Create"),
                        ],
                    ),

                    # STORE ACTIVE TAB
                    dcc.Store(id="active-tab", data="info"),

                    # RIGHT PANEL CONTENT
                    html.Div(
                        id="content-panel",
                        style={
                            "flex": 1,
                            "padding": "20px",
                        },
                        children=[
                            html.Div(id="content-panel-info", style={"display": "block"}),  # Loaded dynamically
                            html.Div(id="content-panel-plots", style={"display": "none"}),  # Loaded dynamically
                            html.Div(id="content-panel-numbers", style={"display": "none"}),  # Loaded dynamically
                            html.Div(id="content-panel-create", style={"display": "none"})  # Loaded dynamically
                        ],
                    ),
                ],
            ),
        ],
    )
