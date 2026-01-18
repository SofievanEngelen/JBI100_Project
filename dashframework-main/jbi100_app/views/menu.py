from dash import html, dcc
import dash_bootstrap_components as dbc


def layout():
    """
    Minimal navigation menu for Final Report.
    Single entry point to the visualization tool.
    Includes dark mode toggle.
    """
    return html.Div(
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "12px 18px",
            "borderBottom": "1px solid var(--border)",
            "background": "var(--bg-panel)",
            "marginBottom": "10px",
            "position": "relative",
            "zIndex": 2000,
        },
        children=[
            # ── Left: title
            html.Div(
                "JBI100 Visualization Tool",
                style={
                    "fontWeight": 900,
                    "fontSize": "14px",
                    "color": "var(--text-main)",
                },
            ),

            # ── Right: nav + dark mode toggle
            html.Div(
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "16px",
                },
                children=[
                    dcc.Link(
                        "Visualisation",
                        href="/vis",
                        style={
                            "fontWeight": 800,
                            "fontSize": "13px",
                            "color": "#2b66e3",
                            "textDecoration": "none",
                        },
                    ),

                    dbc.Switch(
                        id="theme-toggle",
                        label="Dark mode",
                        value=False,
                        style={
                            "fontSize": "12px",
                            "color": "var(--text-main)",
                        },
                    ),
                ],
            ),
        ],
    )
