# jbi100_app/callbacks/visualisation_callbacks.py
from __future__ import annotations

import random

from dash import Input, Output, State, callback, no_update
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from jbi100_app.data.data_loader import DATA_INFO, ALL_COUNTRIES, UN_COUNTRIES
from jbi100_app.data.category_mapping import UI_CATEGORIES

# ============================================================
# Styling
# ============================================================
COLOR_SCALE = px.colors.sequential.YlOrRd

# PCP: population as density (alpha blending), selection as highlight
PCP_POP_LINE = "rgba(40,55,70,0.10)"
PCP_SEL_LINE_FALLBACK = "rgba(180,35,24,0.95)"

# Map highlighting: brush (secondary)
MAP_BRUSH_OUTLINE_COLOR = "rgba(43,102,227,0.90)"

# Histogram colors (use opacity for alpha blending)
HIST_POP_RGBA = "rgba(40,55,70,0.20)"
HIST_SEL_RGBA = "rgba(180,35,24,0.35)"
HIST_BRUSH_RGBA = "rgba(43,102,227,0.30)"

# KDE line colors
KDE_POP_RGBA = "rgba(40,55,70,0.85)"
KDE_SEL_RGBA = "rgba(180,35,24,0.90)"
KDE_BRUSH_RGBA = "rgba(43,102,227,0.90)"

# ============================================================
# Selection color policy
# ============================================================
MAX_SELECTED_COUNTRIES = 5

# Unique palette (must have >= MAX_SELECTED_COUNTRIES colors)
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

# ============================================================
# Helpers
# ============================================================
_META_COLS = {"Country", "Region", "Continent", "_UN_NAME", "_PLOTLY_NAME"}


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


def _geo_subset(df: pd.DataFrame, geo_scale: str, focus_country: str | None) -> pd.DataFrame:
    geo_scale = geo_scale or "global"
    if geo_scale not in ("continent", "region") or not focus_country:
        return df
    if geo_scale == "continent":
        cont = df.loc[df["Country"] == focus_country, "Continent"]
        if cont.empty:
            return df
        return df[df["Continent"] == cont.iloc[0]].copy()
    reg = df.loc[df["Country"] == focus_country, "Region"]
    if reg.empty:
        return df
    return df[df["Region"] == reg.iloc[0]].copy()


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
    """
    Gaussian KDE scaled to histogram counts:
      counts(grid) ≈ pdf(grid) * n * bin_width
    """
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


# ============================================================
# NEW: Stable, unique, random color assignment per country
# ============================================================
def _normalize_selection_store(sel_store) -> list[dict]:
    """
    Ensure list-of-dicts shape and uniqueness:
      [{"country_name": str, "colour_rgb": str}, ...]
    Invalid entries dropped. Duplicate country names collapsed (first wins).
    If duplicate colors exist, later duplicates are dropped (conservative).
    """
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
            # conservative: skip duplicates rather than silently reassign
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


def _available_colors(sel_store: list[dict]) -> list[str]:
    used = {str(x.get("colour_rgb")) for x in sel_store if isinstance(x, dict) and x.get("colour_rgb")}
    return [c for c in SELECTION_COLOR_POOL if c not in used]


