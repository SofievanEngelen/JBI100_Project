from dash import html, dcc

def render_plots_tab(figures):
    # `figures` = list of plotly figures
    return html.Div([
        html.H3("Plots"),

        *[
            html.Div([
                dcc.Graph(figure=f),
                html.Hr()
            ]) for f in figures
        ]
    ])
