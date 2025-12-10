# app.py
from dash import html, dcc, Input, Output, State
from main import app

# Import layouts
from jbi100_app.views.data_view import data_view_layout
from jbi100_app.views.map_view import map_view_layout

# Import callbacks
from jbi100_app.callbacks import data_callbacks  # noqa
from jbi100_app.callbacks import map_callbacks   # noqa


# ========= PAGE LAYOUT =========

app.layout = html.Div(
    id="app-container",
    children=[

        html.Div(
            id="page-content",
            children=[
                html.Div(id="map-view-wrapper",
                         style={"display": "none"},
                         children=map_view_layout()),

                html.Div(id="data-view-wrapper",
                         style={"display": "block"},
                         children=data_view_layout()),
            ],
        ),

        dcc.Store(id="current-page", data="data"),
        dcc.Store(id="map-click", data=None)
    ],
)


# ========= PAGE SWITCHING =========

@app.callback(
    Output("current-page", "data"),
    Input("bottom-nav-button", "n_clicks"),
    State("current-page", "data"),
    prevent_initial_call=True
)
def toggle_page(n, current):
    return "data" if current == "map" else "map"


@app.callback(
    Output("bottom-nav-button", "children"),
    Input("current-page", "data")
)
def update_btn(page):
    return "Go to Data View" if page == "map" else "Go to Map View"


@app.callback(
    Output("map-view-wrapper", "style"),
    Output("data-view-wrapper", "style"),
    Input("current-page", "data")
)
def update_visibility(page):
    if page == "map":
        return {"display": "block"}, {"display": "none"}
    return {"display": "none"}, {"display": "block"}


if __name__ == "__main__":
    app.run(debug=True)