def _merge_selection_store(prev_store, desired_names: list[str]) -> tuple[list[dict], bool]:
    """
    Build the next selection-store from:
      - prev_store: current list-of-dicts
      - desired_names: dropdown/map desired list[str] (order matters)

    Rules:
      - Preserve existing colors for countries already selected
      - For newly added countries: randomly pick an unused color from pool
      - No two selected countries may share the same color
      - Returns (new_store, ok). If ok is False, it means we could not assign a unique color.
    """
    prev_store = _normalize_selection_store(prev_store)
    desired_names = _clamp_selection(desired_names, limit=MAX_SELECTED_COUNTRIES)

    prev_map = {d["country_name"]: d["colour_rgb"] for d in prev_store}

    new_store: list[dict] = []
    used_colors: set[str] = set()

    # First: keep existing selections (in desired order)
    for name in desired_names:
        if name in prev_map:
            col = prev_map[name]
            if col in used_colors:
                # should not happen if prev was valid, but guard anyway
                continue
            new_store.append({"country_name": name, "colour_rgb": col})
            used_colors.add(col)

    # Then: assign colors for new countries
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
# 1) Init controls from session-store (also initializes selection-store)
# ============================================================
@callback(
    Output("vis-country", "value"),
    Output("vis-category", "value"),
    Output("vis-metric", "value"),
    Output("vis-country", "options"),
    Output("vis-metric", "options"),
    Output("vis-warnings", "children"),
    Output("vis-selection-store", "data"),
    Input("session-store", "data"),
    State("vis-country", "value"),
    State("vis-category", "value"),
    State("vis-metric", "value"),
    State("vis-selection-store", "data"),
)
def init_vis_controls(data, cur_country, cur_cat, cur_metric, cur_sel_store):
    df = _safe_df()

    countries_all = (
        ALL_COUNTRIES
        if (ALL_COUNTRIES is not None and len(ALL_COUNTRIES) > 0)
        else (sorted(df["Country"].dropna().astype(str).unique().tolist()) if "Country" in df.columns else [])
    )
    country_opts = [{"label": str(c), "value": str(c)} for c in countries_all]

    data = data or {}
    s_country = data.get("country")
    s_cat = data.get("ui_category")

    selected_names = _as_list_of_str(cur_country) if cur_country else _as_list_of_str(s_country)
    selected_names = _clamp_selection(selected_names, limit=MAX_SELECTED_COUNTRIES)

    ui_category = cur_cat if (cur_cat is not None) else s_cat

    metric_cols = _metric_cols_for_category(df, ui_category)
    if not metric_cols:
        metric_cols = _all_numeric_metrics(df)

    metric_opts = [{"label": _pretty_metric(c), "value": c} for c in metric_cols]
    metric = cur_metric if (cur_metric in set(metric_cols)) else (metric_cols[0] if metric_cols else None)

    warn = ""
    if df.empty:
        warn = "Dataset is empty after UN filter. Check mun_dataset.csv loading and Country names."
    elif not metric_cols:
        warn = "No numeric metrics found (or category mapping does not match columns)."

    cur_sel_store = _normalize_selection_store(cur_sel_store)

    # If we already have a valid store, keep it (and trim to current selected_names)
    if cur_sel_store:
        merged, ok = _merge_selection_store(cur_sel_store, _names_from_store(cur_sel_store))
        if ok:
            cur_sel_store = merged

    # If store empty but we have selected names (from landing), assign random unique colors
    if (not cur_sel_store) and selected_names:
        merged, ok = _merge_selection_store([], selected_names)
        cur_sel_store = merged if ok else []

    # Ensure dropdown reflects store if store exists
    if cur_sel_store:
        selected_names = _names_from_store(cur_sel_store)

    return selected_names, ui_category, metric, country_opts, metric_opts, warn, cur_sel_store


# ============================================================
# 1b) Keep metric dropdown consistent when category changes
# ============================================================
@callback(
    Output("vis-metric", "options", allow_duplicate=True),
    Output("vis-metric", "value", allow_duplicate=True),
    Input("vis-category", "value"),
    State("vis-metric", "value"),
    prevent_initial_call=True,
)
def refresh_metric_options(ui_category, cur_metric):
    df = _safe_df()
    cols = _metric_cols_for_category(df, ui_category)
    if not cols:
        cols = _all_numeric_metrics(df)

    opts = [{"label": _pretty_metric(c), "value": c} for c in cols]
    if not cols:
        return opts, None
    return opts, (cur_metric if cur_metric in set(cols) else cols[0])


