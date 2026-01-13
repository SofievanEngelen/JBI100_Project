from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric, pretty_metric
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.constants import BASE_GREY, FADED_GREY


def build_scatter_figure(
    df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
    in_mask: pd.Series,
    selection_store: list[SelectedCountry],
    brush_countries: list[str] | None = None,
) -> go.Figure:
    fig = go.Figure()

    if df is None or df.empty:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0))
        return fig

    if not x_metric or not y_metric or x_metric not in df.columns or y_metric not in df.columns:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0))
        return fig

    # ------------------------------------------------------------
    # Scope mask (continent/region): fade OUT-OF-SCOPE like filter
    # ------------------------------------------------------------
    in_mask_arr = (
        in_mask.to_numpy(dtype=bool)
        if in_mask is not None and len(in_mask) == len(df)
        else np.ones(len(df), dtype=bool)
    )

    # start with geo-scope fade
    base_colours = np.where(in_mask_arr, BASE_GREY, FADED_GREY)

    # ------------------------------------------------------------
    # PCP brush overlay (fade NON-brushed points, like filter)
    # - if brush exists, keep brushed points at their current base colour
    #   and fade the rest.
    # ------------------------------------------------------------
    brush_set = set(str(x) for x in (brush_countries or []) if x)
    if brush_set:
        brush_mask = df["Country"].astype(str).isin(brush_set).to_numpy(dtype=bool)

        # combine: "active" = in-scope AND brushed
        active = brush_mask
        base_colours = np.where(active, base_colours, FADED_GREY)

    x = coerce_numeric(df[x_metric])
    y = coerce_numeric(df[y_metric])

    # ------------------------------------------------------------
    # Base scatter layer
    # ------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="markers",
            marker=dict(
                size=6,
                color=base_colours,
            ),
            selected=dict(marker=dict(size=7)),
            unselected=dict(marker=dict(opacity=0.15)),
            text=df["Country"],
            hovertemplate="<b>%{text}</b><br>"
            + pretty_metric(x_metric)
            + ": %{x}<br>"
            + pretty_metric(y_metric)
            + ": %{y}<extra></extra>",
            showlegend=False,
        )
    )

    # ------------------------------------------------------------
    # Explicitly selected countries (coloured)
    # ------------------------------------------------------------
    for item in selection_store:
        cname = item.get("country_name")
        ccol = item.get("colour_rgb") or "rgb(180,35,24)"
        if not cname:
            continue

        row = df.loc[df["Country"] == cname]
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
                marker=dict(
                    size=12,
                    color=ccol,
                    line=dict(width=1, color="rgba(0,0,0,0.35)"),
                ),
                hovertemplate="<b>" + cname + "</b><br>"
                + pretty_metric(x_metric)
                + ": %{x}<br>"
                + pretty_metric(y_metric)
                + ": %{y}<extra></extra>",
                showlegend=False,
            )
        )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(title=pretty_metric(x_metric)),
        yaxis=dict(title=pretty_metric(y_metric)),
        dragmode="lasso",
    )

    return fig
