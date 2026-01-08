# jbi100_app/views/Visualisation.py
from __future__ import annotations

from dash import html, dcc

from jbi100_app.data.data_loader import DATA_INFO
from jbi100_app.data.category_mapping import UI_CATEGORIES, UI_CATEGORY_LABELS


def _label_map() -> dict:
    if isinstance(UI_CATEGORY_LABELS, dict):
        return UI_CATEGORY_LABELS
    m: dict = {}
    if isinstance(UI_CATEGORY_LABELS, (list, tuple)):
        for item in UI_CATEGORY_LABELS:
            if isinstance(item, dict) and "value" in item and "label" in item:
                m[item["value"]] = item["label"]
    return m


def _numeric_attribute_values() -> list[str]:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return []
    exclude = {"Country", "_CountryKey", "Continent", "Region"}
    cols = []
    for c in list(DATA_INFO.columns):
        if c in exclude:
            continue
        try:
            if DATA_INFO[c].dtype.kind in "if":
                cols.append(c)
        except Exception:
            continue
    return sorted(set(cols), key=lambda s: str(s).lower())


def _card(children, style_extra=None):
    """
    White card used for the sidebar.
    """
    style = {
        "background": "white",
        "borderRadius": "14px",
        "boxShadow": "0 6px 18px rgba(15, 23, 42, 0.08)",
        "border": "1px solid rgba(148, 163, 184, 0.35)",
        "padding": "12px",
        "minHeight": 0,
    }
    if style_extra:
        style.update(style_extra)
    return html.Div(style=style, children=children)


def _panel(children, style_extra=None):
    """
    Grey outer panel (matches your top-right window look).
    Use this for Map, Right panel, and PCP so they feel consistent.
    """
    style = {
        "height": "100%",
        "background": "#ffffff",
        "borderRadius": "18px",
        "padding": "18px 22px",
        "boxSizing": "border-box",
        "display": "flex",
        "flexDirection": "column",
        "gap": "12px",
        "minHeight": 0,
        "border": "1px solid rgba(148, 163, 184, 0.25)",
    }
    if style_extra:
        style.update(style_extra)
    return html.Div(style=style, children=children)


def _plot_wrap(children, style_extra=None):
    """
    White inner plot card inside the grey panel.
    """
    style = {
        "background": "white",
        "borderRadius": "12px",
        "padding": "10px",
        "boxSizing": "border-box",
        "flex": "1",
        "minHeight": 0,
        "border": "1px solid rgba(148, 163, 184, 0.25)",
    }
    if style_extra:
        style.update(style_extra)
    return html.Div(style=style, children=children)


_ALL_ATTRS = _numeric_attribute_values()
_ATTR_OPTIONS = [{"label": a.replace("_", " "), "value": a} for a in _ALL_ATTRS]

_LABELS = _label_map()
_CATEGORY_OPTIONS = [
    {"label": _LABELS.get(k, k), "value": k}
    for k in (UI_CATEGORIES.keys() if isinstance(UI_CATEGORIES, dict) else [])
]

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}