# ============================================================
# 2) Clear selection / brush
# ============================================================
@callback(
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-selection-store", "data", allow_duplicate=True),
    Output("vis-max-selection-dialog", "displayed", allow_duplicate=True),
    Input("vis-clear-selection", "n_clicks"),
    prevent_initial_call=True,
)
def clear_selection(n):
    if n and n > 0:
        return [], [], False
    return no_update, no_update, no_update


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
# NEW: Dropdown change -> update selection store with stable colors
#      (and enforce max 5 with popup)
# ============================================================
@callback(
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-selection-store", "data", allow_duplicate=True),
    Output("vis-max-selection-dialog", "displayed", allow_duplicate=True),
    Input("vis-country", "value"),
    State("vis-selection-store", "data"),
    prevent_initial_call=True,
)
def dropdown_selection_enforce_max(vis_country_value, current_sel_store):
    new_names = _as_list_of_str(vis_country_value)
    current_sel_store = _normalize_selection_store(current_sel_store)
    prev_names = _names_from_store(current_sel_store)

    # If user tries to select >5, revert and show popup
    if len(new_names) > MAX_SELECTED_COUNTRIES:
        return prev_names, current_sel_store, True

    new_names = _clamp_selection(new_names, limit=MAX_SELECTED_COUNTRIES)
    merged, ok = _merge_selection_store(current_sel_store, new_names)
    if not ok:
        # No unique colors available: revert and show popup
        return prev_names, current_sel_store, True

    return _names_from_store(merged), merged, False


# ============================================================
# 3) Map click -> selection (linked views)
#    stable colors, no reshuffle; enforce max
# ============================================================
@callback(
    Output("vis-country", "value", allow_duplicate=True),
    Output("vis-selection-store", "data", allow_duplicate=True),
    Output("vis-max-selection-dialog", "displayed", allow_duplicate=True),
    Input("vis-map", "clickData"),
    State("vis-selection-store", "data"),
    prevent_initial_call=True,
)
def map_click_to_selection(clickData, current_sel_store):
    current_sel_store = _normalize_selection_store(current_sel_store)
    selected_names = _names_from_store(current_sel_store)

    country = _to_country_from_click(clickData)
    if not country:
        return no_update, no_update, no_update

    # Toggle off
    if country in selected_names:
        new_names = [c for c in selected_names if c != country]
        merged, ok = _merge_selection_store(current_sel_store, new_names)
        if ok:
            return _names_from_store(merged), merged, False
        return selected_names, current_sel_store, False

    # Try to add
    if len(selected_names) >= MAX_SELECTED_COUNTRIES:
        return no_update, no_update, True

    new_names = [country] + selected_names
    new_names = _clamp_selection(new_names, limit=MAX_SELECTED_COUNTRIES)

    merged, ok = _merge_selection_store(current_sel_store, new_names)
    if not ok:
        return no_update, no_update, True

    return _names_from_store(merged), merged, False


# ============================================================
# 4) PCP: draw + capture brush subset into store
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
    pop_df = _geo_subset(df_global, geo_scale or "global", focus)

    dims = _pick_pcp_dims(df_global, ui_category, max_dims=8)

    if pop_df.empty or len(dims) < 2:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=40, b=10), title="PCP (insufficient data)")
        return fig, "Population: (none)", None

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

    dimensions = [{"label": _pretty_metric(c), "values": work[c].to_numpy()} for c in dims]

    fig = go.Figure()
    fig.add_trace(
        go.Parcoords(
            line=dict(color=PCP_POP_LINE),
            dimensions=dimensions,
            labelfont=dict(size=11),
            tickfont=dict(size=10),
        )
    )

    # Overlay selected countries using their stored color (stable)
    for item in selection_store:
        cname = item.get("country_name")
        ccol = item.get("colour_rgb")
        if not cname:
            continue
        sel = work[work["Country"] == cname].copy()
        if sel.empty:
            continue
        sel_dims = [{"label": _pretty_metric(c), "values": sel[c].to_numpy()} for c in dims]
        fig.add_trace(
            go.Parcoords(
                line=dict(color=ccol or PCP_SEL_LINE_FALLBACK),
                dimensions=sel_dims,
                labelfont=dict(size=11),
                tickfont=dict(size=10),
            )
        )

    pop_text = "Population: global" if (geo_scale or "global") == "global" else f"Population: {geo_scale} (focus={focus or 'none'})"
    fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=40, b=10), title="PCP (all countries; selection is highlight)")

    brush_out = prev_brush if prev_brush is not None else None
    brushed = _extract_brush_countries(selected_data, work)
    if brushed:
        brush_out = {"countries": brushed}

    return fig, pop_text, brush_out


