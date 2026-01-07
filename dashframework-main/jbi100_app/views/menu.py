# jbi100_app/views/menu.py
from dash import html, dcc


def layout():
    """
    Minimal navigation menu for Final Report.
    Single entry point to the visualization tool.
    """
    return html.Div(
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "12px 18px",
            "borderBottom": "1px solid rgba(0,0,0,0.08)",
            "background": "white",
        },
        children=[
            html.Div(
                "JBI100 Visualization Tool",
                style={"fontWeight": 900, "fontSize": "14px", "color": "#0b1f3b"},
            ),
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
        ],
    )
