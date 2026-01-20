from __future__ import annotations

from typing import Any

from dash import html, dcc
import dash_bootstrap_components as dbc

from jbi100_app.views.menu import layout as menu_layout
from jbi100_app.data.data_loader import DATA_INFO, ALL_COUNTRIES
from jbi100_app.data.attributes import (
    attribute_display_label,
    all_numeric_attributes,
)

# =============================================================================
# Helpers
# =============================================================================

def _card(
    children: Any,
    *,
    style_extra: dict[str, Any] | None = None,
    class_name: str | None = None,
) -> html.Div:
    """
    Generic card wrapper used for sidebar containers.
    """
    style = {
        "background": "var(--bg-card)",
        "borderRadius": "14px",
        "boxShadow": "0 6px 18px rgba(0,0,0,0.25)",
        "border": "1px solid var(--border)",
        "padding": "12px",
        "minHeight": 0,
    }

    if style_extra:
        style.update(style_extra)

    return html.Div(style=style, children=children, className=class_name)


def _onboarding_card(title: str, text: str, icon: str) -> html.Div:
    """
    Small feature card used inside the onboarding modal.
    """
    return html.Div(
        style={
            "background": "white",
            "borderRadius": "14px",
            "padding": "16px",
            "boxShadow": "0 10px 22px rgba(0,0,0,0.06)",
            "border": "1px solid rgba(148,163,184,0.25)",
            "display": "flex",
            "gap": "10px",
            "alignItems": "center",
            "justifyContent": "center",
            "minHeight": "100px",
        },
        children=[
            html.Div(
                [
                    html.Div(
                        title,
                        style={
                            "fontWeight": "800",
                            "fontSize": "15px",
                            "marginBottom": "4px",
                        },
                    ),
                    html.Div(
                        text,
                        style={
                            "fontSize": "13px",
                            "color": "#475569",
                            "lineHeight": "1.35",
                        },
                    ),
                ]
            ),
            html.Div(
                icon,
                style={
                    "fontSize": "26px",
                    "lineHeight": "1",
                },
            ),
        ],
    )


def _panel(
    children: Any,
    *,
    style_extra: dict[str, Any] | None = None,
) -> html.Div:
    """
    Main visualisation panel container (grey background).
    """
    style = {
        "height": "100%",
        "background": "var(--bg-panel)",
        "borderRadius": "18px",
        "padding": "18px 22px",
        "boxSizing": "border-box",
        "display": "flex",
        "flexDirection": "column",
        "gap": "12px",
        "minHeight": 0,
        "border": "1px solid var(--border)",
    }

    if style_extra:
        style.update(style_extra)

    return html.Div(style=style, children=children)


def _plot_wrap(
    children: Any,
    *,
    style_extra: dict[str, Any] | None = None,
) -> html.Div:
    """
    White inner container that wraps Plotly graphs.
    """
    style = {
        "background": "var(--bg-card)",
        "borderRadius": "12px",
        "padding": "10px",
        "boxSizing": "border-box",
        "flex": "1",
        "minHeight": 0,
        "border": "1px solid var(--border)",
    }

    if style_extra:
        style.update(style_extra)

    return html.Div(style=style, children=children)


# =============================================================================
# Shared constants
# =============================================================================

_ALL_ATTRS: list[str] = all_numeric_attributes(DATA_INFO)

ATTRIBUTE_OPTIONS = [
    {"label": attribute_display_label(a), "value": a}
    for a in sorted(_ALL_ATTRS, key=lambda a: attribute_display_label(a).lower())
]

PLOT_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}

# =============================================================================
# Layout
# =============================================================================

