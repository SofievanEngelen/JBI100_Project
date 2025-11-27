from dash import html

def make_menu_layout():
    return html.Div(
        id="menu-container",
        children=[
            html.Button("Map view", id="btn-map", className="nav-button"),
            html.Button("Data view", id="btn-data", className="nav-button"),
        ]
    )
