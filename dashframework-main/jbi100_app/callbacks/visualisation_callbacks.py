# jbi100_app/callbacks/visualisation_callbacks.py
from __future__ import annotations

import random

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, State, callback, html, no_update

from jbi100_app.data.data_loader import DATA_INFO, ALL_COUNTRIES, UN_COUNTRIES
from jbi100_app.data.category_mapping import UI_CATEGORIES

# ============================================================
# Styling
# ============================================================
COLOR_SCALE = px.colors.sequential.YlOrRd

MAX_SELECTED_COUNTRIES = 6

SELECTION_COLOR_POOL = [
    "rgb(180,35,24)",    # red
    "rgb(43,102,227)",   # blue
    "rgb(34,139,34)",    # green
    "rgb(255,140,0)",    # orange
    "rgb(128,0,128)",    # purple
    "rgb(0,139,139)",    # teal
    "rgb(220,20,60)",    # crimson
    "rgb(105,105,105)",  # dim gray
]

# Out-of-scope greying (region/continent)
OUT_SCOPE_POINT = "rgba(130,130,130,0.20)"  # scatter points
IN_SCOPE_POINT = "rgba(40,55,70,0.25)"      # scatter points

PCP_IN_SCOPE = "rgba(90,90,90,0.35)"        # PCP non-selected, in-scope
PCP_OUT_SCOPE = "rgba(160,160,160,0.10)"    # PCP non-selected, out-of-scope

MAP_BRUSH_OUTLINE_COLOR = "rgba(43,102,227,0.90)"

HIST_IN_SCOPE_RGBA = "rgba(40,55,70,0.20)"
HIST_OUT_SCOPE_RGBA = "rgba(130,130,130,0.18)"
HIST_BRUSH_RGBA = "rgba(43,102,227,0.30)"

KDE_IN_SCOPE_RGBA = "rgba(40,55,70,0.85)"
KDE_BRUSH_RGBA = "rgba(43,102,227,0.90)"

# microstate dot threshold (selected countries only)
SMALL_COUNTRY_AREA_KM2 = 50_000  # tweak as desired

_META_COLS = {"Country", "Region", "Continent", "_UN_NAME", "_PLOTLY_NAME", "_ISO3"}


# ============================================================
# Helpers: naming + plotly country mapping
# ============================================================
def _canon_un_name(x: str) -> str:
    if x is None:
        return ""
    s = str(x).strip().upper()
    s = " ".join(s.split())
    return s


_UN_TO_PLOTLY_FIX = {
    "UNITED STATES": "United States",
    "UNITED KINGDOM": "United Kingdom",
    "COTE D'IVOIRE": "Côte d'Ivoire",
    "CONGO, REPUBLIC OF THE": "Congo",
    "CONGO, DEMOCRATIC REPUBLIC OF THE": "Democratic Republic of the Congo",
    "KOREA, SOUTH": "South Korea",
    "KOREA, NORTH": "North Korea",
    "BAHAMAS, THE": "The Bahamas",
    "GAMBIA, THE": "The Gambia",
    "MICRONESIA, FEDERATED STATES OF": "Micronesia",
    "TURKEY (TURKIYE)": "Turkey",
    "BURMA": "Myanmar",
    "NORTH MACEDONIA": "North Macedonia",
    "CABO VERDE": "Cape Verde",
    "TIMOR-LESTE": "Timor-Leste",
    "SAO TOME AND PRINCIPE": "Sao Tome and Principe",
}

_SMALL_WORDS = {"of", "the", "and", "to", "in", "on", "for"}


def _smart_title(s: str) -> str:
    parts = s.lower().split()
    out = []
    for i, w in enumerate(parts):
        if i > 0 and w in _SMALL_WORDS:
            out.append(w)
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)


def _un_to_plotly_name(un_name: str) -> str:
    un = _canon_un_name(un_name)
    if not un:
        return ""
    if un in _UN_TO_PLOTLY_FIX:
        return _UN_TO_PLOTLY_FIX[un]
    if "(" in un:
        un = un.split("(", 1)[0].strip()
    if "," in un:
        left, right = [p.strip() for p in un.split(",", 1)]
        un = f"{right} {left}".strip()
    return _smart_title(un)


# ============================================================
# ISO-3 overrides for microstates (reliable Scattergeo placement)
# ============================================================
ISO3_OVERRIDES = {
    # Canonical/UN-ish names (upper) -> ISO3
    "ANDORRA": "AND",
    "ANTIGUA AND BARBUDA": "ATG",
    "BARBADOS": "BRB",

    # extra common tiny states (optional but helps)
    "LIECHTENSTEIN": "LIE",
    "SAN MARINO": "SMR",
    "MONACO": "MCO",
    "MALTA": "MLT",
    "SINGAPORE": "SGP",
    "SEYCHELLES": "SYC",
    "DOMINICA": "DMA",
    "SAINT KITTS AND NEVIS": "KNA",
    "SAINT LUCIA": "LCA",
    "SAINT VINCENT AND THE GRENADINES": "VCT",
    "GRENADA": "GRD",
    "MARSHALL ISLANDS": "MHL",
    "NAURU": "NRU",
    "PALAU": "PLW",
    "TUVALU": "TUV",
}


