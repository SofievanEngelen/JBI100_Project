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
from jbi100_app.plots.common import (
    coerce_numeric,
    kde_counts,
    prepare_hist_bins,
)
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.attributes import attribute_display_label


# =============================================================================
# Helpers
# =============================================================================

def _bin_edges(
    x_min: float,
    x_max: float,
    nbins: int,
) -> np.ndarray:
    """
    Generate evenly spaced histogram bin edges.
    """
    return np.linspace(float(x_min), float(x_max), max(1, int(nbins)) + 1)


def _countries_per_bin(
    values: np.ndarray,
    countries: list[str],
    edges: np.ndarray,
) -> list[list[str]]:
    """
    For each histogram bin, return the list of countries whose values
    fall into that bin.
    """
    out: list[list[str]] = [[] for _ in range(len(edges) - 1)]

    if values.size == 0:
        return out

    # right=False → bins are [left, right)
    indices = np.digitize(values, edges, right=False) - 1

    for i, bin_idx in enumerate(indices.tolist()):
        if 0 <= bin_idx < len(out):
            out[bin_idx].append(str(countries[i]))
        elif bin_idx == len(out):  # value equals the last edge
            out[-1].append(str(countries[i]))

    return out


# =============================================================================
# Histogram figure
# =============================================================================

def build_histogram_figure(
    df: pd.DataFrame,
    metric: str,
    nbins: int,
    geo_scale: str,
    in_mask: pd.Series,
    selection_store: list[SelectedCountry],
    brush_countries: list[str],
    theme: str = "light",
) -> go.Figure:
    """
    Build a histogram for a single numeric attribute.

    The histogram supports:
    - geographic scoping (continent / region)
    - brushing overlays
    - click-to-filter bin selection
    - selected country reference lines
    - an always-visible in-scope KDE curve

    Parameters
    ----------
    df:
        Source dataframe containing country-level data.
    metric:
        Attribute to visualise.
    nbins:
        Number of histogram bins.
    geo_scale:
        Current geographic scale.
    in_mask:
        Boolean mask indicating which rows are in scope.
    selection_store:
        Selected countries with assigned colours.
    brush_countries:
        Countries included in a temporary brush selection.
    theme:
        Visual theme ("light" or "dark").

    Returns
    -------
    go.Figure
        Configured Plotly histogram figure.
    """
    template = "plotly_dark" if theme == "dark" else "plotly_white"
    fig = go.Figure()

    # ------------------------------------------------------------
    # Safety checks
    # ------------------------------------------------------------
    if df is None or df.empty or not metric or metric not in df.columns:
        fig.update_layout(
            template=template,
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
        )
        return fig

    geo_scale = (geo_scale or "global").lower().strip()
    scope_active = (
        geo_scale in ("continent", "region")
        and in_mask is not None
        and len(in_mask) == len(df)
    )

    in_df = df.loc[in_mask].copy() if scope_active else df.copy()
    out_df = df.loc[~in_mask].copy() if scope_active else df.iloc[0:0].copy()

    # ------------------------------------------------------------
    # In-scope values
    # ------------------------------------------------------------
    in_vals = coerce_numeric(in_df[metric]).to_numpy(dtype=float)
    keep = np.isfinite(in_vals)
    in_vals = in_vals[keep]
    in_names = in_df.loc[keep, "Country"].astype(str).tolist()

    if in_vals.size == 0:
        fig.update_layout(
            template=template,
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
        )
        return fig

    # ------------------------------------------------------------
    # Out-of-scope values
    # ------------------------------------------------------------
    out_vals = coerce_numeric(out_df[metric]).to_numpy(dtype=float)
    out_vals = out_vals[np.isfinite(out_vals)]

    # ------------------------------------------------------------
    # Brush overlay values
    # ------------------------------------------------------------
    brush_vals = np.array([], dtype=float)

    if brush_countries:
        brush_df = df[df["Country"].isin(brush_countries)].copy()
        brush_vals = coerce_numeric(brush_df[metric]).to_numpy(dtype=float)
        brush_vals = brush_vals[np.isfinite(brush_vals)]

    # ------------------------------------------------------------
    # Compute consistent bins across all visible values
    # ------------------------------------------------------------
    all_vals = in_vals
    if out_vals.size:
        all_vals = np.concatenate([all_vals, out_vals])
    if brush_vals.size:
        all_vals = np.concatenate([all_vals, brush_vals])

    grid, bin_width, x_min, x_max = prepare_hist_bins(
        all_vals,
        bins=int(nbins or 30),
    )

    edges = _bin_edges(x_min, x_max, int(nbins or 30))
    centres = (edges[:-1] + edges[1:]) / 2.0

    # ------------------------------------------------------------
    # Bin counts
    # ------------------------------------------------------------
    in_counts, _ = np.histogram(in_vals, bins=edges)

    out_counts = None
    if out_vals.size:
        out_counts, _ = np.histogram(out_vals, bins=edges)

    brush_counts = None
    if brush_vals.size:
        brush_counts, _ = np.histogram(brush_vals, bins=edges)

    in_countries_per_bin = _countries_per_bin(
        in_vals,
        in_names,
        edges,
    )

    # ------------------------------------------------------------
    # Out-of-scope bars
    # ------------------------------------------------------------
    if scope_active and out_vals.size:
        fig.add_trace(
            go.Bar(
                x=centres,
                y=out_counts,
                width=np.full(len(centres), float(bin_width)),
                marker=dict(color=HIST_OUT_SCOPE_RGBA),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # ------------------------------------------------------------
    # In-scope bars (clickable)
    # ------------------------------------------------------------
    fig.add_trace(
        go.Bar(
            x=centres,
            y=in_counts,
            width=np.full(len(centres), float(bin_width)),
            marker=dict(color=HIST_IN_SCOPE_RGBA),
            customdata=[
                {
                    "countries": in_countries_per_bin[i],
                    "left": float(edges[i]),
                    "right": float(edges[i + 1]),
                }
                for i in range(len(centres))
            ],
            hovertemplate=(
                "<b>Bin</b>: [%{customdata.left:.3g}, %{customdata.right:.3g})<br>"
                "<b>Count</b>: %{y}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    # ------------------------------------------------------------
    # In-scope KDE (always shown)
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # Brush overlay bars
    # ------------------------------------------------------------
    if brush_vals.size and brush_counts is not None:
        fig.add_trace(
            go.Bar(
                x=centres,
                y=brush_counts,
                width=np.full(len(centres), float(bin_width)),
                marker=dict(color=HIST_BRUSH_RGBA),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # ------------------------------------------------------------
    # Selected country reference lines
    # ------------------------------------------------------------
    for item in selection_store or []:
        country_name = item.get("country_name")
        colour = item.get("colour_rgb") or "rgb(180,35,24)"

        if not country_name:
            continue

        row = df.loc[df["Country"] == country_name]
        if row.empty:
            continue

        value = pd.to_numeric(row.iloc[0][metric], errors="coerce")
        if value is None or not np.isfinite(float(value)):
            continue

        fig.add_vline(
            x=float(value),
            line_width=2,
            line_color=colour,
            opacity=0.95,
        )

    # ------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------
    fig.update_layout(
        template=template,
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        barmode="overlay",
        xaxis=dict(
            title=attribute_display_label(metric),
            range=[x_min, x_max],
        ),
        yaxis=dict(title="Count"),
        showlegend=False,
        clickmode="event",
    )

    return fig
