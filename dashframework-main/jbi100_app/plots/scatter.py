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
    """
    Build a scatter plot comparing two numeric attributes.

    The plot supports:
    - geographic scoping (continent / region)
    - temporary brushing from other plots
    - explicit country selections with persistent colours

    Parameters
    ----------
    df:
        Source dataframe containing country-level data.
    x_metric:
        Attribute shown on the x-axis.
    y_metric:
        Attribute shown on the y-axis.
    in_mask:
        Boolean mask indicating which rows are in geographic scope.
    selection_store:
        List of explicitly selected countries with assigned colours.
    brush_countries:
        Optional list of temporarily brushed countries.
    theme:
        Visual theme ("light" or "dark").

    Returns
    -------
    go.Figure
        Configured Plotly scatter figure.
    """
    fig = go.Figure()
    template = "plotly_dark" if theme == "dark" else "plotly_white"

    # ------------------------------------------------------------
    # Defensive early exits
    # ------------------------------------------------------------
    if df is None or df.empty:
        fig.update_layout(template=template, margin=dict(l=0, r=0, t=0, b=0))
        return fig

    if (
        not x_metric
        or not y_metric
        or x_metric not in df.columns
        or y_metric not in df.columns
    ):
        fig.update_layout(template=template, margin=dict(l=0, r=0, t=0, b=0))
        return fig

    # ------------------------------------------------------------
    # Geographic scope mask
    # ------------------------------------------------------------
    in_scope_mask = (
        in_mask.to_numpy(dtype=bool)
        if in_mask is not None and len(in_mask) == len(df)
        else np.ones(len(df), dtype=bool)
    )

    # ------------------------------------------------------------
    # Temporary brush mask
    # ------------------------------------------------------------
    brush_set = {str(x) for x in (brush_countries or []) if x}

    brush_mask = (
        df["Country"].astype(str).isin(brush_set).to_numpy(dtype=bool)
        if brush_set
        else np.ones(len(df), dtype=bool)
    )

    active_mask = in_scope_mask & brush_mask

    # ------------------------------------------------------------
    # Base point colouring
    # ------------------------------------------------------------
    if theme == "dark":
        base_colours = np.where(
            active_mask,
            "rgb(220,220,220)",  # active
            "rgb(35,35,35)",     # inactive
        )
    else:
        base_colours = np.where(
            active_mask,
            BASE_GREY,   # active
            FADED_GREY,  # inactive
        )

    x_values = coerce_numeric(df[x_metric])
    y_values = coerce_numeric(df[y_metric])

    # ------------------------------------------------------------
    # Base scatter layer
    # ------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="markers",
            marker=dict(
                size=6,
                color=base_colours,
            ),
            text=df["Country"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                + attribute_display_label(x_metric)
                + ": %{x}<br>"
                + attribute_display_label(y_metric)
                + ": %{y}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    # ------------------------------------------------------------
    # Explicitly selected countries (overlay)
    # ------------------------------------------------------------
    for item in selection_store:
        country_name = item.get("country_name")
        colour = item.get("colour_rgb") or "rgb(180,35,24)"
        colour_light = item.get("colour_rgb_light")

        if not country_name:
            continue

        row = df.loc[df["Country"] == country_name]
        if row.empty:
            continue

        x_val = pd.to_numeric(row.iloc[0][x_metric], errors="coerce")
        y_val = pd.to_numeric(row.iloc[0][y_metric], errors="coerce")

        if not (np.isfinite(float(x_val)) and np.isfinite(float(y_val))):
            continue

        row_idx = row.index[0]

        in_brush = (not brush_set) or (country_name in brush_set)
        is_active = bool(in_scope_mask[row_idx]) and in_brush

        marker_colour = colour if is_active else colour_light

        fig.add_trace(
            go.Scatter(
                x=[float(x_val)],
                y=[float(y_val)],
                mode="markers",
                marker=dict(
                    size=12,
                    color=marker_colour,
                    line=dict(width=1, color="rgba(0,0,0,0.35)"),
                ),
                hovertemplate=(
                    "<b>" + country_name + "</b><br>"
                    + attribute_display_label(x_metric, include_category=False)
                    + ": %{x}<br>"
                    + attribute_display_label(y_metric, include_category=False)
                    + ": %{y}<extra></extra>"
                ),
                showlegend=False,
            )
        )

    # ------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------
    fig.update_layout(
        template=template,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            title=attribute_display_label(x_metric, include_category=False)
        ),
        yaxis=dict(
            title=attribute_display_label(y_metric, include_category=False)
        ),
        dragmode="lasso",
    )

    return fig