def _to_iso3(country_name: str) -> str | None:
    if not country_name:
        return None
    key = _canon_un_name(country_name)
    return ISO3_OVERRIDES.get(key)


def _safe_df() -> pd.DataFrame:
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=["Country", "Region", "Continent"])
    df = DATA_INFO.copy()
    for c in ("Country", "Region", "Continent"):
        if c not in df.columns:
            df[c] = "Unknown"
    df["Country"] = df["Country"].astype(str)

    df["_UN_NAME"] = df["Country"].map(_canon_un_name)
    df = df[df["_UN_NAME"].isin(UN_COUNTRIES)].copy()

    df["_PLOTLY_NAME"] = df["Country"].map(_un_to_plotly_name)
    df["_ISO3"] = df["Country"].map(_to_iso3)

    return df


def _as_list_of_str(x) -> list[str]:
    if x is None:
        return []
    if isinstance(x, str):
        return [x]
    if isinstance(x, (list, tuple)):
        return [str(v) for v in x if v is not None]
    return [str(x)]


def _pretty_metric(name: str) -> str:
    return str(name).replace("_", " ")


def _all_numeric_metrics(df: pd.DataFrame) -> list[str]:
    cols = []
    for c in df.columns:
        if c in _META_COLS:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            cols.append(c)
    return cols


def _metric_cols_for_category(df: pd.DataFrame, ui_category: str | None) -> list[str]:
    all_cols = _all_numeric_metrics(df)
    if not ui_category:
        return all_cols
    allowed = UI_CATEGORIES.get(ui_category, [])
    return [c for c in allowed if c in all_cols]


def _coerce_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _pick_pcp_dims(df: pd.DataFrame, ui_category: str | None, max_dims: int = 8) -> list[str]:
    cols = _metric_cols_for_category(df, ui_category)
    if len(cols) < 2:
        cols = _all_numeric_metrics(df)
    return [c for c in cols if c in df.columns][:max_dims]


def _to_country_from_click(click_data) -> str | None:
    if not click_data or not isinstance(click_data, dict):
        return None
    pts = click_data.get("points", [])
    if not pts:
        return None
    cd = pts[0].get("customdata")
    if isinstance(cd, (list, tuple)) and len(cd) >= 1 and cd[0]:
        return str(cd[0])
    ht = pts[0].get("hovertext")
    if ht:
        return str(ht)
    txt = pts[0].get("text")
    if txt:
        return str(txt)
    return None


def _clamp_selection(sel: list[str], limit: int = MAX_SELECTED_COUNTRIES) -> list[str]:
    out = []
    for c in sel:
        c = str(c)
        if c and c not in out:
            out.append(c)
        if len(out) >= limit:
            break
    return out


def _extract_brush_countries(parcoords_selected, work_df: pd.DataFrame) -> list[str]:
    if not isinstance(parcoords_selected, dict):
        return []
    pts = parcoords_selected.get("points", [])
    if not pts:
        return []
    idxs = []
    for p in pts:
        pn = p.get("pointNumber")
        if isinstance(pn, int):
            idxs.append(pn)
    if not idxs:
        return []
    idxs = [i for i in idxs if 0 <= i < len(work_df)]
    return [str(work_df.iloc[i]["Country"]) for i in idxs]


def _kde_counts(x: np.ndarray, grid: np.ndarray, bin_width: float, bw: float | None = None) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = int(x.size)
    if n < 2:
        return np.zeros_like(grid, dtype=float)

    if bw is None:
        std = float(np.std(x, ddof=1)) if n > 1 else 0.0
        bw = 1.06 * std * (n ** (-1 / 5)) if std > 0 else 1.0

    bw = float(bw)
    if not np.isfinite(bw) or bw <= 0:
        bw = 1.0

    diffs = (grid[:, None] - x[None, :]) / bw
    kern = np.exp(-0.5 * diffs * diffs) / (np.sqrt(2 * np.pi) * bw)
    pdf = np.mean(kern, axis=1)
    return pdf * n * float(bin_width)


def _prepare_hist_bins(x: np.ndarray, bins: int = 30) -> tuple[np.ndarray, float, float, float]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return np.linspace(0.0, 1.0, 50), 0.02, 0.0, 1.0

    lo = float(np.min(x))
    hi = float(np.max(x))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        lo = float(np.median(x))
        hi = lo + 1.0

    pad = 0.02 * (hi - lo)
    lo2 = lo - pad
    hi2 = hi + pad
    edges = np.linspace(lo2, hi2, bins + 1)
    bin_width = float(edges[1] - edges[0])
    grid = np.linspace(lo2, hi2, 240)
    return grid, bin_width, lo2, hi2


def _geo_mask(df: pd.DataFrame, geo_scale: str, focus_country: str | None) -> pd.Series:
    if df is None or df.empty:
        return pd.Series([], dtype=bool)

    geo_scale = (geo_scale or "global").lower().strip()
    if geo_scale not in ("continent", "region"):
        return pd.Series([True] * len(df), index=df.index)

    if not focus_country or "Country" not in df.columns:
        return pd.Series([True] * len(df), index=df.index)

    row = df.loc[df["Country"] == focus_country]
    if row.empty:
        return pd.Series([True] * len(df), index=df.index)

    if geo_scale == "continent":
        key = row.iloc[0].get("Continent")
        if key is None:
            return pd.Series([True] * len(df), index=df.index)
        return df["Continent"] == key

    key = row.iloc[0].get("Region")
    if key is None:
        return pd.Series([True] * len(df), index=df.index)
    return df["Region"] == key