# ============================================================
# 5) Map: metric + selection highlight + brush highlight
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
    pop_df = _geo_subset(df_global, geo_scale or "global", focus)

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

    if pop_df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=40, b=10), title="Map (no data)")
        return fig, msg

    if not metric or metric not in pop_df.columns:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=40, b=10), title="Map (pick a metric)")
        return fig, msg

    plot_df = pop_df.copy()
    plot_df["_z"] = _coerce_numeric(plot_df[metric])

    fig = go.Figure()
    fig.add_trace(
        go.Choropleth(
            locations=plot_df["_PLOTLY_NAME"],
            locationmode="country names",
            z=plot_df["_z"],
            text=plot_df["Country"],
            customdata=np.stack([plot_df["Country"]], axis=-1),
            colorscale=COLOR_SCALE,
            colorbar=dict(title=_pretty_metric(metric)),
            marker_line_color="rgba(255,255,255,0.35)",
            marker_line_width=0.5,
            hovertemplate="<b>%{text}</b><br>" + _pretty_metric(metric) + ": %{z}<extra></extra>",
        )
    )

    # Brush outline
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

    # Selection outlines per selected country with stored color (stable)
    for item in selection_store:
        cname = item.get("country_name")
        ccol = item.get("colour_rgb") or "rgb(180,35,24)"
        if not cname:
            continue
        sel_df = plot_df[plot_df["Country"] == cname].copy()
        if sel_df.empty:
            continue
        fig.add_trace(
            go.Choropleth(
                locations=sel_df["_PLOTLY_NAME"],
                locationmode="country names",
                z=[1.0],
                text=sel_df["Country"],
                customdata=np.stack([sel_df["Country"]], axis=-1),
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                showscale=False,
                marker_line_color=ccol,
                marker_line_width=2.8,
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=40, b=10),
        title="Map (click to select countries; PCP brush highlights subset)",
        geo=dict(showframe=False, showcoastlines=False, projection_type="natural earth"),
    )
    return fig, msg


