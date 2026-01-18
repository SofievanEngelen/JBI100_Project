from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.constants import BASE_GREY, FADED_GREY
from jbi100_app.data.attributes import attribute_display_label


def build_scatter_figure(
    df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
    in_mask: pd.Series,
    selection_store: list[SelectedCountry],
    brush_countries: list[str] | None = None,
    theme: str = "light",
) -> go.Figure:
    fig = go.Figure()
    template = "plotly_dark" if theme == "dark" else "plotly_white"

    if df is None or df.empty:
        fig.update_layout(template=template, margin=dict(l=0, r=0, t=0, b=0))
        return fig

    if not x_metric or not y_metric or x_metric not in df.columns or y_metric not in df.columns:
        fig.update_layout(template=template, margin=dict(l=0, r=0, t=0, b=0))
        return fig

    # ------------------------------------------------------------
    # Scope mask (continent/region): fade OUT-OF-SCOPE like filter
    # ------------------------------------------------------------
    in_mask_arr = (
        in_mask.to_numpy(dtype=bool)
        if in_mask is not None and len(in_mask) == len(df)
        else np.ones(len(df), dtype=bool)
    )

    # ------------------------------------------------------------
    # Scope + brush colouring
    # ------------------------------------------------------------
    brush_set = set(str(x) for x in (brush_countries or []) if x)
    brush_mask = (
        df["Country"].astype(str).isin(brush_set).to_numpy(dtype=bool)
        if brush_set
        else np.ones(len(df), dtype=bool)
    )

    active = in_mask_arr & brush_mask

    if theme == "dark":
        base_colours = np.where(
            active,
            "rgb(220,220,220)",  # active = bright
            "rgb(35,35,35)",  # inactive
        )
    else:
        base_colours = np.where(
            active,
            BASE_GREY,  # active
            FADED_GREY,  # inactive
        )

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
            # selected=dict(marker=dict(size=7)),
            # unselected=dict(marker=dict(opacity=0.03)),
            text=df["Country"],
            hovertemplate="<b>%{text}</b><br>"
            + attribute_display_label(x_metric)
            + ": %{x}<br>"
            + attribute_display_label(y_metric)
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
        ccol_light = item.get("colour_rgb_light")

        if not cname:
            continue

        row = df.loc[df["Country"] == cname]
        if row.empty:
            continue

        xv = pd.to_numeric(row.iloc[0][x_metric], errors="coerce")
        yv = pd.to_numeric(row.iloc[0][y_metric], errors="coerce")

        if not (np.isfinite(float(xv)) and np.isfinite(float(yv))):
            continue

        row_idx = row.index[0]

        in_brush = (not brush_set) or (cname in brush_set)
        active = bool(in_mask_arr[row_idx]) and in_brush

        marker_colour = ccol if active else ccol_light

        fig.add_trace(
            go.Scatter(
                x=[float(xv)],
                y=[float(yv)],
                mode="markers",
                marker=dict(
                    size=12,
                    color=marker_colour,
                    line=dict(width=1, color="rgba(0,0,0,0.35)"),
                ),
                hovertemplate="<b>" + cname + "</b><br>"
                + attribute_display_label(x_metric, include_category=False)
                + ": %{x}<br>"
                + attribute_display_label(y_metric, include_category=False)
                + ": %{y}<extra></extra>",
                showlegend=False,
            )
        )

    fig.update_layout(
        template=template,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(title=attribute_display_label(x_metric, include_category=False)),
        yaxis=dict(title=attribute_display_label(y_metric, include_category=False)),
        dragmode="lasso",
    )

    return fig