layout = html.Div(
    style={
        "height": "100%",
        "width": "100%",
        "overflow": "hidden",
        "padding": "10px 10px 25px 10px",  # small bottom margin
        "boxSizing": "border-box",
        "background": "#f6f7fb",
    },
    children=[
        html.Div(
            style={
                "height": "100%",
                "display": "grid",
                "gridTemplateColumns": "240px 1fr",
                "gap": "12px",
                "minHeight": 0,
            },
            children=[
                # =========================
                # Sidebar (keep as white card)
                # =========================
                _card(
                    style_extra={
                        # "height": "100%",
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "10px",
                        "padding": "12px 12px 25px 12px",
                    },
                    children=[
                        html.Div(
                            "Visualization Tool",
                            style={"fontSize": "16px", "fontWeight": "900", "color": "#0b1f3b"},
                        ),

                        html.Div(
                            "Select Country (max 5)",
                            style={"fontSize": "11px", "fontWeight": "800", "color": "#243b53"},
                        ),
                        dcc.Dropdown(
                            id="vis-country",
                            options=[],
                            value=[],
                            multi=True,
                            placeholder="Find country",
                        ),

                        html.Div(
                            "Select Scale",
                            style={"fontSize": "11px", "fontWeight": "800", "color": "#243b53"},
                        ),
                        dcc.RadioItems(
                            id="vis-geo-scale",
                            value="global",
                            options=[
                                {"label": "Global", "value": "global"},
                                {"label": "Continent", "value": "continent"},
                                {"label": "Region", "value": "region"},
                            ],
                            style={"marginTop": "4px"},
                            inputStyle={"marginRight": "8px"},
                        ),

                        html.Div(
                            "Category (optional)",
                            style={"fontSize": "11px", "fontWeight": "800", "color": "#243b53"},
                        ),
                        dcc.Dropdown(
                            id="vis-category",
                            options=_CATEGORY_OPTIONS,
                            value=None,
                            clearable=True,
                            placeholder="Limit attribute options",
                        ),

                        html.Div(id="vis-warnings", style={"fontSize": "11px", "color": "#b91c1c"}),

                        html.Button(
                            "Clear selection",
                            id="vis-clear-selection",
                            n_clicks=0,
                            style={"width": "100%"},
                        ),
                        html.Button(
                            "Clear brush",
                            id="vis-clear-brush",
                            n_clicks=0,
                            style={"width": "100%"},
                        ),

                        html.Hr(style={"margin": "8px 0"}),

                        html.Div("Population", style={"fontSize": "11px", "fontWeight": "800", "color": "#243b53"}),
                        html.Div(id="vis-population-text", style={"fontSize": "11px", "color": "#516074"}),

                        html.Div("Selected", style={"fontSize": "11px", "fontWeight": "800", "color": "#243b53"}),
                        html.Div(id="vis-selected-text", style={"fontSize": "11px", "color": "#516074"}),

                        # Stores
                        dcc.Store(id="pcp-brush-store", data=None),
                        dcc.Store(id="vis-selection-store", data=[]),
                    ],
                ),

                # =========================
                # Main area
                # =========================
                html.Div(
                    style={
                        "height": "100%",
                        "display": "grid",
                        "gridTemplateRows": "56% 44%",
                        "gap": "12px",
                        "minHeight": 0,
                    },
                    children=[
                        # ---------- Top row: Map + Right panel ----------
                        html.Div(
                            style={
                                "display": "grid",
                                "gridTemplateColumns": "minmax(0, 1fr) minmax(0, 50%)",
                                "gap": "12px",
                                "minHeight": 0,
                            },
                            children=[
                                # =========================
                                # Map (NOW styled like top-right: grey panel + white plot wrap)
                                # =========================
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
                                                    style={"fontSize": "14px", "fontWeight": "900", "color": "#3a3a3a"},
                                                ),
                                                dcc.Dropdown(
                                                    id="vis-metric",
                                                    options=_ATTR_OPTIONS,
                                                    value=_ALL_ATTRS[0] if _ALL_ATTRS else None,
                                                    clearable=False,
                                                    placeholder="Select Attribute",
                                                    style={"width": "320px"},
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

                                # =========================
                                # Right panel (already matches; keep but via _panel for consistency)
                                # =========================
                                _panel(
                                    style_extra={"maxWidth": "50%"},
                                    children=[
                                        html.Div(
                                            "Select Visualisation",
                                            style={"fontSize": "14px", "fontWeight": "900", "color": "#3a3a3a"},
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
                                        ),

                                        # ===== Scatter controls
                                        html.Div(
                                            id="vis-controls-scatter",
                                            style={
                                                "display": "grid",
                                                "gridTemplateColumns": "1fr 1fr",
                                                "gap": "14px",
                                            },
                                            children=[
                                                dcc.Dropdown(
                                                    id="vis-scatter-x",
                                                    options=[],
                                                    placeholder="Attribute 1",
                                                    clearable=False,
                                                ),
                                                dcc.Dropdown(
                                                    id="vis-scatter-y",
                                                    options=[],
                                                    placeholder="Attribute 2",
                                                    clearable=False,
                                                ),
                                            ],
                                        ),

                                        # ===== Histogram controls
                                        html.Div(
                                            id="vis-controls-hist",
                                            style={
                                                "display": "none",
                                                "gridTemplateColumns": "1fr 1fr",
                                                "gap": "18px",
                                                "alignItems": "center",
                                            },
                                            children=[
                                                dcc.Dropdown(
                                                    id="vis-hist-attr",
                                                    options=[],
                                                    placeholder="Attribute",
                                                    clearable=False,
                                                ),
                                                html.Div(
                                                    children=[
                                                        dcc.Slider(
                                                            id="vis-hist-bins",
                                                            min=5,
                                                            max=60,
                                                            step=1,
                                                            value=30,
                                                            tooltip={"placement": "bottom"},
                                                        ),
                                                        html.Div(
                                                            "Bin size",
                                                            style={"textAlign": "center", "fontSize": "14px", "fontWeight": "700"},
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        ),

                                        # ===== Violin controls
                                        html.Div(
                                            id="vis-controls-violin",
                                            style={"display": "none"},
                                            children=[
                                                dcc.Dropdown(
                                                    id="vis-violin-attr",
                                                    options=[],
                                                    placeholder="Attribute",
                                                    clearable=False,
                                                )
                                            ],
                                        ),

                                        # ===== Radar controls (none)
                                        html.Div(id="vis-controls-radar", style={"display": "none"}),

                                        # white plot wrap
                                        _plot_wrap(
                                            children=[
                                                html.Div(
                                                    id="vis-right-wrap-scatter",
                                                    style={"height": "100%", "minHeight": 0},
                                                    children=dcc.Graph(
                                                        id="vis-scatter-plot",
                                                        config=PLOT_CONFIG,
                                                        style={"height": "100%", "width": "100%"},
                                                    ),
                                                ),
                                                html.Div(
                                                    id="vis-right-wrap-hist",
                                                    style={"height": "100%", "minHeight": 0, "display": "none"},
                                                    children=dcc.Graph(
                                                        id="vis-filter-plot",
                                                        config=PLOT_CONFIG,
                                                        style={"height": "100%", "width": "100%"},
                                                    ),
                                                ),
                                                html.Div(
                                                    id="vis-right-wrap-violin",
                                                    style={"height": "100%", "minHeight": 0, "display": "none"},
                                                    children=dcc.Graph(
                                                        id="vis-violin-plot",
                                                        config=PLOT_CONFIG,
                                                        style={"height": "100%", "width": "100%"},
                                                    ),
                                                ),
                                                html.Div(
                                                    id="vis-right-wrap-radar",
                                                    style={"height": "100%", "minHeight": 0, "display": "none"},
                                                    children=dcc.Graph(
                                                        id="vis-radar-plot",
                                                        config=PLOT_CONFIG,
                                                        style={"height": "100%", "width": "100%"},
                                                    ),
                                                ),
                                            ],
                                        ),

                                        html.Div(id="vis-filter-text", style={"fontSize": "12px", "color": "#6b7280"}),
                                    ],
                                ),
                            ],
                        ),

                        # ---------- Bottom row: PCP (NOW styled like top-right: grey panel + white plot wrap) ----------
                        _panel(
                            children=[
                                html.Div(
                                    "Parallel Coordinates",
                                    style={"fontSize": "14px", "fontWeight": "900", "color": "#3a3a3a"},
                                ),
                                _plot_wrap(
                                    dcc.Graph(
                                        id="vis-pcp",
                                        config=PLOT_CONFIG,
                                        style={"height": "100%", "width": "100%"},
                                    )
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
    ],
)
