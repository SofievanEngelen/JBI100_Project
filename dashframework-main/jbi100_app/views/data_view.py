from dash import html, dcc


# COMPONENT FACTORY FUNCTIONS
def make_tag_component(label: str,
                       id_type: str,
                       id_suffix: str,
                       class_name: str = "tag",
                       delete_class: str = "delete-btn") -> html.Div:
    """
    General-purpose tag builder.

    :param label: Text displayed inside the tag.
    :param id_type: Value for the 'type' field in pattern-matching callbacks.
        (e.g., "delete-tag", "delete-geo-tag")
    :param id_suffix: Unique index or identifier.
    :param class_name: CSS class for the outer tag container.
    :param delete_class: CSS class for the delete button.
    :return: Dash component representing a tag with a delete button.
    """
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


def make_tag(label: str, id_suffix: str) -> html.Div:
    return make_tag_component(label, "delete-tag", id_suffix)


def make_geo_tag(label: str, id_suffix: str) -> html.Div:
    return make_tag_component(label, "delete-geo-tag", id_suffix)


def make_tab(label: str) -> html.Button:
    """
    Create a top navigation tab button.

    :param label: Label shown on the tab.
    :return: A styled button acting as a top-level tab.
    """
    return html.Button(
        label,
        id={"type": "top-tab", "tab": label.lower()},
        className="top-tab"
    )


def make_popup() -> html.Div:
    """
    Create the popup box for selecting new attributes.

    :return: A popup modal containing a multi-select dropdown and action buttons.
    """
    return html.Div(
        id="popup-box",
        style={
            "width": "400px",
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

            dcc.Dropdown(
                id="add-attribute-dropdown",
                options=["Attribute A", "Attribute B", "Attribute C"],
                multi=True,
            ),

            # Required action buttons for callbacks
            html.Div(
                style={
                    "display": "flex",
                    "justifyContent": "flex-end",
                    "gap": "10px",
                    "marginTop": "10px",
                },
                children=[
                    html.Button(
                        "Cancel",
                        id="popup-cancel",
                        className="popup-btn"
                    ),
                    html.Button(
                        "Add",
                        id="popup-add",
                        className="popup-btn"
                    ),
                ],
            ),
        ],
    )


def data_view_layout() -> html.Div:
    """
    Build the complete two-panel data view layout.

    The layout includes:\n
    – Left sidebar:
        • Attribute tag management
        • Geographic scale selection
        • Geographic item picker (continent / region / country)
    – Right panel:
        • Navigation tabs
        • Main content area showing active selections

    :return: The full structured dashboard layout.
    """
    return html.Div(
        id="data-view",
        style={"display": "flex", "height": "100vh"},
        children=[

            # LEFT SIDEBAR
            html.Div(
                id="left-panel",
                style={
                    "width": "25%",
                    "backgroundColor": "#b5d9ea",
                    "padding": "10px",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "20px",
                    "overflowY": "auto",
                },
                children=[

                    # Attribute selection area
                    # #TODO: attach this to data so it automatically lists attributes
                    html.Div([
                        html.H3("Attributes", className="section-title"),

                        # Storage for attribute tag values
                        dcc.Store(id="attribute-tags-store", data=[]),

                        # Container where attribute tags are dynamically inserted
                        html.Div(id="attr-tags", className="tag-container"),

                        html.Button(children="+ Add new",
                                    id="add-attribute",
                                    className="add-button"),

                        # Popup modal backdrop (hidden by default)
                        html.Div(
                            id="popup-backdrop",
                            style={
                                "position": "fixed",
                                "top": 0,
                                "left": 0,
                                "width": "100%",
                                "height": "100%",
                                "backgroundColor": "rgba(0,0,0,0.4)",
                                "display": "none",
                                "justifyContent": "center",
                                "alignItems": "center",
                                "zIndex": 9999,
                            },
                            children=[make_popup()],
                        ),
                    ]),

                    # Geographic scale radio selector
                    html.Div([
                        html.H3("Geographical scale", className="section-title"),
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
                    ]),

                    # Store for selected scale tags (continents/regions/countries)
                    dcc.Store(id="scale-tags-store", data=[]),

                    # Dropdown for selecting items at chosen geography level
                    html.Div(
                        id="select-scale-block",
                        children=[
                            html.H3(id="scale-select-title", className="section-title"),

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
                ],
            ),

            # MAIN CONTENT
            html.Div(
                id="right-panel",
                style={
                    "flex": 1,
                    "backgroundColor": "white",
                    "display": "flex",
                    "flexDirection": "column",
                },
                children=[

                    # Top tabs
                    html.Div(
                        id="top-tabs",
                        style={
                            "display": "flex",
                            "backgroundColor": "#c5e1f2",
                            "padding": "8px",
                            "gap": "10px",
                        },
                        children=[
                            make_tab("Info"),
                            make_tab("Plots"),
                            make_tab("Numbers"),
                            make_tab("Create"),
                        ],
                    ),

                    # Main content display
                    html.Div(
                        id="content-panel",
                        style={
                            "flex": 1,
                            "backgroundColor": "white",
                            "borderTop": "2px solid #a0c7dd",
                            "padding": "20px",
                        },
                        children=[
                            html.H3(children="Selected Attributes:",
                                    style={"marginBottom": "10px"}),
                            html.Div(id="content-attribute-tags",
                                     className="tag-container"),
                            html.H4(id="current-scale-display",
                                    style={"marginTop": "15px"}),
                        ],
                    ),
                ],
            ),
        ],
    )
