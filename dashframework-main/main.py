# dashframework-main/main.py
import dash
from dash import Dash, html, dcc, Input, Output

from jbi100_app.views.landing import layout as landing_layout
from jbi100_app.views.layout import layout as vis_layout
from jbi100_app.views.menu import layout as menu_layout

from jbi100_app.callbacks import onboarding_callbacks  # noqa: F401
from jbi100_app.callbacks import right_panel_callbacks  # noqa: F401
from jbi100_app.callbacks import selection_callbacks
from jbi100_app.callbacks import map_callbacks
from jbi100_app.callbacks import scatter_callbacks
from jbi100_app.callbacks import distribution_callbacks
from jbi100_app.callbacks import pcp_callbacks
from jbi100_app.callbacks import radar_callbacks

app = Dash(__name__, suppress_callback_exceptions=True)
app.title = "JBI100 Dashboard"

app.layout = html.Div(
    [
        dcc.Location(id="url"),
        dcc.Store(id="session-store", storage_type="session"),
        html.Div(id="page-content"),
    ]
)

app.validation_layout = html.Div(
    [
        dcc.Location(id="url"),
        menu_layout(),
        landing_layout() if callable(landing_layout) else landing_layout,
        vis_layout() if callable(vis_layout) else vis_layout,
    ]
)


@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname in (None, "/"):
        return landing_layout() if callable(landing_layout) else landing_layout

    if pathname == "/vis":
        return html.Div(
            style={
                "height": "100vh",
                "display": "flex",
                "flexDirection": "column",
                "overflow": "hidden",  # disables page scroll
            },
            children=[
                menu_layout(),
                html.Div(
                    style={
                        "flex": "1",
                        "minHeight": 0,  # IMPORTANT so children can shrink
                        "overflow": "hidden"
                    },
                    children=vis_layout() if callable(vis_layout) else vis_layout,
                ),
            ],
        )

    return html.Div("404 - Page not found", style={"padding": "24px"})


@app.callback(
    Output("url", "pathname"),
    Input("ob-start", "n_clicks"),
    prevent_initial_call=True,
)
def go_to_visualisation(n_start):
    if n_start and n_start > 0:
        return "/vis"
    return dash.no_update


if __name__ == "__main__":
    app.run(debug=True)
