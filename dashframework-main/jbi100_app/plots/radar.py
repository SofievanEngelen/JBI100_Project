# jbi100_app/plots/radar.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import pick_pcp_dims
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.attributes import attribute_display_label


def _rgb_to_rgba(rgb: str, alpha: float) -> str:
    """
    Convert an RGB colour string to RGBA with the given alpha.

    Falls back to a default red if parsing fails.
    """
    s = (rgb or "").strip()

    if s.startswith("rgba("):
        return s

    if s.startswith("rgb(") and s.endswith(")"):
        inside = s[4:-1]
        parts = [p.strip() for p in inside.split(",")]
        if len(parts) == 3:
            return f"rgba({parts[0]},{parts[1]},{parts[2]},{alpha})"

    return f"rgba(180,35,24,{alpha})"


def _wrap_label(label: str, max_chars: int = 14) -> str:
    """
    Wrap long axis labels onto two lines using <br> so that
    polar tick labels do not get clipped.
    """
    label = (label or "").strip()

    if len(label) <= max_chars:
        return label

    parts = label.split()
    if len(parts) <= 1:
        return label[:max_chars] + "…"

    mid = max(1, len(parts) // 2)
    return " ".join(parts[:mid]) + "<br>" + " ".join(parts[mid:])


def build_radar_figure(
    df: pd.DataFrame,
    ui_category: str | None,
    selection_store: list[SelectedCountry],
    dims_override: list[str] | None = None,
    theme: str = "light",
) -> go.Figure:
    """
    Build a radar (spider) plot comparing multiple countries across attributes.

    Requirements:
    - At least 3 selected countries
    - At least 3 numeric attributes (max 8)

    Parameters
    ----------
    df:
        Source dataframe containing country-level data.
    ui_category:
        Currently selected UI category (unused here but kept for API consistency).
    selection_store:
        Selected countries with assigned colours.
    dims_override:
        Optional explicit list of attributes to plot.
    theme:
        Visual theme ("light" or "dark").

    Returns
    -------
    go.Figure
        Configured Plotly radar figure.
    """
    template = "plotly_dark" if theme == "dark" else "plotly_white"

    # ------------------------------------------------------------
    # Guard: minimum number of selected countries
    # ------------------------------------------------------------
    if df is None or df.empty or len(selection_store) < 3:
        fig = go.Figure()
        fig.add_annotation(
            text="Select at least 3 countries to view the radar plot",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18, color="#374151"),
            align="center",
        )
        fig.update_layout(
            template=template,
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    # ------------------------------------------------------------
    # Choose dimensions (maximum of 8)
    # ------------------------------------------------------------
    if dims_override:
        dims = [d for d in dims_override if d in df.columns][:8]
    else:
        dims = pick_pcp_dims(df, max_dims=8)

    # Explicit user-controlled dimensions but too few
    if dims_override is not None and len(dims) < 3:
        fig = go.Figure()
        fig.add_annotation(
            text="Select at least 3 attributes to view the radar plot",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18, color="var(--text-main)"),
            align="center",
        )
        fig.update_layout(
            template=template,
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    # Not enough numeric attributes available
    if len(dims) < 3:
        fig = go.Figure()
        fig.add_annotation(
            text="Not enough numeric attributes for radar plot",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=16, color="var(--text-main)"),
            align="center",
        )
        fig.update_layout(
            template=template,
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
            showlegend=False,
        )
        return fig

    # ------------------------------------------------------------
    # Normalisation bounds per dimension
    # ------------------------------------------------------------
    mins: dict[str, float] = {}
    maxs: dict[str, float] = {}

    for d in dims:
        vals = pd.to_numeric(df[d], errors="coerce")
        vals = vals[np.isfinite(vals)]

        if vals.size == 0:
            mins[d], maxs[d] = 0.0, 1.0
        else:
            mn, mx = float(vals.min()), float(vals.max())
            if mx <= mn:
                mx = mn + 1.0
            mins[d], maxs[d] = mn, mx

    def normalise(value: float, dim: str) -> float:
        return (float(value) - mins[dim]) / (maxs[dim] - mins[dim])

    # Axis labels
    theta = [
        _wrap_label(attribute_display_label(d), max_chars=14)
        for d in dims
    ]
    theta_closed = theta + [theta[0]]

    fig = go.Figure()

    # ------------------------------------------------------------
    # Country traces
    # ------------------------------------------------------------
    for item in selection_store:
        country_name = item.get("country_name")
        base_rgb = item.get("colour_rgb") or "rgb(180,35,24)"

        if not country_name:
            continue

        country_key = country_name.strip().upper()
        row = df.loc[df["_CountryKey"] == country_key]

        if row.empty:
            continue

        values: list[float] = []
        valid = True

        for d in dims:
            v = pd.to_numeric(row.iloc[0][d], errors="coerce")
            if v is None or not np.isfinite(float(v)):
                valid = False
                break
            values.append(normalise(v, d))

        if not valid:
            continue

        values_closed = values + [values[0]]

        fig.add_trace(
            go.Scatterpolar(
                r=values_closed,
                theta=theta_closed,
                mode="lines",
                line=dict(
                    color=_rgb_to_rgba(base_rgb, 0.95),
                    width=2,
                ),
                fill="toself",
                fillcolor=_rgb_to_rgba(base_rgb, 0.25),
                showlegend=False,
            )
        )

    # ------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------
    fig.update_layout(
        template=template,
        margin=dict(l=40, r=40, t=30, b=40),
        title=None,
        showlegend=False,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickvals=[0, 0.5, 1],
                tickfont=dict(size=10),
            ),
            angularaxis=dict(
                tickfont=dict(size=10),
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    return fig