# ============================================================
# Country dropdown label with coloured dot
# ============================================================
def _country_option_label(name: str, color: str | None):
    dot = html.Span(
        style={
            "width": "10px",
            "height": "10px",
            "borderRadius": "50%",
            "background": color or "rgba(148,163,184,0.9)",
            "display": "inline-block",
            "flex": "0 0 auto",
        }
    )
    return html.Span(
        [dot, html.Span(str(name).upper(), style={"fontWeight": 800, "letterSpacing": "0.02em"})],
        style={"display": "inline-flex", "alignItems": "center", "gap": "6px"},
    )


# ============================================================
# Selection store (stable colours)
# ============================================================
def _normalize_selection_store(sel_store) -> list[dict]:
    if not isinstance(sel_store, list):
        return []

    seen_names = set()
    seen_colors = set()
    out: list[dict] = []

    for item in sel_store:
        if not isinstance(item, dict):
            continue
        n = item.get("country_name")
        c = item.get("colour_rgb")
        if not n or not c:
            continue
        n = str(n)
        c = str(c)

        if n in seen_names:
            continue
        if c in seen_colors:
            continue

        seen_names.add(n)
        seen_colors.add(c)
        out.append({"country_name": n, "colour_rgb": c})

        if len(out) >= MAX_SELECTED_COUNTRIES:
            break

    return out


def _names_from_store(sel_store) -> list[str]:
    if not isinstance(sel_store, list):
        return []
    return _clamp_selection(
        [str(x.get("country_name")) for x in sel_store if isinstance(x, dict) and x.get("country_name")],
        limit=MAX_SELECTED_COUNTRIES,
    )


def _merge_selection_store(prev_store, desired_names: list[str]) -> tuple[list[dict], bool]:
    prev_store = _normalize_selection_store(prev_store)
    desired_names = _clamp_selection(desired_names, limit=MAX_SELECTED_COUNTRIES)

    prev_map = {d["country_name"]: d["colour_rgb"] for d in prev_store}

    new_store: list[dict] = []
    used_colors: set[str] = set()

    # keep existing colours
    for name in desired_names:
        if name in prev_map:
            col = prev_map[name]
            if col in used_colors:
                continue
            new_store.append({"country_name": name, "colour_rgb": col})
            used_colors.add(col)

    # assign new colours
    for name in desired_names:
        if name in prev_map:
            continue
        free = [c for c in SELECTION_COLOR_POOL if c not in used_colors]
        if not free:
            return prev_store, False
        col = random.choice(free)
        new_store.append({"country_name": name, "colour_rgb": col})
        used_colors.add(col)

    return new_store, True


