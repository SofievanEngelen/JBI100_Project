from dash import html


# Main Map View Layout
def map_view_layout() -> html.Div:
    """
    Build the complete two-panel map view layout.

    The layout includes:\n
    – Left sidebar:
        • Map controls (filters, layers, interactions — placeholder for now)
    – Right panel:
        • Title area
        • Main map canvas (placeholder container)

    :return: The full structured dashboard layout for the map view.
    """
    return html.Div(
        id="map-view",
        style={"display": "flex", "height": "100vh"},
        children=[

            # LEFT SIDEBAR
            html.Div(
                id="map-left-panel",
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

                    # Title
                    html.H3("Map Controls", className="section-title"),

                    # Placeholder for future map-related controls
                    html.Div(
                        children="Sidebar content for Map View",
                        style={
                            "backgroundColor": "white",
                            "padding": "10px",
                            "borderRadius": "8px",
                        },
                    ),
                ],
            ),

            # MAIN MAP CONTENT
            html.Div(
                id="map-right-panel",
                style={
                    "flex": 1,
                    "backgroundColor": "white",
                    "padding": "20px",
                    "borderTop": "2px solid #a0c7dd",
                },
                children=[

                    # Map title
                    html.H2("Map View", style={"marginBottom": "15px"}),

                    # Placeholder map container
                    html.Div(
                        children="Map goes here",
                        style={
                            "height": "100%",
                            "backgroundColor": "#eef5fb",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "border": "2px dashed #a0c7dd",
                            "borderRadius": "10px",
                        },
                    ),
                ],
            ),
        ],
    )
