from __future__ import annotations

from dash import Input, Output, callback, html

from jbi100_app.data.attributes import ATTRIBUTE_METADATA, attribute_scale


# =============================================================================
# Attribute lookup panel
# =============================================================================

@callback(
    Output("attr-lookup-panel", "children"),
    Output("attr-lookup-panel", "style"),
    Input("attr-lookup-dd", "value"),
)
def update_attribute_lookup(attr: str | None):
    """
    Update the attribute information panel based on the selected attribute.

    Displays metadata including:
    - display name
    - unit
    - category
    - scale interpretation
    - description
    - guidance on how to read the attribute
    """
    if not attr or attr not in ATTRIBUTE_METADATA.index:
        return None, {"display": "none"}

    row = ATTRIBUTE_METADATA.loc[attr]
    scale = attribute_scale(attr)

    scale_label = (
        "Logarithmic (relative comparison)"
        if scale == "log"
        else "Linear (absolute values)"
    )

    children = [
        html.Div(
            [
                html.Span(
                    row["Display_name"],
                    style={"fontWeight": "800"},
                ),
                html.Span(
                    f" ({row['Unit']})" if row["Unit"] else "",
                    style={"color": "var(--text-muted)"},
                ),
                html.Span(
                    row["Category"],
                    style={
                        "float": "right",
                        "fontSize": "11px",
                        "fontWeight": "700",
                        "color": "var(--accent)",
                    },
                ),
            ],
            style={"marginBottom": "6px"},
        ),
        html.Div(
            f"Scale: {scale_label}",
            style={
                "fontSize": "11px",
                "color": "var(--text-muted)",
                "marginBottom": "6px",
            },
        ),
        html.Div("Description", style={"fontWeight": "800"}),
        html.Div(row["Description"], style={"marginBottom": "8px"}),
        html.Div("How to read", style={"fontWeight": "800"}),
        html.Div(row["Interpretation"]),
    ]

    return (
        children,
        {
            "display": "block",
            "marginTop": "10px",
            "padding": "10px",
            "border": "1px solid var(--border)",
            "borderRadius": "10px",
            "background": "var(--bg-card)",
            "fontSize": "12px",
            "color": "var(--text-main)",
        },
    )


# =============================================================================
# Theme handling
# =============================================================================

@callback(
    Output("theme-store", "data"),
    Input("theme-toggle", "value"),
)
def set_theme(is_dark: bool) -> str:
    """
    Store the current theme selection.
    """
    return "dark" if is_dark else "light"


@callback(
    Output("root", "data-theme"),
    Input("theme-store", "data"),
)
def apply_theme(theme: str) -> str:
    """
    Apply the stored theme to the root container.
    """
    return theme
