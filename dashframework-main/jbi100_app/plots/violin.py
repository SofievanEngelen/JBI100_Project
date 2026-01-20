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
    in_mask: pd.Series,
    selection_store: list[SelectedCountry],
    theme: str = "light",
) -> go.Figure:
    """
    Build a horizontal violin plot for a single metric.

    The plot shows:
    - the in-scope distribution (continent / region or global)
    - an optional out-of-scope distribution (faded), if applicable
    - vertical reference lines for selected countries

    Parameters
    ----------
    df:
        Source dataframe containing country-level data.
    metric:
        Column name to visualise.
    geo_scale:
        Current geographic scale ("global", "continent", or "region").
    in_mask:
        Boolean mask indicating which rows are in scope.
    selection_store:
        List of selected countries with assigned colours.
    theme:
        Visual theme ("light" or "dark").

    Returns
    -------
    go.Figure
        A configured Plotly violin plot.
    """
    template = "plotly_dark" if theme == "dark" else "plotly_white"

    fig = go.Figure()

    # Defensive early exit for invalid inputs
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

    # Split in-scope and out-of-scope data
    in_df = df.loc[in_mask].copy() if scope_active else df.copy()
    out_df = df.loc[~in_mask].copy() if scope_active else df.iloc[0:0].copy()

    # Coerce and clean in-scope values
    in_vals = coerce_numeric(in_df[metric]).to_numpy(dtype=float)
    in_vals = in_vals[np.isfinite(in_vals)]

    if in_vals.size == 0:
        fig.update_layout(
            template=template,
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
        )
        return fig

    # Coerce and clean out-of-scope values
    out_vals = coerce_numeric(out_df[metric]).to_numpy(dtype=float)
    out_vals = out_vals[np.isfinite(out_vals)]

    # --------------------------------------------------------------
    # Out-of-scope distribution (faded)
    # --------------------------------------------------------------
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

    # --------------------------------------------------------------
    # In-scope distribution
    # --------------------------------------------------------------
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

    # --------------------------------------------------------------
    # Selected country reference lines
    # --------------------------------------------------------------
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

    # --------------------------------------------------------------
    # Layout
    # --------------------------------------------------------------
    fig.update_layout(
        template=template,
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        xaxis=dict(title=attribute_display_label(metric)),
        yaxis=dict(showticklabels=False),
        showlegend=False,
    )

    return fig
