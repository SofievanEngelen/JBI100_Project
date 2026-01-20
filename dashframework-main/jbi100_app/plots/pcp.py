# jbi100_app/plots/pcp.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.constants import BASE_GREY, FADED_GREY
from jbi100_app.data.attributes import (
    ATTRIBUTE_METADATA,
    attribute_display_label,
    all_numeric_attributes,
)


def _build_discrete_colourscale(
    code_to_colour: dict[int, str],
    cmax: int,
) -> list[list[object]]:
    """
    Build a discrete Plotly colourscale from integer colour codes.

    Each integer code maps to a flat colour band across its interval.
    """
    eps = 1e-6
    scale: list[list[object]] = []

    for code in range(0, cmax + 1):
        colour = code_to_colour.get(code)
        if colour is None:
            continue

        left = code / (cmax + 1)
        right = (code + 1) / (cmax + 1) - eps
        if right <= left:
            right = min(1.0 - eps, left + eps)

        scale.append([left, colour])
        scale.append([right, colour])

    scale.sort(key=lambda x: float(x[0]))

    if scale and float(scale[-1][0]) < 1.0:
        scale.append([1.0, scale[-1][1]])

    return scale


def build_pcp_figure(
    df: pd.DataFrame,
    ui_category: str | None,
    geo_scale: str,
    in_mask: pd.Series,
    selection_store: list[SelectedCountry],
    max_dims: int = 8,
    brush_countries: list[str] | None = None,
    uirevision: str | None = None,
    dims_override: list[str] | None = None,
    show_selected_only: bool = False,
    colour_by_first_axis: bool = False,
    theme: str = "light",
) -> go.Figure:
    """
    Build a Parallel Coordinates Plot (PCP).

    Supports:
    - dynamic attribute selection (up to max_dims)
    - geographic scoping (continent / region)
    - brushing from other plots
    - persistent country selection with colour identity
    - optional colouring by first axis

    Parameters
    ----------
    df:
        Source dataframe containing country-level data.
    ui_category:
        Currently selected UI category (kept for API consistency).
    geo_scale:
        Geographic scale ("global", "continent", "region").
    in_mask:
        Boolean mask indicating which rows are in geographic scope.
    selection_store:
        Selected countries with assigned colours.
    max_dims:
        Maximum number of dimensions to display.
    brush_countries:
        Optional list of temporarily brushed countries.
    uirevision:
        Plotly uirevision key for preserving interaction state.
    dims_override:
        Explicit list of dimensions selected via the UI.
    show_selected_only:
        Whether to restrict the plot to selected countries only.
    colour_by_first_axis:
        Whether to colour lines by the first dimension value.
    theme:
        Visual theme ("light" or "dark").

    Returns
    -------
    go.Figure
        Configured PCP figure.
    """

    # ------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------
    template = "plotly_dark" if theme == "dark" else "plotly_white"

    PCP_BG = "rgba(0,0,0,0)"
    PCP_AXIS = "#ffffff" if theme == "dark" else "#374151"
    MARGIN = dict(l=60, r=60, t=50, b=25)

    # ------------------------------------------------------------
    # Dimension selection
    # ------------------------------------------------------------
    if dims_override:
        dims = [d for d in dims_override if d in df.columns][:max_dims]
    else:
        dims = pick_pcp_dims(df, max_dims=max_dims)

    if dims_override is not None and len(dims) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Select at least 2 attributes in the sidebar to view the PCP",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18, color=PCP_AXIS),
            align="center",
        )
        fig.update_layout(template=template, margin=MARGIN)
        return fig

    if df is None or df.empty or len(dims) < 2:
        fig = go.Figure()
        fig.update_layout(template=template, margin=MARGIN)
        return fig

    # ------------------------------------------------------------
    # Normalise data to [0, 1]
    # ------------------------------------------------------------
    work = df[["Country"] + dims].copy()

    for col in dims:
        work[col] = coerce_numeric(work[col])
        median = work[col].median(skipna=True)
        work[col] = work[col].fillna(median)

        mn, mx = float(work[col].min()), float(work[col].max())
        if np.isfinite(mn) and np.isfinite(mx) and mx > mn:
            work[col] = (work[col] - mn) / (mx - mn)
        else:
            work[col] = 0.0

    # ------------------------------------------------------------
    # Selected countries (normal + light colours)
    # ------------------------------------------------------------
    selected_names: list[str] = []
    selection_colour_map: dict[str, dict[str, str]] = {}

    for item in (selection_store or []):
        if not isinstance(item, dict):
            continue

        name = item.get("country_name")
        colour = item.get("colour_rgb")
        colour_light = item.get("colour_rgb_light") or colour

        if not name or not colour:
            continue

        if name not in selection_colour_map:
            selected_names.append(name)
            selection_colour_map[name] = {
                "normal": colour,
                "light": colour_light,
            }

    # ------------------------------------------------------------
    # Selected-only filter
    # ------------------------------------------------------------
    if show_selected_only:
        keep = set(selected_names)
        if not keep:
            fig = go.Figure()
            fig.add_annotation(
                text="No countries selected",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=18, color=PCP_AXIS),
                align="center",
            )
            fig.update_layout(
                template=None,
                margin=MARGIN,
                paper_bgcolor=PCP_BG,
                plot_bgcolor=PCP_BG,
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
                uirevision=uirevision,
            )
            return fig

        work = work[work["Country"].astype(str).isin(keep)].copy()

    # ------------------------------------------------------------
    # Colour universe
    # ------------------------------------------------------------
    countries = work["Country"].astype(str).to_numpy()

    # Geographic scope mask
    if in_mask is not None and isinstance(in_mask, pd.Series) and len(in_mask) == len(df):
        scope_series = pd.Series(
            in_mask.to_numpy(dtype=bool),
            index=df["Country"].astype(str),
        )
        in_scope = np.array(
            [bool(scope_series.get(c, True)) for c in countries],
            dtype=bool,
        )
    else:
        in_scope = np.ones(len(work), dtype=bool)

    # Brush mask
    brush_set = {str(x) for x in (brush_countries or []) if x}
    in_brush = (
        np.isin(countries, np.array(list(brush_set), dtype=str))
        if brush_set
        else np.ones(len(work), dtype=bool)
    )

    # ------------------------------------------------------------
    # PCP dimensions
    # ------------------------------------------------------------
    dimensions = []

    for col in dims:
        if col in ATTRIBUTE_METADATA.index:
            meta = ATTRIBUTE_METADATA.loc[col]
            name = meta["Display_name"]
            unit = meta["Unit"]
        else:
            name = col
            unit = ""

        label = f"{name}<br>({unit})" if unit else name

        dimensions.append(
            dict(
                label=label,
                values=work[col].to_numpy(),
                range=[0, 1],
                tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                ticktext=["0", "0.2", "0.4", "0.6", "0.8", "1"],
            )
        )

    # ============================================================
    # Mode A: colour by first axis
    # ============================================================
    if colour_by_first_axis:
        first_dim = dims[0]
        values = work[first_dim].to_numpy(dtype=float)

        sentinel = -0.10
        active = in_scope & in_brush
        values = np.where(active, values, sentinel)

        colourscale = [
            [0, "rgb(68,1,84)"],
            [1.0, "rgb(253,231,37)"],
        ]

        fig = go.Figure(
            data=[
                go.Parcoords(
                    line=dict(
                        color=values,
                        colorscale=colourscale,
                        cmin=sentinel,
                        cmax=1.0,
                        showscale=True,
                        colorbar=dict(
                            title=attribute_display_label(
                                first_dim,
                                include_category=False,
                            )
                        ),
                    ),
                    dimensions=dimensions,
                    labelfont=dict(size=12, color=PCP_AXIS),
                    tickfont=dict(size=10, color=PCP_AXIS),
                    domain=dict(x=[0.05, 0.95]),
                )
            ]
        )

        fig.update_layout(
            template=template,
            margin=MARGIN,
            paper_bgcolor=PCP_BG,
            showlegend=False,
            uirevision=uirevision,
        )
        return fig

    # ============================================================
    # Mode B: discrete colours (theme-aware scope emphasis)
    # ============================================================
    if theme == "dark":
        PCP_IN_SCOPE_GREY = "rgb(230,230,230)"
        PCP_OUT_SCOPE_GREY = "rgb(110,110,110)"
    else:
        PCP_IN_SCOPE_GREY = BASE_GREY
        PCP_OUT_SCOPE_GREY = FADED_GREY

    codes = np.ones(len(work), dtype=int)
    is_selected = np.isin(countries, np.array(selected_names, dtype=str))

    # Fade non-selected countries only
    codes[~is_selected & ~in_scope] = 0
    codes[~is_selected & ~in_brush] = 0

    # Assign selected-country codes
    name_to_code = {name: 2 + i for i, name in enumerate(selected_names)}

    for i, cname in enumerate(countries):
        code = name_to_code.get(cname)
        if code is not None:
            codes[i] = code

    # ------------------------------------------------------------
    # Colour mapping
    # ------------------------------------------------------------
    code_to_colour: dict[int, str] = {
        0: PCP_OUT_SCOPE_GREY,
        1: PCP_IN_SCOPE_GREY,
    }

    for i, name in enumerate(selected_names):
        code_to_colour[2 + i] = selection_colour_map[name]["normal"]

    # Flip selected colours when inactive in dark mode
    if theme == "dark":
        for i, cname in enumerate(countries):
            if cname in selection_colour_map and not (in_scope[i] and in_brush[i]):
                code = name_to_code[cname]
                code_to_colour[code] = selection_colour_map[cname]["light"]

    # ------------------------------------------------------------
    # Build colourscale
    # ------------------------------------------------------------
    cmax = max(code_to_colour.keys())
    colourscale = _build_discrete_colourscale(code_to_colour, cmax=cmax)

    # ------------------------------------------------------------
    # PCP trace
    # ------------------------------------------------------------
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
                labelfont=dict(size=12, color=PCP_AXIS),
                tickfont=dict(size=10, color=PCP_AXIS),
                domain=dict(x=[0.05, 0.95]),
            )
        ]
    )

    fig.update_layout(
        template=template,
        margin=MARGIN,
        paper_bgcolor=PCP_BG,
        showlegend=False,
        uirevision=uirevision,
    )

    return fig
