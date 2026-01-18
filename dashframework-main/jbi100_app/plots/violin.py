# jbi100_app/plots/violin.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.constants import BASE_GREY_35, BASE_GREY_12, FADED_GREY_15, FADED_GREY_10
from jbi100_app.data.attributes import attribute_display_label


def build_violin_figure(
    df: pd.DataFrame,
    metric: str,
    geo_scale: str,
    in_mask: pd.Series,
    selection_store: list[SelectedCountry],
    theme: str = "light",
) -> go.Figure:
    template = "plotly_dark" if theme == "dark" else "plotly_white"

    fig = go.Figure()
    if df is None or df.empty or not metric or metric not in df.columns:
        fig.update_layout(template=template, margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig

    geo_scale = (geo_scale or "global").lower().strip()
    scope_active = geo_scale in ("continent", "region") and in_mask is not None and len(in_mask) == len(df)

    in_df = df.loc[in_mask].copy() if scope_active else df.copy()
    out_df = df.loc[~in_mask].copy() if scope_active else df.iloc[0:0].copy()

    in_vals = coerce_numeric(in_df[metric]).to_numpy(dtype=float)
    in_vals = in_vals[np.isfinite(in_vals)]
    if in_vals.size == 0:
        fig.update_layout(template=template, margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig

    out_vals = coerce_numeric(out_df[metric]).to_numpy(dtype=float)
    out_vals = out_vals[np.isfinite(out_vals)]

    if scope_active and out_vals.size > 0:
        fig.add_trace(
            go.Violin(
                x=out_vals,
                orientation="h",
                box_visible=True,
                meanline_visible=False,
                points=False,
                line_color=FADED_GREY_15,
                fillcolor=FADED_GREY_10,
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Violin(
            x=in_vals,
            orientation="h",
            box_visible=True,
            meanline_visible=False,
            points=False,
            line_color=BASE_GREY_35,
            fillcolor=BASE_GREY_12,
            hoverinfo="skip",
            showlegend=False,
        )
    )

    for item in selection_store:
        cname = item.get("country_name")
        ccol = item.get("colour_rgb") or "rgb(180,35,24)"
        if not cname:
            continue
        row = df.loc[df["Country"] == cname]
        if row.empty:
            continue
        v = pd.to_numeric(row.iloc[0][metric], errors="coerce")
        if v is None or not np.isfinite(float(v)):
            continue
        fig.add_vline(x=float(v), line_width=2, line_color=ccol, opacity=0.95)

    fig.update_layout(
        template=template,
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        xaxis=dict(title=attribute_display_label(metric)),
        yaxis=dict(showticklabels=False),
        showlegend=False,
    )
    return fig