# ============================================================
# Toggle right plots
# ============================================================
@callback(
    Output("vis-right-wrap-scatter", "style"),
    Output("vis-right-wrap-hist", "style"),
    Output("vis-right-wrap-violin", "style"),
    Output("vis-right-wrap-radar", "style"),

    Output("vis-controls-scatter", "style"),
    Output("vis-controls-hist", "style"),
    Output("vis-controls-violin", "style"),
    Output("vis-controls-radar", "style"),

    Input("vis-right-viz", "value"),
)
def toggle_right_panel(viz_key):
    plot_show = {"display": "block", "height": "100%", "minHeight": 0}
    plot_hide = {"display": "none", "height": "100%", "minHeight": 0}

    ctrl_scatter = {"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px"}
    ctrl_hist = {"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "18px", "alignItems": "center"}
    ctrl_one = {"display": "block"}
    ctrl_none = {"display": "none"}

    viz_key = (viz_key or "scatter").lower().strip()

    if viz_key == "hist":
        return plot_hide, plot_show, plot_hide, plot_hide, ctrl_none, ctrl_hist, ctrl_none, ctrl_none

    if viz_key == "violin":
        return plot_hide, plot_hide, plot_show, plot_hide, ctrl_none, ctrl_none, ctrl_one, ctrl_none

    if viz_key == "radar":
        return plot_hide, plot_hide, plot_hide, plot_show, ctrl_none, ctrl_none, ctrl_none, ctrl_none

    # scatter (default)
    return plot_show, plot_hide, plot_hide, plot_hide, ctrl_scatter, ctrl_none, ctrl_none, ctrl_none



# ============================================================
# Init/update country dropdown + stable colours
# ============================================================
@callback(
    Output("vis-country", "value"),
    Output("vis-country", "options"),
    Output("vis-warnings", "children"),
    Output("vis-selection-store", "data"),
    Input("vis-country", "value"),
    State("vis-selection-store", "data"),
    prevent_initial_call=False,
)
def init_or_update_country_dropdown(vis_country_value, cur_sel_store):
    df = _safe_df()

    countries_all = (
        ALL_COUNTRIES
        if (ALL_COUNTRIES is not None and len(ALL_COUNTRIES) > 0)
        else (sorted(df["Country"].dropna().astype(str).unique().tolist()) if "Country" in df.columns else [])
    )

    cur_sel_store = _normalize_selection_store(cur_sel_store)

    new_names = _clamp_selection(_as_list_of_str(vis_country_value), limit=MAX_SELECTED_COUNTRIES)
    merged, ok = _merge_selection_store(cur_sel_store, new_names)
    if not ok:
        merged = cur_sel_store

    color_map = {d["country_name"]: d["colour_rgb"] for d in merged}
    opts = [{"value": str(c), "label": _country_option_label(str(c), color_map.get(str(c)))} for c in countries_all]

    warn = ""
    if df.empty:
        warn = "Dataset is empty after UN filter. Check mun_dataset.csv loading and Country names."

    return _names_from_store(merged), opts, warn, merged


# ============================================================
# Clear selection / brush
# ============================================================
@callback(
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-selection-store", "data", allow_duplicate=True),
    Input("vis-clear-selection", "n_clicks"),
    prevent_initial_call=True,
)
def clear_selection(n):
    if n and n > 0:
        return [], []
    return no_update, no_update


@callback(
    Output("pcp-brush-store", "data", allow_duplicate=True),
    Input("vis-clear-brush", "n_clicks"),
    prevent_initial_call=True,
)
def clear_brush(n):
    if n and n > 0:
        return None
    return no_update


# ============================================================
# Scatter attribute dropdown options (based on category)
# ============================================================
@callback(
    Output("vis-scatter-x", "options"),
    Output("vis-scatter-y", "options"),
    Output("vis-scatter-x", "value"),
    Output("vis-scatter-y", "value"),
    Input("vis-category", "value"),
    State("vis-scatter-x", "value"),
    State("vis-scatter-y", "value"),
)
def refresh_scatter_attr_options(ui_category, cur_x, cur_y):
    df = _safe_df()
    cols = _metric_cols_for_category(df, ui_category)
    if len(cols) < 2:
        cols = _all_numeric_metrics(df)

    opts = [{"label": _pretty_metric(c), "value": c} for c in cols]

    if not cols:
        return [], [], None, None

    if cur_x not in cols:
        cur_x = cols[0]
    if cur_y not in cols or cur_y == cur_x:
        cur_y = cols[1] if len(cols) > 1 else cols[0]

    return opts, opts, cur_x, cur_y


@callback(
    Output("vis-hist-attr", "options"),
    Output("vis-hist-attr", "value"),
    Output("vis-violin-attr", "options"),
    Output("vis-violin-attr", "value"),
    Input("vis-category", "value"),
    State("vis-hist-attr", "value"),
    State("vis-violin-attr", "value"),
)
def refresh_single_attr_options(ui_category, cur_hist, cur_violin):
    df = _safe_df()
    cols = _metric_cols_for_category(df, ui_category)
    if not cols:
        cols = _all_numeric_metrics(df)

    opts = [{"label": _pretty_metric(c), "value": c} for c in cols]
    if not cols:
        return [], None, [], None

    if cur_hist not in cols:
        cur_hist = cols[0]
    if cur_violin not in cols:
        cur_violin = cols[0]

    return opts, cur_hist, opts, cur_violin


# ============================================================
# Map click -> selection toggle
# ============================================================
@callback(
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-selection-store", "data", allow_duplicate=True),
    Input("vis-map", "clickData"),
    State("vis-selection-store", "data"),
    prevent_initial_call=True,
)
def map_click_to_selection(clickData, current_sel_store):
    current_sel_store = _normalize_selection_store(current_sel_store)
    selected_names = _names_from_store(current_sel_store)

    country = _to_country_from_click(clickData)
    if not country:
        return no_update, no_update

    if country in selected_names:
        new_names = [c for c in selected_names if c != country]
        merged, ok = _merge_selection_store(current_sel_store, new_names)
        return (_names_from_store(merged), merged) if ok else (selected_names, current_sel_store)

    if len(selected_names) >= MAX_SELECTED_COUNTRIES:
        return no_update, no_update

    new_names = [country] + selected_names
    new_names = _clamp_selection(new_names, limit=MAX_SELECTED_COUNTRIES)

    merged, ok = _merge_selection_store(current_sel_store, new_names)
    return (_names_from_store(merged), merged) if ok else (no_update, no_update)


# ============================================================
# PCP
# ============================================================
@callback(
    Output("vis-pcp", "figure"),
    Output("vis-population-text", "children"),
    Output("pcp-brush-store", "data"),
    Input("vis-category", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
    Input("vis-pcp", "selectedData"),
    State("pcp-brush-store", "data"),
)
def update_pcp(ui_category, geo_scale, selection_store, selected_data, prev_brush):
    df_global = _safe_df()

    selection_store = _normalize_selection_store(selection_store)
    selected_names = _names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    pop_df = df_global.copy()
    dims = _pick_pcp_dims(df_global, ui_category, max_dims=8)

    if pop_df.empty or len(dims) < 2:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0))
        return fig, "Population: (none)", None

    in_mask = _geo_mask(pop_df, geo_scale or "global", focus).loc[pop_df.index]

    work = pop_df[["Country"] + dims].copy()
    for c in dims:
        work[c] = _coerce_numeric(work[c])
        med = work[c].median(skipna=True)
        work[c] = work[c].fillna(med)
        mn, mx = float(work[c].min()), float(work[c].max())
        if np.isfinite(mn) and np.isfinite(mx) and mx > mn:
            work[c] = (work[c] - mn) / (mx - mn)
        else:
            work[c] = 0.0

    k = len(selected_names)
    name_to_sel_code = {name: 2 + i for i, name in enumerate(selected_names)}
    codes = np.zeros(len(work), dtype=int)

    in_mask_arr = in_mask.to_numpy(dtype=bool)
    codes[in_mask_arr] = 1
    for i, cname in enumerate(work["Country"].astype(str).tolist()):
        if cname in name_to_sel_code:
            codes[i] = name_to_sel_code[cname]

    cmax = max(2, 2 + k)
    colorscale = [
        [0.0, PCP_OUT_SCOPE],
        [1.0 / cmax - 1e-6, PCP_OUT_SCOPE],
        [1.0 / cmax, PCP_IN_SCOPE],
        [2.0 / cmax - 1e-6, PCP_IN_SCOPE],
    ]

    sel_color_map = {d["country_name"]: d["colour_rgb"] for d in selection_store}
    for i, name in enumerate(selected_names):
        code = 2 + i
        left = code / cmax
        right = min(0.999999, (code + 1e-6) / cmax)
        col = sel_color_map.get(name, "rgb(180,35,24)")
        colorscale.append([left, col])
        colorscale.append([right, col])

    dimensions = [{"label": _pretty_metric(c), "values": work[c].to_numpy()} for c in dims]

    fig = go.Figure(
        data=[
            go.Parcoords(
                line=dict(color=codes, colorscale=colorscale, cmin=0, cmax=cmax, showscale=False),
                dimensions=dimensions,
                labelfont=dict(size=11),
                tickfont=dict(size=10),
            )
        ]
    )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        showlegend=False,
    )

    pop_text = (
        "Population: global"
        if (geo_scale or "global") == "global"
        else f"Population: {geo_scale} (focus={focus or 'none'})"
    )

    brush_out = prev_brush if prev_brush is not None else None
    brushed = _extract_brush_countries(selected_data, work)
    if brushed:
        brush_out = {"countries": brushed}

    return fig, pop_text, brush_out


