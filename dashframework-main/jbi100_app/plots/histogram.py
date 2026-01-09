# jbi100_app/plots/histogram.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.data.constants import (
    HIST_BRUSH_RGBA,
    HIST_IN_SCOPE_RGBA,
    HIST_OUT_SCOPE_RGBA,
    KDE_IN_SCOPE_RGBA,
)
from jbi100_app.plots.common import coerce_numeric, kde_counts, prepare_hist_bins, pretty_metric
from jbi100_app.state.selection_store import SelectedCountry


def _bin_edges(x_min: float, x_max: float, nbins: int) -> np.ndarray:
    return np.linspace(float(x_min), float(x_max), max(1, int(nbins)) + 1)


def _countries_per_bin(values: np.ndarray, countries: list[str], edges: np.ndarray) -> list[list[str]]:
    """
    For each bin i, return list of countries whose value falls into that bin.
    """
    out = [[] for _ in range(len(edges) - 1)]
    if values.size == 0:
        return out

    # right=False => [left, right)
    idx = np.digitize(values, edges, right=False) - 1
    for j, b in enumerate(idx.tolist()):
        if 0 <= b < len(out):
            out[b].append(str(countries[j]))
        elif b == len(out):  # value == last edge
            out[-1].append(str(countries[j]))
    return out


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

    # ---- in-scope values (and names)
    in_vals = coerce_numeric(in_df[metric]).to_numpy(dtype=float)
    in_keep = np.isfinite(in_vals)
    in_vals = in_vals[in_keep]
    in_names = in_df.loc[in_keep, "Country"].astype(str).tolist()

    if in_vals.size == 0:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0), title=None)
        return fig

    # ---- out-of-scope values
    out_vals = coerce_numeric(out_df[metric]).to_numpy(dtype=float)
    out_vals = out_vals[np.isfinite(out_vals)]

    # ---- brush overlay values
    brush_vals = np.array([], dtype=float)
    if brush_countries:
        brush_df = df[df["Country"].isin(brush_countries)].copy()
        brush_vals = coerce_numeric(brush_df[metric]).to_numpy(dtype=float)
        brush_vals = brush_vals[np.isfinite(brush_vals)]

    # ---- compute consistent bins using all values available
    all_vals = in_vals
    if out_vals.size:
        all_vals = np.concatenate([all_vals, out_vals])
    if brush_vals.size:
        all_vals = np.concatenate([all_vals, brush_vals])

    grid, bin_width, x_min, x_max = prepare_hist_bins(all_vals, bins=int(nbins or 30))
    edges = _bin_edges(x_min, x_max, int(nbins or 30))
    centers = (edges[:-1] + edges[1:]) / 2.0

    # counts
    in_counts, _ = np.histogram(in_vals, bins=edges)
    out_counts = None
    if out_vals.size:
        out_counts, _ = np.histogram(out_vals, bins=edges)

    brush_counts = None
    if brush_vals.size:
        brush_counts, _ = np.histogram(brush_vals, bins=edges)

    # countries per bin for click-to-filter
    in_countries_per_bin = _countries_per_bin(in_vals, in_names, edges)

    # ---- out-of-scope bars
    if scope_active and out_vals.size:
        fig.add_trace(
            go.Bar(
                x=centers,
                y=out_counts,
                width=np.full(len(centers), float(bin_width)),
                marker=dict(color=HIST_OUT_SCOPE_RGBA),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # ---- in-scope bars (clickable)
    fig.add_trace(
        go.Bar(
            x=centers,
            y=in_counts,
            width=np.full(len(centers), float(bin_width)),
            marker=dict(color=HIST_IN_SCOPE_RGBA),
            customdata=[
                {
                    "countries": in_countries_per_bin[i],
                    "left": float(edges[i]),
                    "right": float(edges[i + 1]),
                }
                for i in range(len(centers))
            ],
            hovertemplate=(
                "<b>Bin</b>: [%{customdata.left:.3g}, %{customdata.right:.3g})<br>"
                "<b>Count</b>: %{y}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    # ✅ Always keep the ORIGINAL density line (in-scope KDE)
    in_kde = kde_counts(in_vals, grid, float(bin_width))
    fig.add_trace(
        go.Scatter(
            x=grid,
            y=in_kde,
            mode="lines",
            line=dict(color=KDE_IN_SCOPE_RGBA),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # ---- brush overlay bars (selected bin / temporary filter)
    if brush_vals.size and brush_counts is not None:
        fig.add_trace(
            go.Bar(
                x=centers,
                y=brush_counts,
                width=np.full(len(centers), float(bin_width)),
                marker=dict(color=HIST_BRUSH_RGBA),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # ---- selected country vlines
    for item in selection_store or []:
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
        clickmode="event",
    )
    return fig
