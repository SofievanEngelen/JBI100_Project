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
            if isinstance(item, dict):
                k = item.get("value")
                v = item.get("label")
                if k is not None and v is not None:
                    m[k] = v
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                m[item[0]] = item[1]
    return m


def _category_options_list():
    label_map = _label_map()
    return [{"label": label_map.get(k, str(k)), "value": str(k)} for k in UI_CATEGORIES.keys()]


def _metric_options_list_default():
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return []
    cols = [
        c
        for c in DATA_INFO.columns
        if c
        not in (
            "Country",
            "Region",
            "Continent",
            "_CountryKey",
            "_UN_NAME",
            "_PLOTLY_NAME",
        )
    ]
    return [{"label": c, "value": c} for c in cols[:30]]


def _card(children, style_extra=None):
    style = {
        "background": "white",
        "border": "1px solid rgba(0,0,0,0.08)",
        "borderRadius": "16px",
        "boxShadow": "0 10px 24px rgba(16,24,40,0.06)",
        "padding": "14px",
        "boxSizing": "border-box",
    }
    if style_extra:
        style.update(style_extra)
    return html.Div(children=children, style=style)


layout = html.Div(
    style={
        "minHeight": "100vh",
        "overflowX": "hidden",
        "background": "linear-gradient(180deg, #fbfbfd 0%, #f4f6fb 100%)",
        "padding": "18px 22px",
        "boxSizing": "border-box",
    },
    children=[
        # Popup dialog for selection limit
        dcc.ConfirmDialog(
            id="vis-max-selection-dialog",
            message="You cannot select more than 5 countries, please remove one from your selection before adding a new one",
            displayed=False,
        ),

        html.Div(
            style={
                "maxWidth": "1200px",
                "margin": "0 auto",
                "display": "grid",
                "gridTemplateColumns": "360px 1fr",
                "gap": "14px",
                "alignItems": "start",
            },
            children=[
                # =========================
                # LEFT SIDEBAR (controls)
                # =========================
                _card(
                    style_extra={"position": "sticky", "top": "14px"},
                    children=[
                        html.Div(
                            "Delegate Prep Console",
                            style={"fontSize": "16px", "fontWeight": "900", "color": "#0b1f3b"},
                        ),
                        html.Div(
                            id="vis-selected-text",
                            style={"marginTop": "8px", "fontSize": "12px", "color": "#516074"},
                        ),
                        html.Div(style={"height": "12px"}),

                        html.Div(
                            "SELECT GEOGRAPHICAL SCALE",
                            style={"fontSize": "12px", "fontWeight": "900", "color": "#0b1f3b"},
                        ),
                        dcc.RadioItems(
                            id="vis-geo-scale",
                            value="global",
                            options=[
                                {"label": "Global", "value": "global"},
                                {"label": "Continent", "value": "continent"},
                                {"label": "Region", "value": "region"},
                            ],
                            style={"marginTop": "8px"},
                            inputStyle={"marginRight": "8px"},
                        ),

                        html.Div(style={"height": "10px"}),

                        html.Div(
                            "Country (1–5)",
                            style={"fontSize": "12px", "fontWeight": "800", "color": "#0b1f3b"},
                        ),
                        dcc.Dropdown(
                            id="vis-country",
                            multi=True,
                            value=[],
                            options=[],
                            placeholder="Pick 1–5 countries (or click the map)",
                            style={"marginTop": "6px"},
                        ),

                        html.Div(style={"height": "10px"}),

                        html.Div(
                            "Category (optional)",
                            style={"fontSize": "12px", "fontWeight": "800", "color": "#0b1f3b"},
                        ),
                        dcc.Dropdown(
                            id="vis-category",
                            options=_category_options_list(),
                            value=None,
                            clearable=True,
                            placeholder="All categories",
                            style={"marginTop": "6px"},
                        ),

                        html.Div(style={"height": "10px"}),

                        html.Div(
                            "Metric",
                            style={"fontSize": "12px", "fontWeight": "800", "color": "#0b1f3b"},
                        ),
                        dcc.Dropdown(
                            id="vis-metric",
                            clearable=False,
                            value=None,
                            options=_metric_options_list_default(),
                            style={"marginTop": "6px"},
                        ),

                        html.Div(style={"height": "12px"}),

                        html.Div(id="vis-population-text", style={"fontSize": "12px", "color": "#516074"}),
                        html.Div(id="vis-filter-text", style={"marginTop": "10px", "fontSize": "12px", "color": "#516074"}),
                        html.Div(id="vis-warnings", style={"marginTop": "12px", "fontSize": "12px", "color": "#b42318"}),

                        html.Div(style={"height": "12px"}),

                        html.Div(
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "10px"},
                            children=[
                                html.Button(
                                    "Clear selection",
                                    id="vis-clear-selection",
                                    n_clicks=0,
                                    style={
                                        "width": "100%",
                                        "padding": "10px 12px",
                                        "borderRadius": "12px",
                                        "border": "1px solid #d6d9e4",
                                        "background": "white",
                                        "fontWeight": 900,
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "Clear brush",
                                    id="vis-clear-brush",
                                    n_clicks=0,
                                    style={
                                        "width": "100%",
                                        "padding": "10px 12px",
                                        "borderRadius": "12px",
                                        "border": "1px solid #d6d9e4",
                                        "background": "white",
                                        "fontWeight": 900,
                                        "cursor": "pointer",
                                    },
                                ),
                            ],
                        ),

                        # Existing brush store
                        dcc.Store(id="pcp-brush-store", data=None),

                        # Stores list[dict]: [{"country_name": ..., "colour_rgb": ...}, ...]
                        dcc.Store(id="vis-selection-store", data=[]),
                    ],
                ),

                # =========================
                # RIGHT MAIN CONTENT
                # =========================
                html.Div(
                    style={"display": "grid", "gridTemplateRows": "auto auto auto auto auto auto", "gap": "14px"},
                    children=[
                        _card(children=[
                            dcc.Graph(id="vis-map", style={"height": "520px"}, config={"displayModeBar": True})]),
                        _card(children=[
                            dcc.Graph(id="vis-pcp", style={"height": "560px"}, config={"displayModeBar": True})]),
                        _card(children=[dcc.Graph(id="vis-filter-plot", style={"height": "320px"},
                                                  config={"displayModeBar": True})]),  # histogram
                        _card(children=[dcc.Graph(id="vis-violin-plot", style={"height": "320px"},
                                                  config={"displayModeBar": True})]),
                        _card(children=[dcc.Graph(id="vis-scatter-plot", style={"height": "420px"},
                                                  config={"displayModeBar": True})]),
                        _card(children=[dcc.Graph(id="vis-radar-plot", style={"height": "420px"},
                                                  config={"displayModeBar": True})]),
                    ],
                ),
            ],
        )
    ],
)