# ============================================================
# 6) Distribution / explanation view
# ============================================================
@callback(
    Output("vis-filter-plot", "figure"),
    Output("vis-filter-text", "children"),
    Input("vis-metric", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
)
def update_distribution(metric, geo_scale, selection_store, brush_data):
    df_global = _safe_df()

    selection_store = _normalize_selection_store(selection_store)
    selected_names = _names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    pop_df = _geo_subset(df_global, geo_scale or "global", focus)

    if pop_df.empty or not metric or metric not in pop_df.columns:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=10, r=10, t=40, b=10),
            title="Distribution (pick a metric)",
        )
        return fig, ""

    pop_vals = _coerce_numeric(pop_df[metric]).to_numpy(dtype=float)
    pop_vals = pop_vals[np.isfinite(pop_vals)]

    if pop_vals.size == 0:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=10, r=10, t=40, b=10),
            title="Distribution (no numeric data)",
        )
        return fig, ""

    # Brush (optional overlay) — stays
    brush = []
    if isinstance(brush_data, dict) and brush_data.get("countries"):
        brush = [str(x) for x in brush_data.get("countries", []) if x]

    subset_label = None
    subset_vals = np.array([], dtype=float)

    if brush:
        subset_df = pop_df[pop_df["Country"].isin(brush)].copy()
        subset_vals = _coerce_numeric(subset_df[metric]).to_numpy(dtype=float)
        subset_vals = subset_vals[np.isfinite(subset_vals)]
        subset_label = "Brush subset"
    # NOTE: removed "Selected (1–5)" combined overlay entirely

    grid, bin_width, x_min, x_max = _prepare_hist_bins(pop_vals, bins=30)

    fig = go.Figure()

    # Population histogram
    fig.add_trace(
        go.Histogram(
            x=pop_vals,
            nbinsx=30,
            name="Population",
            marker=dict(color=HIST_POP_RGBA),
            opacity=1.0,
            hovertemplate="Population<br>Value: %{x}<br>Count: %{y}<extra></extra>",
        )
    )

    # Population KDE (scaled to counts)
    pop_kde = _kde_counts(pop_vals, grid, bin_width)
    fig.add_trace(
        go.Scatter(
            x=grid,
            y=pop_kde,
            mode="lines",
            name="Population density",
            line=dict(color=KDE_POP_RGBA),
            hoverinfo="skip",
        )
    )

    # Brush overlay (priority: brush)
    if subset_label and subset_vals.size > 0:
        fig.add_trace(
            go.Histogram(
                x=subset_vals,
                nbinsx=30,
                name=subset_label,
                marker=dict(color=HIST_BRUSH_RGBA),
                opacity=1.0,
                hovertemplate=f"{subset_label}<br>Value: %{{x}}<br>Count: %{{y}}<extra></extra>",
            )
        )
        if subset_vals.size >= 5:
            sub_kde = _kde_counts(subset_vals, grid, bin_width)
            fig.add_trace(
                go.Scatter(
                    x=grid,
                    y=sub_kde,
                    mode="lines",
                    name=f"{subset_label} density",
                    line=dict(color=KDE_BRUSH_RGBA),
                    hoverinfo="skip",
                )
            )

    # NEW: per-country vertical markers (no labels)
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

        fig.add_vline(
            x=float(v),
            line_width=2,
            line_color=ccol,
            opacity=0.95,
        )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=40, b=10),
        title=f"Distribution: {_pretty_metric(metric)}",
        barmode="overlay",
        xaxis=dict(title=_pretty_metric(metric), range=[x_min, x_max]),
        yaxis=dict(title="Count"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0),
    )

    if brush:
        return fig, "Explanation view: updated from PCP brush (subset vs population)."
    if selected_names:
        return fig, "Explanation view: showing selected country positions (vertical lines)."
    return fig, "Explanation view: showing population distribution (no subset selected)."


@callback(
    Output("vis-violin-plot", "figure"),
    Input("vis-metric", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
)
def update_violin(metric, geo_scale, selection_store):
    df_global = _safe_df()
    selection_store = _normalize_selection_store(selection_store)
    selected_names = _names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    pop_df = _geo_subset(df_global, geo_scale or "global", focus)

    fig = go.Figure()
    if pop_df.empty or not metric or metric not in pop_df.columns:
        fig.update_layout(template="plotly_white", title="Violin (pick a metric)")
        return fig

    pop_vals = _coerce_numeric(pop_df[metric]).to_numpy(dtype=float)
    pop_vals = pop_vals[np.isfinite(pop_vals)]
    if pop_vals.size == 0:
        fig.update_layout(template="plotly_white", title="Violin (no numeric data)")
        return fig

    # Population violin (horizontal so x=value and we can draw vertical lines)
    fig.add_trace(
        go.Violin(
            x=pop_vals,
            name="Population",
            orientation="h",
            box_visible=False,
            meanline_visible=False,
            points=False,
            line_color="rgba(40,55,70,0.35)",
            fillcolor="rgba(40,55,70,0.12)",
            hoverinfo="skip",
            hovertemplate=None,
        )
    )

    # Vertical markers for selected countries (no labels)
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

        fig.add_vline(
            x=float(v),
            line_width=2,
            line_color=ccol,
            opacity=0.95,
        )

    fig.update_layout(
        template="plotly_white",
        title=f"Violin: {_pretty_metric(metric)}",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(title=_pretty_metric(metric)),
        yaxis=dict(showticklabels=False, title=""),
        showlegend=False,
    )
    return fig

@callback(
    Output("vis-scatter-plot", "figure"),
    Input("vis-metric", "value"),
    Input("vis-category", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
)
def update_scatter(metric, ui_category, geo_scale, selection_store):
    df_global = _safe_df()
    selection_store = _normalize_selection_store(selection_store)
    selected_names = _names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    pop_df = _geo_subset(df_global, geo_scale or "global", focus)

    fig = go.Figure()
    if pop_df.empty:
        fig.update_layout(template="plotly_white", title="Scatter (no data)")
        return fig

    dims = _pick_pcp_dims(df_global, ui_category, max_dims=8)
    dims = [d for d in dims if d in pop_df.columns]

    if len(dims) < 2:
        fig.update_layout(template="plotly_white", title="Scatter (need 2 numeric attributes)")
        return fig

    # choose x/y
    x_metric = dims[0]
    if metric in dims and metric != x_metric:
        y_metric = metric
    else:
        y_metric = dims[1]

    x = _coerce_numeric(pop_df[x_metric])
    y = _coerce_numeric(pop_df[y_metric])

    # Base population layer (single color)
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            name="Population",
            marker=dict(size=6, color="rgba(40,55,70,0.25)"),
            text=pop_df["Country"],
            hovertemplate="<b>%{text}</b><br>"
                          + _pretty_metric(x_metric) + ": %{x}<br>"
                          + _pretty_metric(y_metric) + ": %{y}<extra></extra>",
        )
    )

    # Selected countries (colored points, on top)
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
                name=cname,
                marker=dict(size=12, color=ccol, line=dict(width=1, color="rgba(0,0,0,0.25)")),
                hovertemplate="<b>" + str(cname) + "</b><br>"
                              + _pretty_metric(x_metric) + ": %{x}<br>"
                              + _pretty_metric(y_metric) + ": %{y}<extra></extra>",
                showlegend=False,
            )
        )

    fig.update_layout(
        template="plotly_white",
        title=f"Scatter: {_pretty_metric(y_metric)} vs {_pretty_metric(x_metric)}",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(title=_pretty_metric(x_metric)),
        yaxis=dict(title=_pretty_metric(y_metric)),
    )
    return fig

