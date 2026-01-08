# jbi100_app/plots/pcp.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.data.constants import PCP_IN_SCOPE, PCP_OUT_SCOPE
from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims, pretty_metric
from jbi100_app.state.selection_store import SelectedCountry


def build_pcp_figure(
    df: pd.DataFrame,
    ui_category: str | None,
    geo_scale: str,
    in_mask: pd.Series,
    selection_store: list[SelectedCountry],
    max_dims: int = 8,
) -> go.Figure:
    dims = pick_pcp_dims(df, ui_category, max_dims=max_dims)
    if df is None or df.empty or len(dims) < 2:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0))
        return fig

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

    selected_names = [x["country_name"] for x in selection_store]
    k = len(selected_names)
    name_to_sel_code = {name: 2 + i for i, name in enumerate(selected_names)}
    codes = np.zeros(len(work), dtype=int)

    geo_scale = (geo_scale or "global").lower().strip()
    scope_active = geo_scale in ("continent", "region") and in_mask is not None and len(in_mask) == len(df)

    if scope_active:
        in_mask_arr = in_mask.to_numpy(dtype=bool)
        codes[in_mask_arr] = 1
    else:
        codes[:] = 1

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

    dimensions = [{"label": pretty_metric(c), "values": work[c].to_numpy()} for c in dims]

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
    fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None, showlegend=False)
    return fig
