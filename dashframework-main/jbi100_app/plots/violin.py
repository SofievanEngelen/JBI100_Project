# jbi100_app/plots/violin.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.constants import (
    BASE_GREY_35,
    BASE_GREY_12,
    FADED_GREY_15,
    FADED_GREY_10,
)
from jbi100_app.data.attributes import attribute_display_label


def build_violin_figure(
    df: pd.DataFrame,
    metric: str,
    geo_scale: str,
    geo_scope: str | None,
    in_mask: pd.Series,
    selection_store: list[SelectedCountry],
    theme: str = "light",
) -> go.Figure:
    """
    Build a horizontal violin plot showing:
    - the global distribution (always)
    - the selected region / continent distribution (if active),
      stacked above the global one
    - vertical reference lines for selected countries
    """
    template = "plotly_dark" if theme == "dark" else "plotly_white"
    fig = go.Figure()

    # ------------------------------------------------------------
    # Defensive exit
    # ------------------------------------------------------------
    if df is None or df.empty or not metric or metric not in df.columns:
        fig.update_layout(template=template)
        return fig

    geo_scale = (geo_scale or "global").lower().strip()

    scope_active = (
        geo_scale in ("continent", "region")
        and in_mask is not None
        and len(in_mask) == len(df)
        and in_mask.any()
        and (~in_mask).any()
    )

    # ------------------------------------------------------------
    # Prepare data
    # ------------------------------------------------------------
    global_vals = coerce_numeric(df[metric]).to_numpy(dtype=float)
    global_vals = global_vals[np.isfinite(global_vals)]

    if scope_active:
        scope_vals = coerce_numeric(df.loc[in_mask, metric]).to_numpy(dtype=float)
        scope_vals = scope_vals[np.isfinite(scope_vals)]
    else:
        scope_vals = np.array([])

    if global_vals.size == 0:
        fig.update_layout(template=template)
        return fig

    global_label = "Global"
    scope_label = f"{geo_scale.capitalize()}:<br> {geo_scope.capitalize() if geo_scale in ['continent', 'region'] else ''}"

    # ------------------------------------------------------------
    # Global violin
    # ------------------------------------------------------------
    fig.add_trace(
        go.Violin(
            x=global_vals,
            y=[global_label] * len(global_vals),
            orientation="h",
            box_visible=True,
            points=False,
            line_color=BASE_GREY_35,
            fillcolor=BASE_GREY_12,
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # ------------------------------------------------------------
    # Regional / continent violin (on top)
    # ------------------------------------------------------------
    if scope_active and scope_vals.size > 0:
        fig.add_trace(
            go.Violin(
                x=scope_vals,
                y=[scope_label] * len(scope_vals),
                orientation="h",
                box_visible=True,
                points=False,
                line_color=BASE_GREY_35,
                fillcolor=BASE_GREY_12,
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # ------------------------------------------------------------
    # Selected country reference lines
    # ------------------------------------------------------------
    for item in selection_store:
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
        xaxis=dict(title=attribute_display_label(metric)),
        yaxis=dict(
            title=None,
            categoryorder="array",
            categoryarray=[scope_label, global_label]
            if scope_active
            else [global_label],
        ),
        showlegend=False,
    )

    return fig

