# jbi100_app/plots/radar.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import pick_pcp_dims
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.attributes import attribute_display_label


def _rgb_to_rgba(rgb: str, a: float) -> str:
    s = (rgb or "").strip()
    if s.startswith("rgba("):
        return s
    if s.startswith("rgb(") and s.endswith(")"):
        inside = s[4:-1]
        parts = [p.strip() for p in inside.split(",")]
        if len(parts) == 3:
            return f"rgba({parts[0]},{parts[1]},{parts[2]},{a})"
    return f"rgba(180,35,24,{a})"


def _wrap_label(s: str, max_chars: int = 14) -> str:
    """
    Wrap long labels onto 2 lines using <br> so polar tick labels don't get clipped.
    """
    s = (s or "").strip()
    if len(s) <= max_chars:
        return s

    parts = s.split()
    if len(parts) <= 1:
        return s[:max_chars] + "…"

    mid = max(1, len(parts) // 2)
    return " ".join(parts[:mid]) + "<br>" + " ".join(parts[mid:])


def build_radar_figure(
    df: pd.DataFrame,
    ui_category: str | None,
    selection_store: list[SelectedCountry],
    dims_override: list[str] | None = None,
) -> go.Figure:
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
            template="plotly_white",
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    # Choose dimensions (max 8)
    if dims_override:
        dims = [d for d in dims_override if d in df.columns][:8]
    else:
        dims = pick_pcp_dims(df, max_dims=8)

    # If user is explicitly controlling dims via sidebar, warn when too few
    if dims_override is not None and len(dims) < 3:
        fig = go.Figure()
        fig.add_annotation(
            text="Select at least 3 attributes in the sidebar to view the radar plot",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18, color="#374151"),
            align="center",
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    if len(dims) < 3:
        fig = go.Figure()
        fig.add_annotation(
            text="Not enough numeric attributes for radar plot",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=16, color="#374151"),
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(l=0, r=0, t=0, b=0),
            title=None,
            showlegend=False,
        )
        return fig

    mins, maxs = {}, {}
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

    def norm(v, d):
        return (float(v) - mins[d]) / (maxs[d] - mins[d])

    theta = [_wrap_label(attribute_display_label(d), max_chars=14) for d in dims]
    theta_closed = theta + [theta[0]]

    fig = go.Figure()

    for item in selection_store:
        cname = item.get("country_name")
        base_rgb = item.get("colour_rgb") or "rgb(180,35,24)"
        if not cname:
            continue

        row = df.loc[df["Country"] == cname]
        if row.empty:
            continue

        r = []
        ok = True
        for d in dims:
            v = pd.to_numeric(row.iloc[0][d], errors="coerce")
            if v is None or not np.isfinite(float(v)):
                ok = False
                break
            r.append(norm(v, d))
        if not ok:
            continue

        r_closed = r + [r[0]]

        fig.add_trace(
            go.Scatterpolar(
                r=r_closed,
                theta=theta_closed,
                mode="lines",
                line=dict(color=_rgb_to_rgba(base_rgb, 0.95), width=2),
                fill="toself",
                fillcolor=_rgb_to_rgba(base_rgb, 0.25),
                showlegend=False,
            )
        )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=30, b=40),  # ✅ extra breathing room prevents cut-off
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
                tickfont=dict(size=10),  # ✅ helps fit 8 labels
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig
