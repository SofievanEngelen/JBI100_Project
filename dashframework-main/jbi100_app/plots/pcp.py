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
    if dims_override:
        dims = [d for d in dims_override if d in df.columns][:max_dims]
    else:
        dims = pick_pcp_dims(df, ui_category, max_dims=max_dims)

    MARGIN = dict(l=60, r=60, t=50, b=25)

    if dims_override is not None and len(dims) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Select at least 2 attributes in the sidebar to view the PCP",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=18, color="#374151"),
            align="center",
        )
        fig.update_layout(template="plotly_white", margin=MARGIN, title=None, showlegend=False)
        return fig

    if df is None or df.empty or len(dims) < 2:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=MARGIN, uirevision=uirevision)
        return fig

    # ---- normalize
    work = df[["Country"] + dims].copy()
    for c in dims:
        work[c] = coerce_numeric(work[c])
        med = work[c].median(skipna=True)
        work[c] = work[c].fillna(med)

        mn, mx = float(work[c].min()), float(work[c].max())
        if np.isfinite(mn) and np.isfinite(mx) and mx > mn:
            work[c] = (work[c] - mn) / (mx - mn)
        else:
            work[c] = 0.0

    # ---- selected countries list (for both modes)
    selected_names: list[str] = []
    sel_colour_map: dict[str, str] = {}
    for d in (selection_store or []):
        if not isinstance(d, dict):
            continue
        n = d.get("country_name")
        c = d.get("colour_rgb")
        if not n or not c:
            continue
        if n not in sel_colour_map:
            selected_names.append(n)
            sel_colour_map[n] = c

    if show_selected_only:
        keep = set(selected_names)
        if not keep:
            fig = go.Figure()
            fig.update_layout(template="plotly_white", margin=MARGIN, uirevision=uirevision)
            return fig
        work = work[work["Country"].astype(str).isin(keep)].copy()

    countries = work["Country"].astype(str).to_numpy()

    # ---- scope mask: fade out-of-scope (continent/region)
    if in_mask is not None and isinstance(in_mask, pd.Series) and len(in_mask) == len(df):
        # map df-level mask -> work rows by Country match
        # (work is derived from df, but may be filtered by selected_only)
        df_in = pd.Series(in_mask.to_numpy(dtype=bool), index=df["Country"].astype(str))
        in_scope = np.array([bool(df_in.get(str(c), True)) for c in countries], dtype=bool)
    else:
        in_scope = np.ones(len(work), dtype=bool)

    # ---- brush mask
    brush_set = set(str(x) for x in (brush_countries or []) if x)
    in_brush = np.ones(len(work), dtype=bool)
    if brush_set:
        in_brush = np.isin(countries, np.array(list(brush_set), dtype=str))

    dimensions = [{"label": pretty_metric(c), "values": work[c].to_numpy()} for c in dims]

    # ============================================================
    # MODE A: Color by first axis (single trace, stable)
    # - Out-of-scope and/or non-brushed -> faded grey via sentinel
    # ============================================================
    if color_by_first_axis:
        first_dim = dims[0]
        vals = work[first_dim].to_numpy(dtype=float)  # 0..1

        # Sentinel: everything "inactive" becomes grey
        sentinel = -0.10
        active = in_scope & in_brush
        vals = np.where(active, vals, sentinel)

        # Colorscale: a grey band at bottom, then Viridis for 0..1
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
                    labelfont=dict(size=12),
                    tickfont=dict(size=10),
                    domain=dict(x=[0.05, 0.95]),
                )
            ]
        )

        fig.update_layout(
            template="plotly_white",
            margin=MARGIN,
            title=None,
            showlegend=False,
            uirevision=uirevision,
        )
        return fig

    # ============================================================
    # MODE B: Discrete colours (selected colours + scope/brush fade)
    # ============================================================
    # Codes:
    # 0 = faded (out of scope OR out of brush)
    # 1 = base grey (in scope)
    # 2+ = selected countries
    codes = np.ones(len(work), dtype=int)

    # first apply scope fade
    codes[~in_scope] = 0

    # then apply brush fade (also fades out-of-scope already)
    if brush_set:
        codes[~in_brush] = 0

    name_to_code = {name: 2 + i for i, name in enumerate(selected_names)}
    for i, cname in enumerate(countries.tolist()):
        code = name_to_code.get(cname)
        if code is not None:
            codes[i] = code

    k = len(selected_names)
    cmax = 2 + max(0, k - 1)

    code_to_colour: dict[int, str] = {
        0: FADED_GREY,
        1: BASE_GREY,
    }
    for i, name in enumerate(selected_names):
        code_to_colour[2 + i] = sel_colour_map[name]

    colourscale = _build_discrete_colorscale(code_to_colour, cmax=cmax)

    fig = go.Figure(
        data=[
            go.Parcoords(
                line=dict(
                    color=codes.astype(float),
                    colorscale=colourscale,
                    cmin=0,
                    cmax=cmax,
                    showscale=False,
                ),
                dimensions=dimensions,
                labelfont=dict(size=12),
                tickfont=dict(size=10),
                domain=dict(x=[0.05, 0.95]),
            )
        ]
    )

    fig.update_layout(
        template="plotly_white",
        margin=MARGIN,
        title=None,
        showlegend=False,
        uirevision=uirevision,
    )

    return fig
