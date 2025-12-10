from dash import html, dcc

PLOT_TYPES = [
    {"label": "Scatter Plot", "value": "scatter"},
    {"label": "Line Chart", "value": "line"},
    {"label": "Bar Chart", "value": "bar"},
    {"label": "Histogram", "value": "histogram"},
]


def render_create_tab():
    return html.Div([
        html.H3("Create Custom Visualisation"),

        html.Label("Choose plot type"),
        dcc.Dropdown(
            id="create-vis-type",
            options=PLOT_TYPES,
            placeholder="Select visualisation type…",
            style={"width": "300px", "marginBottom": "20px"}
        ),

        html.Div(id="create-vis-field-container"),

        html.Button(
            "Generate Plot",
            id="create-vis-submit",
            className="attr-btn",
            style={"marginTop": "20px"}
        ),

        html.Div(id="create-vis-output", style={"marginTop": "30px"})
    ])
