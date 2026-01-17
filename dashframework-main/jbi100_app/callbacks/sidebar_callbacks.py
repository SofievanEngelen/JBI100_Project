from dash import Input, Output, callback, html

from jbi100_app.data.attributes import ATTRIBUTE_METADATA, attribute_scale


@callback(
    Output("attr-lookup-panel", "children"),
    Output("attr-lookup-panel", "style"),
    Input("attr-lookup-dd", "value"),
)
def update_attribute_lookup(attr):
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
                    style={"color": "#6b7280"},
                ),
                html.Span(
                    row["Category"],
                    style={
                        "float": "right",
                        "fontSize": "11px",
                        "fontWeight": "700",
                        "color": "#2563eb",
                    },
                ),
            ],
            style={"marginBottom": "6px"},
        ),
        html.Div(
            f"Scale: {scale_label}",
            style={
                "fontSize": "11px",
                "color": "#6b7280",
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
            "border": "1px solid rgba(148,163,184,0.35)",
            "borderRadius": "10px",
            "background": "#fbfcff",
            "fontSize": "12px",
            "color": "#1f2937",
        },
    )
