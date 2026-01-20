from __future__ import annotations

from dash import html, dcc
import dash_bootstrap_components as dbc


def layout() -> html.Div:
    """
    Top navigation bar for the application.

    Provides:
    - App title (left)
    - Dark mode toggle switch (right)

    This component is intentionally minimal and stateless.
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
            # ─────────────────────────────────────────────
            # Left: Application title
            # ─────────────────────────────────────────────
            html.Div(
                "MUN Digital Debate Coach",
                style={
                    "fontWeight": 900,
                    "fontSize": "14px",
                    "color": "var(--text-main)",
                },
            ),

            # ─────────────────────────────────────────────
            # Right: Navigation + theme toggle
            # ─────────────────────────────────────────────
            html.Div(
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "16px",
                },
                children=[
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