@callback(
    Output("vis-radar-plot", "figure"),
    Input("vis-category", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
)
def update_radar(ui_category, geo_scale, selection_store):
    df_global = _safe_df()
    selection_store = _normalize_selection_store(selection_store)
    selected_names = _names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    pop_df = _geo_subset(df_global, geo_scale or "global", focus)

    fig = go.Figure()
    if pop_df.empty or not selection_store:
        fig.update_layout(template="plotly_white", title="Radar (select countries)")
        return fig

    # Keep radar readable (5–7 axes is ideal)
    dims = _pick_pcp_dims(df_global, ui_category, max_dims=6)
    dims = [d for d in dims if d in pop_df.columns]
    if len(dims) < 3:
        fig.update_layout(template="plotly_white", title="Radar (need ≥ 3 attributes)")
        return fig

    # Compute min/max for normalization in current population scope
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
        v = float(v)
        return (v - mins[d]) / (maxs[d] - mins[d])

    def rgb_to_rgba(rgb: str, a: float) -> str:
        # Accepts "rgb(r,g,b)" or already "rgba(...)"
        s = (rgb or "").strip()
        if s.startswith("rgba("):
            return s  # leave it
        if s.startswith("rgb(") and s.endswith(")"):
            inside = s[4:-1]
            parts = [p.strip() for p in inside.split(",")]
            if len(parts) == 3:
                return f"rgba({parts[0]},{parts[1]},{parts[2]},{a})"
        # fallback
        return f"rgba(180,35,24,{a})"

    theta = [_pretty_metric(d) for d in dims]
    theta_closed = theta + [theta[0]]

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

        # Filled coloured polygon + outline
        fig.add_trace(
            go.Scatterpolar(
                r=r_closed,
                theta=theta_closed,
                mode="lines",
                name=str(cname),
                line=dict(color=rgb_to_rgba(base_rgb, 0.95), width=2),
                fill="toself",
                fillcolor=rgb_to_rgba(base_rgb, 0.25),
            )
        )

    fig.update_layout(
        template="plotly_white",
        title="Radar: selected countries (normalized per axis)",
        margin=dict(l=20, r=20, t=50, b=20),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickvals=[0, 0.5, 1]),
            bgcolor="rgba(0,0,0,0)",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.0),
    )
    return fig