layout = html.Div(
    id="root",
    **{"data-theme": "light"},
    style={
        "height": "100%",
        "width": "100%",
        "padding": "10px 10px 25px 10px",
        "boxSizing": "border-box",
        "background": "var(--bg-main)",
        "color": "var(--text-main)",
    },
    children=[
        # ─────────────────────────────────────────────────────────────
        # Top navigation bar
        # ─────────────────────────────────────────────────────────────
        menu_layout(),

        # ─────────────────────────────────────────────────────────────
        # Main app grid
        # ─────────────────────────────────────────────────────────────
        html.Div(
            id="app-root",
            style={
                "height": "93%",
                "display": "grid",
                "gridTemplateColumns": "275px 1fr",
                "gap": "12px",
                "minHeight": 0,
                "marginTop": "12px",
            },
            children=[
                # ======================================================
                # Sidebar
                # ======================================================
                _card(
                    class_name="sidebar-card",
                    style_extra={
                        "display": "flex",
                        "flexDirection": "column",
                        "padding": "12px 12px 25px 12px",
                        "height": "100%",
                        "minHeight": 0,
                    },
                    children=[
                        # ── Popups
                        dcc.ConfirmDialog(id="vis-country-limit-dialog", message="", displayed=False),
                        dcc.ConfirmDialog(id="vis-attr-limit-dialog", message="", displayed=False),

                        # ── Title
                        html.Div(
                            "Visualization Tool",
                            style={
                                "fontSize": "16px",
                                "fontWeight": "900",
                                "marginBottom": "6px",
                            },
                        ),

                        # ── Country selection
                        html.Div(
                            "Select Country (max 6)",
                            style={
                                "fontSize": "11px",
                                "fontWeight": "800",
                                "color": "var(--text-muted)",
                            },
                        ),
                        dcc.Dropdown(
                            id="vis-country",
                            options=[],
                            value=[],
                            multi=True,
                            placeholder="Find country",
                            style={"paddingBottom": "10px"},
                        ),

                        # ── Geo scale
                        html.Div(
                            "Select Scale",
                            style={
                                "fontSize": "11px",
                                "fontWeight": "800",
                                "color": "var(--text-muted)",
                            },
                        ),
                        dcc.RadioItems(
                            id="vis-geo-scale",
                            value="global",
                            options=[
                                {"label": "Global", "value": "global"},
                                {"label": "Continent", "value": "continent"},
                                {"label": "Region", "value": "region"},
                            ],
                            style={"marginTop": "4px", "marginBottom": "6px"},
                            inputStyle={"marginRight": "8px"},
                        ),

                        # ── Geo scope dropdown (conditional)
                        html.Div(
                            id="vis-geo-scope-container",
                            style={"display": "none", "marginBottom": "6px"},
                            children=[
                                html.Div(
                                    "Visible area",
                                    style={
                                        "fontSize": "11px",
                                        "fontWeight": "800",
                                        "color": "var(--text-muted)",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="vis-geo-scope-dd",
                                    options=[],
                                    value=None,
                                    clearable=False,
                                    placeholder="Select continent / region",
                                ),
                            ],
                        ),

                        # ── Warnings & reset
                        html.Div(id="vis-warnings", style={"fontSize": "11px"}),
                        html.Button(
                            "Clear filter",
                            id="vis-clear-all",
                            className="clear-filter-btn",
                            n_clicks=0,
                            style={"width": "100%", "marginBottom": "6px"},
                        ),

                        html.Hr(style={"margin": "8px 0"}),

                        # ── Attribute lookup
                        html.Div(
                            "Understand Attributes",
                            style={
                                "fontSize": "12px",
                                "fontWeight": "800",
                                "color": "var(--text-muted)",
                                "marginBottom": "6px",
                            },
                        ),
                        dcc.Dropdown(
                            id="attr-lookup-dd",
                            options=[
                                {"label": attribute_display_label(a), "value": a}
                                for a in sorted(
                                    all_numeric_attributes(DATA_INFO),
                                    key=lambda a: attribute_display_label(a).lower(),
                                )
                            ],
                            placeholder="Search attribute",
                            clearable=True,
                        ),
                        html.Div(
                            id="attr-lookup-panel",
                            style={
                                "marginTop": "10px",
                                "padding": "10px",
                                "border": "1px solid var(--border)",
                                "borderRadius": "10px",
                                "background": "var(--bg-card)",
                                "fontSize": "12px",
                                "display": "none",
                            },
                        ),

                        # ── Stores
                        dcc.Store(id="pcp-brush-store", data=None),
                        dcc.Store(id="vis-selection-store", data=[]),
                        dcc.Store(id="pcp-dims-store", data=None),
                        dcc.Store(id="radar-attr-store", data=None),
                        dcc.Store(id="vis-selected-attributes"),
                    ],
                ),

                # ======================================================
                # Main visualization area
                # ======================================================
                html.Div(
                    style={
                        "height": "100%",
                        "display": "grid",
                        "gridTemplateRows": "50% 50%",
                        "gap": "12px",
                        "minHeight": 0,
                    },
                    children=[
                        # ── Top row (Map + Right panel)
                        html.Div(
                            style={
                                "display": "grid",
                                "gridTemplateColumns": "minmax(0, 1fr) minmax(0, 50%)",
                                "gap": "12px",
                                "minHeight": 0,
                            },
                            children=[
                                # Map panel
                                _panel(
                                    children=[
                                        html.Div(
                                            style={
                                                "display": "flex",
                                                "justifyContent": "space-between",
                                                "alignItems": "center",
                                                "gap": "12px",
                                            },
                                            children=[
                                                html.Div(
                                                    "Map",
                                                    style={"fontSize": "18px", "fontWeight": "900"},
                                                ),
                                                dcc.Dropdown(
                                                    id="vis-metric",
                                                    options=ATTRIBUTE_OPTIONS,
                                                    value=_ALL_ATTRS[0] if _ALL_ATTRS else None,
                                                    clearable=False,
                                                    style={"width": "400px"},
                                                ),
                                            ],
                                        ),
                                        _plot_wrap(
                                            dcc.Graph(
                                                id="vis-map",
                                                config=PLOT_CONFIG,
                                                style={"height": "100%", "width": "100%"},
                                            )
                                        ),
                                    ],
                                ),

                                # Right visualization panel
                                _panel(
                                    style_extra={"maxWidth": "50%"},
                                    children=[
                                        # Title + viz selector
                                        html.Div(
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                            },
                                            children=[
                                                html.Div(
                                                    "Select Visualisation",
                                                    style={
                                                        "fontSize": "18px",
                                                        "fontWeight": "900",
                                                        "whiteSpace": "nowrap",
                                                    },
                                                ),
                                                dcc.Dropdown(
                                                    id="vis-right-viz",
                                                    options=[
                                                        {"label": "Scatter plot", "value": "scatter"},
                                                        {"label": "Histogram", "value": "hist"},
                                                        {"label": "Violin plot", "value": "violin"},
                                                        {"label": "Radar plot", "value": "radar"},
                                                    ],
                                                    value="scatter",
                                                    clearable=False,
                                                    style={"minWidth": "220px", "marginLeft": "auto"},
                                                ),
                                            ],
                                        ),

                                        # Controls (shown/hidden by callbacks)
                                        html.Div(
                                            id="vis-controls-scatter",
                                            style={
                                                "display": "grid",
                                                "gridTemplateColumns": "1fr 1fr",
                                                "gap": "14px",
                                            },
                                            children=[
                                                dcc.Dropdown(id="vis-scatter-x", options=[], clearable=False),
                                                dcc.Dropdown(id="vis-scatter-y", options=[], clearable=False),
                                            ],
                                        ),

                                        html.Div(
                                            id="vis-controls-hist",
                                            style={
                                                "display": "none",
                                                "gridTemplateColumns": "1fr 1fr",
                                                "gap": "18px",
                                                "alignItems": "center",
                                            },
                                            children=[
                                                dcc.Dropdown(id="vis-hist-attr", options=[], clearable=False),
                                                dcc.Slider(
                                                    id="vis-hist-bins",
                                                    min=5,
                                                    max=60,
                                                    step=1,
                                                    value=32,
                                                    marks={5: "5", 60: "60"},
                                                    included=False,
                                                ),
                                            ],
                                        ),

                                        html.Div(
                                            id="vis-controls-violin",
                                            style={"display": "none"},
                                            children=[
                                                dcc.Dropdown(id="vis-violin-attr", options=[], clearable=False)
                                            ],
                                        ),

                                        html.Div(
                                            id="vis-controls-radar",
                                            style={"marginTop": "8px"},
                                            children=[
                                                dcc.Dropdown(
                                                    id="vis-radar-attr",
                                                    options=[
                                                        {
                                                            "label": attribute_display_label(
                                                                a,
                                                                include_category=False,
                                                                include_unit=False,
                                                            ),
                                                            "value": a,
                                                        }
                                                        for a in sorted(
                                                            all_numeric_attributes(DATA_INFO),
                                                            key=lambda a: attribute_display_label(a).lower(),
                                                        )
                                                    ],
                                                    value=[],
                                                    multi=True,
                                                    placeholder="Select radar attributes (max 8)",
                                                )
                                            ],
                                        ),

                                        # Plots
                                        _plot_wrap(
                                            children=[
                                                html.Div(
                                                    id="vis-right-wrap-scatter",
                                                    children=dcc.Graph(
                                                        id="vis-scatter-plot",
                                                        config=PLOT_CONFIG,
                                                    ),
                                                ),
                                                html.Div(
                                                    id="vis-right-wrap-hist",
                                                    style={"display": "none"},
                                                    children=dcc.Graph(
                                                        id="vis-filter-plot",
                                                        config=PLOT_CONFIG,
                                                    ),
                                                ),
                                                html.Div(
                                                    id="vis-right-wrap-violin",
                                                    style={"display": "none"},
                                                    children=dcc.Graph(
                                                        id="vis-violin-plot",
                                                        config=PLOT_CONFIG,
                                                    ),
                                                ),
                                                html.Div(
                                                    id="vis-right-wrap-radar",
                                                    children=dcc.Graph(
                                                        id="vis-radar-plot",
                                                        config=PLOT_CONFIG,
                                                    ),
                                                ),
                                                dcc.ConfirmDialog(
                                                    id="radar-max-dims-dialog",
                                                    message="You can select a maximum of 8 attributes for the Radar Plot.",
                                                ),
                                            ]
                                        ),
                                    ],
                                ),
                            ],
                        ),

                        # ── Bottom row: Parallel Coordinates Plot
                        _panel(
                            children=[
                                dcc.ConfirmDialog(
                                    id="pcp-max-dims-dialog",
                                    message="You can select a maximum of 8 attributes for the Parallel Coordinates Plot.",
                                ),
                                html.Div(
                                    style={
                                        "display": "grid",
                                        "gridTemplateColumns": "1fr auto",
                                        "gridTemplateRows": "auto auto",
                                        "columnGap": "16px",
                                        "rowGap": "6px",
                                        "alignItems": "center",
                                    },
                                    children=[
                                        html.Div(
                                            "Parallel Coordinates",
                                            style={"fontSize": "18px", "fontWeight": "900"},
                                        ),
                                        dcc.Dropdown(
                                            id="pcp-attr-dd",
                                            options=[
                                                {
                                                    "label": attribute_display_label(
                                                        a,
                                                        include_category=False,
                                                        include_unit=False,
                                                    ),
                                                    "value": a,
                                                }
                                                for a in sorted(
                                                    all_numeric_attributes(DATA_INFO),
                                                    key=lambda a: attribute_display_label(a).lower(),
                                                )
                                            ],
                                            value=[],
                                            multi=True,
                                            placeholder="Select PCP attributes (max 8)",
                                            style={"minWidth": "520px", "maxWidth": "800px"},
                                        ),
                                        html.Div(
                                            style={
                                                "display": "flex",
                                                "alignItems": "center",
                                                "gap": "18px",
                                                "fontSize": "12px",
                                            },
                                            children=[
                                                dcc.Checklist(
                                                    id="vis-pcp-color-first-axis",
                                                    options=[{"label": "Colour by 1st axis", "value": "on"}],
                                                    value=[],
                                                ),
                                                dcc.Checklist(
                                                    id="vis-pcp-selected-only",
                                                    options=[{"label": "Selected only", "value": "on"}],
                                                    value=[],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                _plot_wrap(
                                    dcc.Graph(id="vis-pcp", config=PLOT_CONFIG)
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),

        # ─────────────────────────────────────────────────────────────
        # Onboarding modal
        # ─────────────────────────────────────────────────────────────
        dbc.Modal(
            id="onboarding-modal",
            is_open=True,
            centered=True,
            size="xl",
            backdrop=True,
            className="onboarding-modal",
            children=[
                dbc.ModalBody(
                    style={
                        "padding": "32px",
                        "background": "linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%)",
                        "borderRadius": "18px",
                    },
                    children=[
                        html.Div(
                            style={"textAlign": "center", "marginBottom": "28px"},
                            children=[
                                html.H1(
                                    "MUN Digital Debate Coach",
                                    style={"fontWeight": "900", "fontSize": "36px"},
                                ),
                                html.P(
                                    [
                                        "Turn country-level indicators into ",
                                        html.Strong("clear, comparable, argument-ready"),
                                        " evidence for MUN debates.",
                                    ],
                                    style={
                                        "fontSize": "16px",
                                        "color": "#475569",
                                        "maxWidth": "720px",
                                        "margin": "0 auto",
                                    },
                                ),
                            ],
                        ),

                        html.Div(
                            style={
                                "display": "grid",
                                "gridTemplateColumns": "repeat(6, 1fr)",
                                "gap": "18px",
                                "marginBottom": "22px",
                            },
                            children=[
                                html.Div(
                                    _onboarding_card(
                                        "Country Profile",
                                        "Quickly understand your country’s global and regional position",
                                        "🌍",
                                    ),
                                    style={"gridColumn": "span 2"},
                                ),
                                html.Div(
                                    _onboarding_card(
                                        "Compare Countries",
                                        "See whether indicators are above or below regional averages",
                                        "📊",
                                    ),
                                    style={"gridColumn": "span 2"},
                                ),
                                html.Div(
                                    _onboarding_card(
                                        "Stress-test Claims",
                                        "Reveal trade-offs and contradictions across indicators",
                                        "⚖️",
                                    ),
                                    style={"gridColumn": "span 2"},
                                ),
                                html.Div(
                                    _onboarding_card(
                                        "Identify Allies",
                                        "Find countries with similar multi-indicator profiles",
                                        "🤝",
                                    ),
                                    style={"gridColumn": "span 3"},
                                ),
                                html.Div(
                                    _onboarding_card(
                                        "Spot Data Weaknesses",
                                        "Detect unusual or inconsistent indicators for rebuttal",
                                        "🔍",
                                    ),
                                    style={"gridColumn": "span 3"},
                                ),
                            ],
                        ),

                        html.Div(
                            style={"margin": "0 auto"},
                            children=[
                                html.Div(
                                    "Select your assigned country",
                                    style={
                                        "fontWeight": "800",
                                        "fontSize": "14px",
                                        "marginBottom": "8px",
                                    },
                                ),
                                dcc.Dropdown(
                                    id="onboarding-country",
                                    options=[
                                        {"label": c, "value": c}
                                        for c in sorted(ALL_COUNTRIES)
                                    ],
                                    clearable=False,
                                    placeholder="Choose your assigned country",
                                ),
                            ],
                        ),

                        html.Div(
                            style={"textAlign": "center", "marginTop": "26px"},
                            children=[
                                dbc.Button(
                                    "Start Exploring",
                                    id="onboarding-confirm",
                                    color="primary",
                                    size="lg",
                                    disabled=True,
                                    style={
                                        "padding": "10px 34px",
                                        "fontWeight": "800",
                                        "fontSize": "16px",
                                        "borderRadius": "10px",
                                    },
                                )
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)
