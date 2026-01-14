from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims, pretty_metric
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.constants import BASE_GREY, FADED_GREY


def _build_discrete_colorscale(code_to_colour: dict[int, str], cmax: int) -> list[list[object]]:
    eps = 1e-6
    scale: list[list[object]] = []

    for code in range(0, cmax + 1):
        col = code_to_colour.get(code)
        if col is None:
            continue

        left = code / (cmax + 1)
        right = (code + 1) / (cmax + 1) - eps
        if right <= left:
            right = min(1.0 - eps, left + eps)

        scale.append([left, col])
        scale.append([right, col])

    scale.sort(key=lambda x: float(x[0]))
    if scale and float(scale[-1][0]) < 1.0:
        scale.append([1.0, scale[-1][1]])

    return scale


def build_pcp_figure(
    df: pd.DataFrame,
    ui_category: str | None,
    geo_scale: str,
    in_mask: pd.Series,
    selection_store: list[SelectedCountry],
    max_dims: int = 8,
    brush_countries: list[str] | None = None,
    uirevision: str | None = None,
    dims_override: list[str] | None = None,
    show_selected_only: bool = False,
    color_by_first_axis: bool = False,
) -> go.Figure:

    MARGIN = dict(l=60, r=60, t=50, b=25)

    # ------------------------------------------------------------
    # Pick dimensions
    # ------------------------------------------------------------
    if dims_override:
        dims = [d for d in dims_override if d in df.columns][:max_dims]
    else:
        dims = pick_pcp_dims(df, ui_category, max_dims=max_dims)

    if df is None or df.empty or len(dims) < 2:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=MARGIN, uirevision=uirevision)
        return fig

    # ------------------------------------------------------------
    # Normalize data
    # ------------------------------------------------------------
    work = df[["Country"] + dims].copy()
    for c in dims:
        work[c] = coerce_numeric(work[c])
        med = work[c].median(skipna=True)
        work[c] = work[c].fillna(med)

        mn, mx = float(work[c].min()), float(work[c].max())
        work[c] = (work[c] - mn) / (mx - mn) if mx > mn else 0.0

    # ------------------------------------------------------------
    # Parse selected countries (store BOTH colours)
    # ------------------------------------------------------------
    selected_names: list[str] = []
    sel_colours: dict[str, dict[str, str]] = {}

    for d in (selection_store or []):
        if not isinstance(d, dict):
            continue
        name = d.get("country_name")
        dark = d.get("colour_rgb")
        light = d.get("colour_rgb_light") or dark
        if not name or not dark:
            continue

        if name not in sel_colours:
            selected_names.append(name)
            sel_colours[name] = {"dark": dark, "light": light}

    # ------------------------------------------------------------
    # Selected-only filtering (IMPORTANT: before masks)
    # ------------------------------------------------------------
    if show_selected_only:
        if not selected_names:
            fig = go.Figure()
            fig.update_layout(template="plotly_white", margin=MARGIN, uirevision=uirevision)
            return fig
        work = work[work["Country"].astype(str).isin(selected_names)].copy()

    # ------------------------------------------------------------
    # Recompute masks AFTER filtering
    # ------------------------------------------------------------
    countries = work["Country"].astype(str).to_numpy()

    # scope mask
    if in_mask is not None and len(in_mask) == len(df):
        df_scope = pd.Series(in_mask.to_numpy(dtype=bool), index=df["Country"].astype(str))
        in_scope = np.array([df_scope.get(c, True) for c in countries], dtype=bool)
    else:
        in_scope = np.ones(len(work), dtype=bool)

    # brush mask
    brush_set = set(str(x) for x in (brush_countries or []) if x)
    in_brush = (
        np.isin(countries, np.array(list(brush_set), dtype=str))
        if brush_set
        else np.ones(len(work), dtype=bool)
    )

    # ------------------------------------------------------------
    # PCP dimensions
    # ------------------------------------------------------------
    dimensions = [
        {"label": pretty_metric(c), "values": work[c].to_numpy()}
        for c in dims
    ]

    # ============================================================
    # MODE A: Color by first axis (EARLY EXIT)
    # ============================================================
    if color_by_first_axis:
        first_dim = dims[0]
        vals = work[first_dim].to_numpy(dtype=float)

        sentinel = -0.10
        active = in_scope & in_brush
        vals = np.where(active, vals, sentinel)

        colorscale = [
            [0.0, FADED_GREY],
            [0.0909, FADED_GREY],
            [0.0910, "rgb(68,1,84)"],
            [1.0, "rgb(253,231,37)"],
        ]

        fig = go.Figure(
            data=[
                go.Parcoords(
                    line=dict(
                        color=vals,
                        colorscale=colorscale,
                        cmin=sentinel,
                        cmax=1.0,
                        showscale=True,
                        colorbar=dict(title=pretty_metric(first_dim)),
                    ),
                    dimensions=dimensions,
                )
            ]
        )

        fig.update_layout(
            template="plotly_white",
            margin=MARGIN,
            uirevision=uirevision,
        )
        return fig

    # ============================================================
    # MODE B: Discrete colours (default)
    # ============================================================
    # Codes:
    # 0 = faded
    # 1 = base grey
    # 2+ = selected countries
    codes = np.ones(len(work), dtype=int)

    codes[~in_scope] = 0
    codes[~in_brush] = 0

    name_to_code = {name: 2 + i for i, name in enumerate(selected_names)}

    for i, cname in enumerate(countries):
        if cname in name_to_code:
            codes[i] = name_to_code[cname]

    # ------------------------------------------------------------
    # Colour map (brush-aware)
    # ------------------------------------------------------------
    code_to_colour = {
        0: FADED_GREY,
        1: BASE_GREY,
    }

    for i, name in enumerate(selected_names):
        dark = sel_colours[name]["dark"]
        light = sel_colours[name]["light"]

        idx = np.where(countries == name)[0]
        if len(idx) > 0 and in_brush[idx[0]]:
            code_to_colour[2 + i] = dark
        else:
            code_to_colour[2 + i] = light

    colourscale = _build_discrete_colorscale(
        code_to_colour,
        cmax=max(code_to_colour),
    )

    fig = go.Figure(
        data=[
            go.Parcoords(
                line=dict(
                    color=codes.astype(float),
                    colorscale=colourscale,
                    cmin=0,
                    cmax=max(code_to_colour),
                    showscale=False,
                ),
                dimensions=dimensions,
            )
        ]
    )

    fig.update_layout(
        template="plotly_white",
        margin=MARGIN,
        uirevision=uirevision,
    )

    return fig