# ============================================================
# Map: continent/region => out-of-scope white, in-scope coloured
#      selected microstates => dot (ISO-3 when available)
# ============================================================
@callback(
    Output("vis-map", "figure"),
    Output("vis-selected-text", "children"),
    Input("vis-metric", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
)
def update_map(metric, geo_scale, selection_store, brush_data):
    df_global = _safe_df()

    selection_store = _normalize_selection_store(selection_store)
    selected_names = _names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    pop_df = df_global.copy()
    if pop_df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig, "Selected: (none)"

    brush = []
    if isinstance(brush_data, dict) and brush_data.get("countries"):
        brush = [str(x) for x in brush_data.get("countries", []) if x]

    if selected_names and brush:
        msg = f"Selected: {', '.join(selected_names)} | Brush: {len(brush)} countries"
    elif selected_names:
        msg = f"Selected: {', '.join(selected_names)}"
    elif brush:
        msg = f"Selected: (none) | Brush: {len(brush)} countries"
    else:
        msg = "Selected: (none)"

    if not metric or metric not in pop_df.columns:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig, msg

    plot_df = pop_df.copy()
    plot_df["_z"] = _coerce_numeric(plot_df[metric])

    geo_scale = (geo_scale or "global").lower().strip()
    scope_active = geo_scale in ("continent", "region") and focus is not None

    fig = go.Figure()

    if scope_active:
        in_mask = _geo_mask(plot_df, geo_scale, focus)
        in_df = plot_df.loc[in_mask].copy()
        out_df = plot_df.loc[~in_mask].copy()

        if not out_df.empty:
            fig.add_trace(
                go.Choropleth(
                    locations=out_df["_PLOTLY_NAME"],
                    locationmode="country names",
                    z=[1.0] * len(out_df),
                    text=out_df["Country"],
                    customdata=np.stack([out_df["Country"]], axis=-1),
                    colorscale=[[0, "rgba(255,255,255,1)"], [1, "rgba(255,255,255,1)"]],
                    showscale=False,
                    marker_line_color="rgba(200,200,200,0.55)",
                    marker_line_width=0.6,
                    hoverinfo="skip",
                    colorbar=dict(
                        title=None,  # your screenshot has no colorbar title
                        orientation="h",
                        x=0.5,
                        xanchor="center",
                        y=1.08,  # pushes it above the map
                        yanchor="top",
                        len=1.0,  # full width
                        thickness=18,
                        tickfont=dict(size=14),
                    ),
                )
            )

        fig.add_trace(
            go.Choropleth(
                locations=in_df["_PLOTLY_NAME"],
                locationmode="country names",
                z=in_df["_z"],
                text=in_df["Country"],
                customdata=np.stack([in_df["Country"]], axis=-1),
                colorscale=COLOR_SCALE,
                marker_line_color="rgba(255,255,255,0.35)",
                marker_line_width=0.5,
                hovertemplate="<b>%{text}</b><br>" + _pretty_metric(metric) + ": %{z}<extra></extra>",
            )
        )
    else:
        fig.add_trace(
            go.Choropleth(
                locations=plot_df["_PLOTLY_NAME"],
                locationmode="country names",
                z=plot_df["_z"],
                text=plot_df["Country"],
                customdata=np.stack([plot_df["Country"]], axis=-1),
                colorscale=COLOR_SCALE,
                colorbar=dict(
                    title=None,  # your screenshot has no colorbar title
                    orientation="h",
                    x=0.5,
                    xanchor="center",
                    y=1.08,  # pushes it above the map
                    yanchor="top",
                    len=1.0,  # full width
                    thickness=18,
                    tickfont=dict(size=14),
                ),
                marker_line_color="rgba(255,255,255,0.35)",
                marker_line_width=0.5,
                hovertemplate="<b>%{text}</b><br>" + _pretty_metric(metric) + ": %{z}<extra></extra>",
            )
        )

    # brush outline
    if brush:
        brush_df = plot_df[plot_df["Country"].isin(brush)].copy()
        if not brush_df.empty:
            fig.add_trace(
                go.Choropleth(
                    locations=brush_df["_PLOTLY_NAME"],
                    locationmode="country names",
                    z=[1.0] * len(brush_df),
                    text=brush_df["Country"],
                    customdata=np.stack([brush_df["Country"]], axis=-1),
                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                    showscale=False,
                    marker_line_color=MAP_BRUSH_OUTLINE_COLOR,
                    marker_line_width=1.5,
                    hoverinfo="skip",
                )
            )

    # selected: big -> border, tiny -> dot
    for item in selection_store:
        cname = item.get("country_name")
        ccol = item.get("colour_rgb") or "rgb(180,35,24)"
        if not cname:
            continue

        row = plot_df.loc[plot_df["Country"] == cname]
        if row.empty:
            continue

        plotly_name = row.iloc[0].get("_PLOTLY_NAME")
        iso3 = row.iloc[0].get("_ISO3")
        area = pd.to_numeric(row.iloc[0].get("land_area_km2"), errors="coerce")

        is_small = bool(np.isfinite(area) and float(area) < float(SMALL_COUNTRY_AREA_KM2))

        if is_small:
            # Prefer ISO-3 for microstates (much more reliable)
            if isinstance(iso3, str) and iso3.strip():
                fig.add_trace(
                    go.Scattergeo(
                        locations=[iso3],
                        locationmode="ISO-3",
                        mode="markers",
                        marker=dict(size=12, color=ccol, line=dict(width=1.5, color="white")),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
            elif isinstance(plotly_name, str) and plotly_name.strip():
                fig.add_trace(
                    go.Scattergeo(
                        locations=[plotly_name],
                        locationmode="country names",
                        mode="markers",
                        marker=dict(size=12, color=ccol, line=dict(width=1.5, color="white")),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
            continue

        # large country: border outline
        if isinstance(plotly_name, str) and plotly_name.strip():
            fig.add_trace(
                go.Choropleth(
                    locations=[plotly_name],
                    locationmode="country names",
                    z=[1.0],
                    text=[cname],
                    customdata=[[cname]],
                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                    showscale=False,
                    marker_line_color=ccol,
                    marker_line_width=2.8,
                    hoverinfo="skip",
                )
            )

    # remove internal whitespace (make geo fill the whole panel)
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        geo=dict(
            domain=dict(x=[0, 1], y=[0, 0.88]),  # leave top strip for horizontal colorbar
            showframe=False,
            showcoastlines=False,
            projection_type="natural earth",
        ),
    )

    return fig, msg


# ============================================================
# Histogram
# ============================================================
# ============================================================
# Histogram
# ============================================================
@callback(
    Output("vis-filter-plot", "figure"),
    Output("vis-filter-text", "children"),
    Input("vis-hist-attr", "value"),
    Input("vis-hist-bins", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
)
def update_distribution(hist_attr, bins, geo_scale, selection_store, brush_data):
    df_global = _safe_df()

    selection_store = _normalize_selection_store(selection_store)
    selected_names = _names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    pop_df = df_global.copy()
    fig = go.Figure()

    metric = hist_attr
    nbins = int(bins or 30)

    if pop_df.empty or not metric or metric not in pop_df.columns:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig, ""

    in_mask = _geo_mask(pop_df, geo_scale or "global", focus)
    in_df = pop_df.loc[in_mask].copy()
    out_df = pop_df.loc[~in_mask].copy()

    in_vals = _coerce_numeric(in_df[metric]).to_numpy(dtype=float)
    in_vals = in_vals[np.isfinite(in_vals)]
    if in_vals.size == 0:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig, ""

    out_vals = _coerce_numeric(out_df[metric]).to_numpy(dtype=float)
    out_vals = out_vals[np.isfinite(out_vals)]

    brush = []
    if isinstance(brush_data, dict) and brush_data.get("countries"):
        brush = [str(x) for x in brush_data.get("countries", []) if x]

    brush_vals = np.array([], dtype=float)
    if brush:
        brush_df = pop_df[pop_df["Country"].isin(brush)].copy()
        brush_vals = _coerce_numeric(brush_df[metric]).to_numpy(dtype=float)
        brush_vals = brush_vals[np.isfinite(brush_vals)]

    # build a bin range that covers everything we might draw
    all_for_bins = in_vals
    if out_vals.size > 0:
        all_for_bins = np.concatenate([all_for_bins, out_vals])
    if brush_vals.size > 0:
        all_for_bins = np.concatenate([all_for_bins, brush_vals])

    grid, bin_width, x_min, x_max = _prepare_hist_bins(all_for_bins, bins=nbins)

    scope_active = (geo_scale or "global") in ("continent", "region") and focus

    # out-of-scope (grey)
    if scope_active and out_vals.size > 0:
        fig.add_trace(
            go.Histogram(
                x=out_vals,
                nbinsx=nbins,
                marker=dict(color=HIST_OUT_SCOPE_RGBA),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # in-scope (dark)
    fig.add_trace(
        go.Histogram(
            x=in_vals,
            nbinsx=nbins,
            marker=dict(color=HIST_IN_SCOPE_RGBA),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # in-scope KDE (scaled to counts)
    in_kde = _kde_counts(in_vals, grid, bin_width)
    fig.add_trace(
        go.Scatter(
            x=grid,
            y=in_kde,
            mode="lines",
            line=dict(color=KDE_IN_SCOPE_RGBA),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # brush overlay
    if brush_vals.size > 0:
        fig.add_trace(
            go.Histogram(
                x=brush_vals,
                nbinsx=nbins,
                marker=dict(color=HIST_BRUSH_RGBA),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        if brush_vals.size >= 5:
            brush_kde = _kde_counts(brush_vals, grid, bin_width)
            fig.add_trace(
                go.Scatter(
                    x=grid,
                    y=brush_kde,
                    mode="lines",
                    line=dict(color=KDE_BRUSH_RGBA),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # selected country vertical lines
    for item in selection_store:
        cname = item.get("country_name")
        ccol = item.get("colour_rgb") or "rgb(180,35,24)"
        if not cname:
            continue
        row = pop_df.loc[pop_df["Country"] == cname]
        if row.empty:
            continue
        v = pd.to_numeric(row.iloc[0][metric], errors="coerce")
        if v is None or not np.isfinite(float(v)):
            continue
        fig.add_vline(x=float(v), line_width=2, line_color=ccol, opacity=0.95)

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        barmode="overlay",
        xaxis=dict(title=_pretty_metric(metric), range=[x_min, x_max]),
        yaxis=dict(title="Count"),
        showlegend=False,
    )

    return fig, ("Continent/region active" if scope_active else "Global")


# ============================================================
# Violin
# ============================================================
@callback(
    Output("vis-violin-plot", "figure"),
    Input("vis-violin-attr", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
)
def update_violin(metric, geo_scale, selection_store):
    df_global = _safe_df()

    selection_store = _normalize_selection_store(selection_store)
    selected_names = _names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    pop_df = df_global.copy()
    fig = go.Figure()

    if pop_df.empty or not metric or metric not in pop_df.columns:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig

    in_mask = _geo_mask(pop_df, geo_scale or "global", focus)
    in_df = pop_df.loc[in_mask].copy()
    out_df = pop_df.loc[~in_mask].copy()

    in_vals = _coerce_numeric(in_df[metric]).to_numpy(dtype=float)
    in_vals = in_vals[np.isfinite(in_vals)]
    if in_vals.size == 0:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig

    out_vals = _coerce_numeric(out_df[metric]).to_numpy(dtype=float)
    out_vals = out_vals[np.isfinite(out_vals)]

    scope_active = (geo_scale or "global") in ("continent", "region") and focus

    if scope_active and out_vals.size > 0:
        fig.add_trace(
            go.Violin(
                x=out_vals,
                orientation="h",
                box_visible=False,
                meanline_visible=False,
                points=False,
                line_color="rgba(130,130,130,0.25)",
                fillcolor="rgba(130,130,130,0.10)",
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Violin(
            x=in_vals,
            orientation="h",
            box_visible=False,
            meanline_visible=False,
            points=False,
            line_color="rgba(40,55,70,0.35)",
            fillcolor="rgba(40,55,70,0.12)",
            hoverinfo="skip",
            showlegend=False,
        )
    )

    for item in selection_store:
        cname = item.get("country_name")
        ccol = item.get("colour_rgb") or "rgb(180,35,24)"
        if not cname:
            continue
        row = pop_df.loc[pop_df["Country"] == cname]
        if row.empty:
            continue
        v = pd.to_numeric(row.iloc[0][metric], errors="coerce")
        if v is None or not np.isfinite(float(v)):
            continue
        fig.add_vline(x=float(v), line_width=2, line_color=ccol, opacity=0.95)

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        xaxis=dict(title=_pretty_metric(metric)),
        yaxis=dict(showticklabels=False),
        showlegend=False,
    )
    return fig


# ============================================================
# Scatter (uses Attribute 1/2 dropdowns)
# ============================================================
@callback(
    Output("vis-scatter-plot", "figure"),
    Input("vis-scatter-x", "value"),
    Input("vis-scatter-y", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
)
def update_scatter(x_metric, y_metric, geo_scale, selection_store):
    df_global = _safe_df()

    selection_store = _normalize_selection_store(selection_store)
    selected_names = _names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    pop_df = df_global.copy()
    fig = go.Figure()

    if pop_df.empty or not x_metric or not y_metric or x_metric not in pop_df.columns or y_metric not in pop_df.columns:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig

    in_mask = _geo_mask(pop_df, geo_scale or "global", focus).to_numpy(dtype=bool)
    base_colors = np.where(in_mask, IN_SCOPE_POINT, OUT_SCOPE_POINT)

    x = _coerce_numeric(pop_df[x_metric])
    y = _coerce_numeric(pop_df[y_metric])

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            marker=dict(size=6, color=base_colors),
            text=pop_df["Country"],
            hovertemplate="<b>%{text}</b><br>"
                          + _pretty_metric(x_metric) + ": %{x}<br>"
                          + _pretty_metric(y_metric) + ": %{y}<extra></extra>",
            showlegend=False,
        )
    )

    for item in selection_store:
        cname = item.get("country_name")
        ccol = item.get("colour_rgb") or "rgb(180,35,24)"
        if not cname:
            continue
        row = pop_df.loc[pop_df["Country"] == cname]
        if row.empty:
            continue

        xv = pd.to_numeric(row.iloc[0][x_metric], errors="coerce")
        yv = pd.to_numeric(row.iloc[0][y_metric], errors="coerce")
        if not (np.isfinite(float(xv)) and np.isfinite(float(yv))):
            continue

        fig.add_trace(
            go.Scatter(
                x=[float(xv)],
                y=[float(yv)],
                mode="markers",
                marker=dict(size=12, color=ccol, line=dict(width=1, color="rgba(0,0,0,0.25)")),
                hovertemplate="<b>" + str(cname) + "</b><br>"
                              + _pretty_metric(x_metric) + ": %{x}<br>"
                              + _pretty_metric(y_metric) + ": %{y}<extra></extra>",
                showlegend=False,
            )
        )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        xaxis=dict(title=_pretty_metric(x_metric)),
        yaxis=dict(title=_pretty_metric(y_metric)),
    )
    return fig


# ============================================================
# Radar: require at least 3 selected countries
# ============================================================
@callback(
    Output("vis-radar-plot", "figure"),
    Input("vis-category", "value"),
    Input("vis-selection-store", "data"),
)
def update_radar(ui_category, selection_store):
    df_global = _safe_df()

    selection_store = _normalize_selection_store(selection_store)
    pop_df = df_global.copy()

    if pop_df.empty or len(selection_store) < 3:
        fig = go.Figure()
        fig.add_annotation(
            text="Select at least 3 countries to view the radar plot",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18, color="#374151"),
            align="center",
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    dims = _pick_pcp_dims(pop_df, ui_category, max_dims=6)
    dims = [d for d in dims if d in pop_df.columns]
    if len(dims) < 3:
        fig = go.Figure()
        fig.add_annotation(
            text="Not enough numeric attributes for radar plot",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=16, color="#374151"),
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
            showlegend=False,
        )
        return fig

    mins, maxs = {}, {}
    for d in dims:
        vals = pd.to_numeric(pop_df[d], errors="coerce")
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            mins[d], maxs[d] = 0.0, 1.0
        else:
            mn, mx = float(vals.min()), float(vals.max())
            if mx <= mn:
                mx = mn + 1.0
            mins[d], maxs[d] = mn, mx

    def norm(v, d):
        return (float(v) - mins[d]) / (maxs[d] - mins[d])

    def rgb_to_rgba(rgb: str, a: float) -> str:
        s = (rgb or "").strip()
        if s.startswith("rgba("):
            return s
        if s.startswith("rgb(") and s.endswith(")"):
            inside = s[4:-1]
            parts = [p.strip() for p in inside.split(",")]
            if len(parts) == 3:
                return f"rgba({parts[0]},{parts[1]},{parts[2]},{a})"
        return f"rgba(180,35,24,{a})"

    theta = [_pretty_metric(d) for d in dims]
    theta_closed = theta + [theta[0]]

    fig = go.Figure()

    for item in selection_store:
        cname = item.get("country_name")
        base_rgb = item.get("colour_rgb") or "rgb(180,35,24)"
        if not cname:
            continue

        row = pop_df.loc[pop_df["Country"] == cname]
        if row.empty:
            continue

        r = []
        ok = True
        for d in dims:
            v = pd.to_numeric(row.iloc[0][d], errors="coerce")
            if v is None or not np.isfinite(float(v)):
                ok = False
                break
            r.append(norm(v, d))
        if not ok:
            continue

        r_closed = r + [r[0]]

        fig.add_trace(
            go.Scatterpolar(
                r=r_closed,
                theta=theta_closed,
                mode="lines",
                line=dict(color=rgb_to_rgba(base_rgb, 0.95), width=2),
                fill="toself",
                fillcolor=rgb_to_rgba(base_rgb, 0.25),
                showlegend=False,
            )
        )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        showlegend=False,
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickvals=[0, 0.5, 1], tickfont=dict(size=10)),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig
