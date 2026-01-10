# jbi100_app/plots/pcp.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims, pretty_metric
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.constants import BASE_GREY, FADED_GREY


def _build_discrete_colorscale(code_to_colour: dict[int, str], cmax: int) -> list[list[object]]:
    """
    Build a piecewise-constant Plotly colorscale for integer codes in [0..cmax].
    """
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
    geo_scale: str,                  # kept for signature compatibility
    in_mask: pd.Series,              # kept for signature compatibility
    selection_store: list[SelectedCountry],
    max_dims: int = 8,
    brush_countries: list[str] | None = None,
    uirevision: str | None = None,    # ✅ RESTORED
    dims_override: list[str] | None = None,
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
        fig.update_layout(
            template="plotly_white",
            margin=MARGIN,
            title=None,
            showlegend=False,
            uirevision=uirevision,
        )
        return fig

    if df is None or df.empty or len(dims) < 2:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_white",
            margin=MARGIN,
            title=None,
            showlegend=False,
            uirevision=uirevision,
        )
        return fig

    # ------------------------------------------------------------
    # Normalize values to 0..1
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # Build colour codes
    # ------------------------------------------------------------
    countries = work["Country"].astype(str).to_numpy()
    codes = np.ones(len(work), dtype=int)

    brush_set = set(str(x) for x in (brush_countries or []) if x)
    if brush_set:
        brushed = np.isin(countries, np.array(list(brush_set), dtype=str))
        codes[~brushed] = 0

    selected_names: list[str] = []
    sel_main: dict[str, str] = {}
    sel_light: dict[str, str] = {}

    for d in (selection_store or []):
        if not isinstance(d, dict):
            continue
        n = d.get("country_name")
        c = d.get("colour_rgb")
        cl = d.get("colour_rgb_light")
        if not n or not c or not cl:
            continue
        n = str(n)
        if n not in sel_main:
            selected_names.append(n)
            sel_main[n] = str(c)
            sel_light[n] = str(cl)

    name_to_code = {name: 2 + i for i, name in enumerate(selected_names)}

    for i, cname in enumerate(countries.tolist()):
        code = name_to_code.get(cname)
        if code is None:
            continue
        if brush_set and cname not in brush_set:
            codes[i] = code + len(selected_names)
        else:
            codes[i] = code

    # ------------------------------------------------------------
    # Discrete colorscale
    # ------------------------------------------------------------
    code_to_colour: dict[int, str] = {
        0: FADED_GREY,
        1: BASE_GREY,
    }

    for i, name in enumerate(selected_names):
        code_to_colour[2 + i] = sel_main[name]
        code_to_colour[2 + len(selected_names) + i] = sel_light[name]

    cmax = 2 + (2 * max(0, len(selected_names) - 1))
    colourscale = _build_discrete_colorscale(code_to_colour, cmax=cmax)

    dimensions = [
        {"label": pretty_metric(c), "values": work[c].to_numpy()}
        for c in dims
    ]

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
        uirevision=uirevision,   # ✅ APPLIED
    )
    return fig
