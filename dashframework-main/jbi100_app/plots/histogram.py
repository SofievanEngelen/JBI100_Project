# jbi100_app/plots/histogram.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.data.constants import (
    HIST_BRUSH_RGBA,
    HIST_IN_SCOPE_RGBA,
    HIST_OUT_SCOPE_RGBA,
    KDE_BRUSH_RGBA,
    KDE_IN_SCOPE_RGBA,
)
from jbi100_app.plots.common import coerce_numeric, kde_counts, prepare_hist_bins, pretty_metric
from jbi100_app.state.selection_store import SelectedCountry


def build_histogram_figure(
    df: pd.DataFrame,
    metric: str,
    nbins: int,
    geo_scale: str,
    in_mask: pd.Series,
    selection_store: list[SelectedCountry],
    brush_countries: list[str],
) -> go.Figure:
    fig = go.Figure()
    if df is None or df.empty or not metric or metric not in df.columns:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig

    geo_scale = (geo_scale or "global").lower().strip()
    scope_active = geo_scale in ("continent", "region") and in_mask is not None and len(in_mask) == len(df)

    in_df = df.loc[in_mask].copy() if scope_active else df.copy()
    out_df = df.loc[~in_mask].copy() if scope_active else df.iloc[0:0].copy()

    in_vals = coerce_numeric(in_df[metric]).to_numpy(dtype=float)
    in_vals = in_vals[np.isfinite(in_vals)]
    if in_vals.size == 0:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig

    out_vals = coerce_numeric(out_df[metric]).to_numpy(dtype=float)
    out_vals = out_vals[np.isfinite(out_vals)]

    brush_vals = np.array([], dtype=float)
    if brush_countries:
        brush_df = df[df["Country"].isin(brush_countries)].copy()
        brush_vals = coerce_numeric(brush_df[metric]).to_numpy(dtype=float)
        brush_vals = brush_vals[np.isfinite(brush_vals)]

    all_for_bins = in_vals
    if out_vals.size > 0:
        all_for_bins = np.concatenate([all_for_bins, out_vals])
    if brush_vals.size > 0:
        all_for_bins = np.concatenate([all_for_bins, brush_vals])

    grid, bin_width, x_min, x_max = prepare_hist_bins(all_for_bins, bins=nbins)

    if scope_active and out_vals.size > 0:
        fig.add_trace(go.Histogram(x=out_vals, nbinsx=nbins, marker=dict(color=HIST_OUT_SCOPE_RGBA), hoverinfo="skip"))

    fig.add_trace(go.Histogram(x=in_vals, nbinsx=nbins, marker=dict(color=HIST_IN_SCOPE_RGBA), hoverinfo="skip"))

    in_kde = kde_counts(in_vals, grid, bin_width)
    fig.add_trace(go.Scatter(x=grid, y=in_kde, mode="lines", line=dict(color=KDE_IN_SCOPE_RGBA), hoverinfo="skip"))

    if brush_vals.size > 0:
        fig.add_trace(go.Histogram(x=brush_vals, nbinsx=nbins, marker=dict(color=HIST_BRUSH_RGBA), hoverinfo="skip"))
        if brush_vals.size >= 5:
            brush_kde = kde_counts(brush_vals, grid, bin_width)
            fig.add_trace(go.Scatter(x=grid, y=brush_kde, mode="lines", line=dict(color=KDE_BRUSH_RGBA), hoverinfo="skip"))

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
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        barmode="overlay",
        xaxis=dict(title=pretty_metric(metric), range=[x_min, x_max]),
        yaxis=dict(title="Count"),
        showlegend=False,
    )
    return fig
