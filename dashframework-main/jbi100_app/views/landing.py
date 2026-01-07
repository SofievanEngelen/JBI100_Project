# jbi100_app/views/landing.py
from __future__ import annotations

from dash import dcc, html

from jbi100_app.data.category_mapping import UI_CATEGORY_LABELS
from jbi100_app.data.data_loader import ALL_COUNTRIES


def _title_case_country(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return " ".join([w.capitalize() for w in s.split(" ")])


COUNTRY_OPTIONS = [{"label": _title_case_country(c), "value": c} for c in ALL_COUNTRIES]


def _card(style_extra=None, children=None):
    style = {
        "border": "1px solid rgba(0,0,0,0.08)",
        "borderRadius": "18px",
        "background": "white",
        "boxShadow": "0 10px 30px rgba(0,0,0,0.06)",
        "padding": "18px",
        "boxSizing": "border-box",
    }
    if style_extra:
        style.update(style_extra)
    return html.Div(style=style, children=children)


def _iter_category_labels():
    x = UI_CATEGORY_LABELS

    if isinstance(x, dict):
        for k, v in x.items():
            yield k, v
        return

    if isinstance(x, (list, tuple)):
        for item in x:
            if isinstance(item, dict):
                k = item.get("value")
                v = item.get("label")
                if k is not None and v is not None:
                    yield k, v
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                yield item[0], item[1]
        return


def _default_cat_key():
    for k, _ in _iter_category_labels():
        return k
    return None


layout = html.Div(
    style={
        "minHeight": "100vh",
        "background": "linear-gradient(180deg, #fbfbfd 0%, #f4f6fb 100%)",
        "padding": "18px 22px",
        "boxSizing": "border-box",
    },
    children=[
        html.Div(
            style={"width": "100%", "maxWidth": "1400px", "margin": "0 auto"},
            children=[
                _card(
                    style_extra={"padding": "22px 22px"},
                    children=[
                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"},
                            children=[
                                html.Div(
                                    children=[
                                        html.Div(
                                            "MUN Global Strategist",
                                            style={
                                                "fontSize": "40px",
                                                "fontWeight": "900",
                                                "letterSpacing": "-0.02em",
                                                "color": "#0b1f3b",
                                            },
                                        ),
                                        html.Div(
                                            "Select a delegation and optionally a category. Then explore with linked views.",
                                            style={"marginTop": "6px", "fontSize": "14px", "color": "#516074"},
                                        ),
                                    ]
                                ),
                                html.Div(
                                    style={
                                        "border": "1px solid rgba(0,0,0,0.08)",
                                        "borderRadius": "999px",
                                        "padding": "8px 12px",
                                        "fontSize": "12px",
                                        "color": "#516074",
                                        "background": "#fbfcff",
                                    },
                                    children="Delegate Prep Console",
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(style={"height": "14px"}),

                html.Div(
                    style={"display": "grid", "gridTemplateColumns": "minmax(520px, 1.4fr) minmax(360px, 1fr)", "gap": "14px", "alignItems": "start"},
                    children=[
                        _card(
                            children=[
                                html.Div(
                                    "1. Select your delegation country",
                                    style={"fontSize": "16px", "fontWeight": "900", "color": "#0b1f3b"},
                                ),
                                dcc.Dropdown(
                                    id="country-dd",
                                    options=COUNTRY_OPTIONS,
                                    value=ALL_COUNTRIES[0] if len(ALL_COUNTRIES) > 0 else None,
                                    placeholder="Search country",
                                    searchable=True,
                                    clearable=False,
                                    style={"marginTop": "10px"},
                                ),
                                html.Div(
                                    "Tip: start with your delegation country; you can compare others later via map selection.",
                                    style={"fontSize": "12px", "color": "#6b778c", "marginTop": "8px"},
                                ),
                            ],
                        ),

                        _card(
                            children=[
                                html.Div(
                                    "2. Optional category (you can clear it)",
                                    style={"fontSize": "16px", "fontWeight": "900", "color": "#0b1f3b"},
                                ),
                                html.Div(
                                    "This only influences the default PCP dimensions and available metrics.",
                                    style={"fontSize": "12px", "color": "#6b778c", "marginTop": "6px"},
                                ),
                                dcc.Checklist(
                                    id="cat-radio",
                                    options=[{"label": label, "value": key} for key, label in _iter_category_labels()],
                                    value=[_default_cat_key()] if _default_cat_key() else [],
                                    labelStyle={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "gap": "10px",
                                        "padding": "10px 12px",
                                        "border": "1px solid rgba(0,0,0,0.08)",
                                        "borderRadius": "14px",
                                        "marginTop": "10px",
                                        "cursor": "pointer",
                                        "background": "#ffffff",
                                    },
                                    inputStyle={"transform": "scale(1.05)"},
                                    style={"marginTop": "10px"},
                                ),
                                html.Div(id="category-hint", style={"fontSize": "12px", "color": "#6b778c", "marginTop": "10px"}),
                            ],
                        ),
                    ],
                ),

                _card(
                    style_extra={"padding": "18px", "marginTop": "12px", "display": "flex", "justifyContent": "center", "alignItems": "center"},
                    children=[
                        html.Button(
                            "GET STARTED",
                            id="ob-start",
                            n_clicks=0,
                            style={
                                "display": "inline-flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "height": "56px",
                                "lineHeight": "56px",
                                "padding": "0 44px",
                                "borderRadius": "999px",
                                "border": "none",
                                "background": "linear-gradient(135deg, #2b66e3, #1f4fd8)",
                                "color": "white",
                                "fontSize": "15px",
                                "fontWeight": "900",
                                "letterSpacing": "0.12em",
                                "textTransform": "uppercase",
                                "cursor": "pointer",
                                "minWidth": "420px",
                                "boxShadow": "0 14px 28px rgba(43,102,227,0.25)",
                            },
                        ),
                    ],
                ),
            ],
        )
    ],
)
