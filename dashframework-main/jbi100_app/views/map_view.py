from dash import html, dcc
from jbi100_app.data_loader import CATEGORY_ATTRIBUTES, ALL_COUNTRIES, COUNTRY_TO_REGION, COUNTRY_TO_CONTINENT


def map_view_layout() -> html.Div:
    category_list = list(CATEGORY_ATTRIBUTES.keys())

    # Dynamic region list (UN M49)
    REGION_OPTIONS = ["Global"] + sorted(set(COUNTRY_TO_REGION.values()))

    return html.Div(
        id="map-view",
        style={"display": "flex", "height": "100vh"},
        children=[

            # LEFT SIDEBAR
            html.Div(
                id="map-left-panel",
                children=[

                    html.H2("Map view", className="section-title"),

                    # -------------------------
                    # ATTRIBUTE SELECTION
                    # -------------------------
                    html.H4("ATTRIBUTE SELECTION", className="section-subtitle"),

                    html.Label("Select category"),
                    dcc.Dropdown(
                        id="category-dropdown",
                        options=[{"label": c, "value": c} for c in category_list],
                        value=None,
                        clearable=False,
                    ),

                    html.Label("Select attribute"),
                    dcc.Dropdown(
                        id="attr-dropdown",
                        options=[],
                        value=None,
                        clearable=False,
                    ),

                    # -------------------------
                    # VIEW SELECTION
                    # -------------------------
                    html.H4("VIEW SELECTION", className="section-subtitle"),

                    dcc.RadioItems(
                        id="view-radio",
                        options=[
                            {"label": "Global", "value": "Global"},
                            {"label": "Continent", "value": "Continent"},
                            {"label": "Region", "value": "Region"},
                        ],
                        value="Global",
                        className="radio-group",
                    ),

                    html.Label("Select continent / region"),
                    dcc.Dropdown(
                        id="region-dropdown",
                        options=[{"label": r, "value": r} for r in REGION_OPTIONS],
                        value="Global",
                        clearable=False,
                    ),

                    html.Div(
                        id="map-nav-button-container",
                        children=[
                            html.Button(
                                "Go to Data View",
                                id="bottom-nav-button",
                                className="switch-view-button"
                            )
                        ]
                    )
                ],
            ),

            # RIGHT PANEL (MAP)
            html.Div(
                id="map-right-panel",
                children=[
                    # --- SEARCH BAR AT TOP ---
                    html.Div(
                        id="map-search-container",
                        children=[
                            html.Div(
                                id="search-inner-wrapper",
                                children=[
                                    html.Span(
                                        id="search-icon",
                                        children=[
                                            html.I(className="search-icon-svg")
                                        ]
                                    ),
                                    dcc.Dropdown(
                                        id="search-country",
                                        options=[{"label": c, "value": c} for c in ALL_COUNTRIES],
                                        searchable=True,
                                        clearable=True,
                                        placeholder="Search country",
                                    )
                                ]
                            )
                        ]
                    ),

                    # --- MAP BELOW ---
                    dcc.Graph(id="mun-map",
                              style={"height": "100%"},
                              )
                ],
            ),

        ],
    )
