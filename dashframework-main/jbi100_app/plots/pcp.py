from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims, pretty_metric
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.constants import BASE_GREY, FADED_GREY


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _build_discrete_colorscale(code_to_colour: dict[int, str], cmax: int) -> list[list[object]]:
    """
    Build a piecewise-constant Plotly colorscale for integer codes.

    Each integer maps to a flat colour segment.
    """
    eps = 1e-6
    scale: list[list[object]] = []

    for code in range(0, cmax + 1):
        col = code_to_colour.get(code)
        if col is None:
            continue

        left = code / (cmax + 1)
        right = (code + 1) / (cmax + 1) - eps
        if right <= left:
            right = min(1.0 - eps, left + eps)

        scale.append([left, col])
        scale.append([right, col])

    scale.sort(key=lambda x: float(x[0]))
    if scale and float(scale[-1][0]) < 1.0:
        scale.append([1.0, scale[-1][1]])

    return scale


def _parcoords_dimensions(work: pd.DataFrame, dims: list[str]) -> list[dict]:
    return [{"label": pretty_metric(c), "values": work[c].to_numpy()} for c in dims]


def _single_color_scale(rgb: str) -> list[list[object]]:
    # flat colorscale
    return [[0.0, rgb], [1.0, rgb]]


# ---------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------
def build_pcp_figure(
    df: pd.DataFrame,
    ui_category: str | None,
    geo_scale: str,                 # kept for compatibility
    in_mask: pd.Series,             # kept for compatibility
    selection_store: list[SelectedCountry],
    max_dims: int = 8,
    brush_countries: list[str] | None = None,
    uirevision: str | None = None,
    dims_override: list[str] | None = None,
    show_selected_only: bool = False,
    color_by_first_axis: bool = False,   # ✅ NEW
) -> go.Figure:
    # ------------------------------------------------------------
    # Dimensions
    # ------------------------------------------------------------
    if dims_override:
        dims = [d for d in dims_override if d in df.columns][:max_dims]
    else:
        dims = pick_pcp_dims(df, ui_category, max_dims=max_dims)

    MARGIN = dict(l=60, r=60, t=50, b=25)

    if dims_override is not None and len(dims) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Select at least 2 attributes in the sidebar to view the PCP",
            x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=18, color="#374151"),
            align="center",
        )
        fig.update_layout(
            template="plotly_white",
            margin=MARGIN,
            title=None,
            showlegend=False,
        )
        return fig

    if df is None or df.empty or len(dims) < 2:
        fig = go.Figure()
        fig.update_layout(template="plotly_white", margin=MARGIN, uirevision=uirevision)
        return fig

    # ------------------------------------------------------------
    # Normalize values to 0..1 (PCP displayed scale)
    # ------------------------------------------------------------
    work = df[["Country"] + dims].copy()
    for c in dims:
        work[c] = coerce_numeric(work[c])
        med = work[c].median(skipna=True)
        work[c] = work[c].fillna(med)

        mn, mx = float(work[c].min()), float(work[c].max())
        if np.isfinite(mn) and np.isfinite(mx) and mx > mn:
            work[c] = (work[c] - mn) / (mx - mn)
        else:
            work[c] = 0.0

    countries = work["Country"].astype(str).to_numpy()
    brush_set = set(str(x) for x in (brush_countries or []) if x)

    # ------------------------------------------------------------
    # ✅ Selected-only visibility mode (works in BOTH color modes)
    # ------------------------------------------------------------
    selected_names: list[str] = []
    sel_colour_map: dict[str, str] = {}
    for d in (selection_store or []):
        if not isinstance(d, dict):
            continue
        n = d.get("country_name")
        c = d.get("colour_rgb")
        if not n or not c:
            continue
        if n not in sel_colour_map:
            selected_names.append(n)
            sel_colour_map[n] = c

    if show_selected_only:
        keep = set(selected_names)
        if not keep:
            # show nothing
            fig = go.Figure()
            fig.update_layout(template="plotly_white", margin=MARGIN, uirevision=uirevision)
            return fig
        work = work[work["Country"].astype(str).isin(keep)].copy()
        countries = work["Country"].astype(str).to_numpy()

    dimensions = _parcoords_dimensions(work, dims)

    # ------------------------------------------------------------
    # ✅ MODE A: Color by first axis (continuous colorscale)
    # - If there is a brush filter, keep non-brushed in a faint grey trace
    # - Draw brushed (or all) with a colorscale based on dims[0]
    # - Then draw selected countries on top using their fixed colours
    # ------------------------------------------------------------
    if color_by_first_axis:
        first_dim = dims[0]

        # base continuous colour = first axis (0..1)
        color_vals = work[first_dim].to_numpy(dtype=float)

        # If a brush filter exists: push non-brushed to a sentinel below the scale
        # and add a grey segment at the bottom of the colorscale.
        brush_set = set(str(x) for x in (brush_countries or []) if x)
        if brush_set:
            countries = work["Country"].astype(str).to_numpy()
            in_brush = np.isin(countries, np.array(list(brush_set), dtype=str))

            # sentinel for "out of brush"
            sentinel = -0.10
            color_vals = np.where(in_brush, color_vals, sentinel)

            # colorscale with a grey band for sentinel, then Viridis for 0..1
            # cmin=-0.10, cmax=1.0 => sentinel maps to bottom
            colorscale = [
                [0.0, FADED_GREY],
                [0.0909, FADED_GREY],  # ~ (-0.10 -> 0) region
                [0.0910, "rgb(68,1,84)"],  # viridis start (approx)
                [1.0, "rgb(253,231,37)"],  # viridis end (approx)
            ]
            cmin = sentinel
            cmax = 1.0
            showscale = True
        else:
            colorscale = "Viridis"
            cmin = 0.0
            cmax = 1.0
            showscale = True

        dimensions = [{"label": pretty_metric(c), "values": work[c].to_numpy()} for c in dims]

        fig = go.Figure(
            data=[
                go.Parcoords(
                    line=dict(
                        color=color_vals,
                        colorscale=colorscale,
                        cmin=cmin,
                        cmax=cmax,
                        showscale=showscale,
                        colorbar=dict(title=pretty_metric(first_dim)),
                    ),
                    dimensions=dimensions,
                    labelfont=dict(size=12),
                    tickfont=dict(size=10),
                    domain=dict(x=[0.05, 0.95]),
                )
            ]
        )

        fig.update_layout(
            template="plotly_white",
            margin=MARGIN,
            title=None,
            showlegend=False,
            uirevision=uirevision,
        )
        return fig

    # ------------------------------------------------------------
    # MODE B (existing): Discrete colouring (brush fade + selected colours)
    # ------------------------------------------------------------
    codes = np.ones(len(work), dtype=int)

    if brush_set:
        brushed = np.isin(countries, np.array(list(brush_set), dtype=str))
        codes[~brushed] = 0

    name_to_code = {name: 2 + i for i, name in enumerate(selected_names)}
    for i, cname in enumerate(countries.tolist()):
        code = name_to_code.get(cname)
        if code is not None:
            codes[i] = code

    k = len(selected_names)
    cmax = 2 + max(0, k - 1)

    code_to_colour: dict[int, str] = {
        0: FADED_GREY,
        1: BASE_GREY,
    }
    for i, name in enumerate(selected_names):
        code_to_colour[2 + i] = sel_colour_map[name]

    colourscale = _build_discrete_colorscale(code_to_colour, cmax=cmax)

    fig = go.Figure(
        data=[
            go.Parcoords(
                line=dict(
                    color=codes.astype(float),
                    colorscale=colourscale,
                    cmin=0,
                    cmax=cmax,
                    showscale=False,
                ),
                dimensions=dimensions,
                labelfont=dict(size=12),
                tickfont=dict(size=10),
                domain=dict(x=[0.05, 0.95]),
            )
        ]
    )

    fig.update_layout(
        template="plotly_white",
        margin=MARGIN,
        title=None,
        showlegend=False,
        uirevision=uirevision,
    )

    return fig
