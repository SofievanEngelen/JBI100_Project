# jbi100_app/plots/pcp.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims, pretty_metric
from jbi100_app.state.selection_store import SelectedCountry


def build_pcp_figure(
    df: pd.DataFrame,
    ui_category: str | None,
    geo_scale: str,                 # kept for signature compatibility
    in_mask: pd.Series,             # kept for signature compatibility
    selection_store: list[SelectedCountry],
    max_dims: int = 8,
    brush_countries: list[str] | None = None,
    uirevision: str | None = None,
) -> go.Figure:
    dims = pick_pcp_dims(df, ui_category, max_dims=max_dims)

    # Centered, label-safe layout for Parcoords
    MARGIN = dict(l=60, r=60, t=50, b=25)

    if df is None or df.empty or len(dims) < 2:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=MARGIN, uirevision=uirevision)
        return fig

    # ------------------------------------------------------------
    # Normalize values to 0..1 (must match what constraintrange uses)
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
    # Colour scheme (ONLY these 3 states)
    # ------------------------------------------------------------
    BASE_GREY = "rgb(105, 105, 105)"   # default
    FADED_GREY = "rgb(242, 242, 242)"  # filtered out

    # Selected countries (sidebar colours)
    selected_names = [x.get("country_name") for x in (selection_store or []) if x.get("country_name")]
    k = len(selected_names)
    name_to_sel_code = {name: 2 + i for i, name in enumerate(selected_names)}

    # Codes:
    # 1 = base grey
    # 0 = faded grey (only when a filter exists)
    # 2+ = selected colours
    codes = np.ones(len(work), dtype=int)

    brush_set = set(str(x) for x in (brush_countries or []) if x)
    if brush_set:
        brushed_mask = work["Country"].astype(str).isin(brush_set).to_numpy(dtype=bool)
        codes[~brushed_mask] = 0
        codes[brushed_mask] = 1

    # Selected overrides everything
    countries_list = work["Country"].astype(str).tolist()
    for i, cname in enumerate(countries_list):
        code = name_to_sel_code.get(cname)
        if code is not None:
            codes[i] = code

    # Build discrete-ish colourscale for codes 0,1,2..(k+1)
    cmax = max(2, 2 + k)

    # code 0 -> FADED, code 1 -> BASE
    colourscale = [
        [0.0, FADED_GREY],
        [1.0 / cmax - 1e-6, FADED_GREY],
        [1.0 / cmax, BASE_GREY],
        [2.0 / cmax - 1e-6, BASE_GREY],
    ]

    sel_colour_map = {d.get("country_name"): d.get("colour_rgb") for d in (selection_store or [])}
    for i, name in enumerate(selected_names):
        code = 2 + i
        left = code / cmax
        right = min(0.999999, (code + 1e-6) / cmax)
        col = sel_colour_map.get(name) or "rgb(180,35,24)"
        colourscale.append([left, col])
        colourscale.append([right, col])

    dimensions = [{"label": pretty_metric(c), "values": work[c].to_numpy()} for c in dims]

    fig = go.Figure(
        data=[
            go.Parcoords(
                line=dict(
                    color=codes,
                    colorscale=colourscale,
                    cmin=0,
                    cmax=cmax,
                    showscale=False,
                ),
                dimensions=dimensions,
                labelfont=dict(size=12),
                tickfont=dict(size=10),
                domain=dict(x=[0.05, 0.95]),  # centered
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
