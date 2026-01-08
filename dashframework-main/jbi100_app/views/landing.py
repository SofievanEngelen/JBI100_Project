# jbi100_app/views/landing.py
from __future__ import annotations

from dash import dcc, html

from jbi100_app.data.category_mapping import UI_CATEGORIES, UI_CATEGORY_LABELS
from jbi100_app.data.data_loader import ALL_COUNTRIES, DATA_INFO


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


def _numeric_attribute_options() -> list[dict]:
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
    cols = sorted(set(cols), key=lambda s: str(s).lower())
    return [{"label": c, "value": c} for c in cols]


ATTR_OPTIONS = _numeric_attribute_options()


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
                                            "Pick your delegation, choose default attributes, and optionally add attributes from categories.",
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

                # ======= 2-column layout: LEFT = (1 + 2), RIGHT = 3 =======
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "minmax(520px, 1.1fr) minmax(520px, 1fr)",
                        "gap": "14px",
                        "alignItems": "start",
                    },
                    children=[
                        # LEFT column: 1 + 2 stacked
                        html.Div(
                            style={"display": "grid", "gridTemplateRows": "auto auto", "gap": "14px"},
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
                                            "2. Choose attributes",
                                            style={"fontSize": "16px", "fontWeight": "900", "color": "#0b1f3b"},
                                        ),
                                        html.Div(
                                            "Select the default attribute pool used on the visualisation page (each plot can still override locally).",
                                            style={"fontSize": "12px", "color": "#6b778c", "marginTop": "6px"},
                                        ),
                                        dcc.Dropdown(
                                            id="all-attrs-dd",
                                            options=ATTR_OPTIONS,
                                            value=[],  # default: empty (user must choose)
                                            multi=True,
                                            placeholder="Select attributes (alphabetical)",
                                            style={"marginTop": "10px"},
                                        ),
                                    ],
                                ),
                            ],
                        ),

                        # RIGHT column: 3
                        _card(
                            children=[
                                html.Div(
                                    "3. Category (optional)",
                                    style={"fontSize": "16px", "fontWeight": "900", "color": "#0b1f3b"},
                                ),
                                html.Div(
                                    "Select one or more categories to preview the union of their attributes. You can add them to your selected attributes with the button.",
                                    style={"fontSize": "12px", "color": "#6b778c", "marginTop": "6px"},
                                ),
                                dcc.Checklist(
                                    id="cat-radio",
                                    options=[{"label": label, "value": key} for key, label in _iter_category_labels()],
                                    value=[],
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
                                html.Div(
                                    id="category-hint",
                                    style={"fontSize": "12px", "color": "#6b778c", "marginTop": "10px"},
                                ),
                                html.Div(
                                    style={"marginTop": "12px"},
                                    children=[
                                        html.Div(
                                            "Category attributes",
                                            style={"fontSize": "12px", "fontWeight": "800", "color": "#243b53"},
                                        ),
                                        html.Div(
                                            id="category-attrs-preview",
                                            style={
                                                "marginTop": "8px",
                                                "border": "1px solid rgba(15, 23, 42, 0.10)",
                                                "borderRadius": "12px",
                                                "padding": "10px 10px",
                                                "background": "#fbfcff",
                                                "maxHeight": "310px",
                                                "overflowY": "auto",
                                            },
                                        ),
                                    ],
                                ),
                                html.Button(
                                    "Add category attributes to selected attributes",
                                    id="cat-add-to-attrs",
                                    n_clicks=0,
                                    style={
                                        "width": "100%",
                                        "marginTop": "12px",
                                        "height": "42px",
                                        "borderRadius": "12px",
                                        "border": "1px solid rgba(43,102,227,0.35)",
                                        "background": "rgba(43,102,227,0.06)",
                                        "color": "#1f4fd8",
                                        "fontWeight": "800",
                                        "cursor": "pointer",
                                    },
                                ),
                            ],
                        ),
                    ],
                ),

                _card(
                    style_extra={
                        "padding": "18px",
                        "marginTop": "12px",
                        "display": "flex",
                        "justifyContent": "center",
                        "alignItems": "center",
                    },
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