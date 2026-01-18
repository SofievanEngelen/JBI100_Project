from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric, pick_pcp_dims
from jbi100_app.state.selection_store import SelectedCountry
from jbi100_app.data.constants import BASE_GREY, FADED_GREY
from jbi100_app.data.attributes import ATTRIBUTE_METADATA, attribute_display_label, all_numeric_attributes


def _build_discrete_colorscale(code_to_colour: dict[int, str], cmax: int) -> list[list[object]]:
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
    color_by_first_axis: bool = False,
    theme: str = "light",
) -> go.Figure:

    # ------------------------------------------------------------
    # THEME
    # ------------------------------------------------------------
    template = "plotly_dark" if theme == "dark" else "plotly_white"

    PCP_BG = "rgba(0,0,0,0)"
    PCP_AXIS = "#ffffff" if theme == "dark" else "#374151"

    MARGIN = dict(l=60, r=60, t=50, b=25)

    # ------------------------------------------------------------
    # DIMENSIONS
    # ------------------------------------------------------------
    if dims_override:
        dims = [d for d in dims_override if d in df.columns][:max_dims]
    else:
        dims = pick_pcp_dims(df, max_dims=max_dims)

    if dims_override is not None and len(dims) < 2:
        fig = go.Figure()
        fig.add_annotation(
            text="Select at least 2 attributes in the sidebar to view the PCP",
            x=0.5, y=0.5, xref="paper", yref="paper",
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
    # NORMALISE DATA
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

    # ------------------------------------------------------------
    # SELECTED COUNTRIES (STORE NORMAL + LIGHT COLOURS)
    # ------------------------------------------------------------
    selected_names: list[str] = []
    sel_colour_map: dict[str, dict[str, str]] = {}

    for d in (selection_store or []):
        if not isinstance(d, dict):
            continue
        name = d.get("country_name")
        col = d.get("colour_rgb")
        col_light = d.get("colour_rgb_light") or col
        if not name or not col:
            continue
        if name not in sel_colour_map:
            selected_names.append(name)
            sel_colour_map[name] = {
                "normal": col,
                "light": col_light,
            }

    # ------------------------------------------------------------
    # SELECTED-ONLY FILTER
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
                font=dict(
                    size=18,
                    color=PCP_AXIS,
                ),
                align="center",
            )
            fig.update_layout(
                template=None,
                margin=MARGIN,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
                uirevision=uirevision,
            )
            return fig
        work = work[work["Country"].astype(str).isin(keep)].copy()

    # ------------------------------------------------------------
    # COLOUR UNIVERSE (SINGLE SOURCE OF TRUTH)
    # ------------------------------------------------------------
    countries = work["Country"].astype(str).to_numpy()

    # scope mask
    if in_mask is not None and isinstance(in_mask, pd.Series) and len(in_mask) == len(df):
        df_scope = pd.Series(in_mask.to_numpy(dtype=bool), index=df["Country"].astype(str))
        in_scope = np.array([bool(df_scope.get(c, True)) for c in countries], dtype=bool)
    else:
        in_scope = np.ones(len(work), dtype=bool)

    # brush mask
    brush_set = set(str(x) for x in (brush_countries or []) if x)
    if brush_set:
        in_brush = np.isin(countries, np.array(list(brush_set), dtype=str))
    else:
        in_brush = np.ones(len(work), dtype=bool)

    # ------------------------------------------------------------
    # PCP DIMENSIONS
    # ------------------------------------------------------------
    dimensions = []

    for c in dims:
        if c in ATTRIBUTE_METADATA.index:
            row = ATTRIBUTE_METADATA.loc[c]
            name = row["Display_name"]
            unit = row["Unit"]
        else:
            name = c
            unit = ""

        label = f"{name}<br>({unit})" if unit else name

        dimensions.append(
            dict(
                label=label,
                values=work[c].to_numpy(),
                range=[0, 1],
                tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                ticktext=["0", "0.2", "0.4", "0.6", "0.8", "1"],
            )
        )

    # ============================================================
    # MODE A: COLOR BY FIRST AXIS
    # ============================================================
    if color_by_first_axis:
        first_dim = dims[0]
        vals = work[first_dim].to_numpy(dtype=float)

        sentinel = -0.10
        active = in_scope & in_brush
        vals = np.where(active, vals, sentinel)

        colorscale = [
            [0, "rgb(68,1,84)"],
            [1.0, "rgb(253,231,37)"],
        ]

        fig = go.Figure(
            data=[
                go.Parcoords(
                    line=dict(
                        color=vals,
                        colorscale=colorscale,
                        cmin=sentinel,
                        cmax=1.0,
                        showscale=True,
                        colorbar=dict(title=attribute_display_label(first_dim, include_category=False)),
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
    # MODE B: DISCRETE COLOURS (THEME-AWARE SCOPE EMPHASIS)
    # ============================================================

    # ------------------------------------------------------------
    # Theme-aware greys
    # ------------------------------------------------------------
    if theme == "dark":
        PCP_IN_SCOPE_GREY = "rgb(230,230,230)"  # light lines
        PCP_OUT_SCOPE_GREY = "rgb(110,110,110)"  # dark lines
    else:
        PCP_IN_SCOPE_GREY = BASE_GREY
        PCP_OUT_SCOPE_GREY = FADED_GREY

    # ------------------------------------------------------------
    # Base codes
    # ------------------------------------------------------------
    codes = np.ones(len(work), dtype=int)

    is_selected = np.isin(countries, np.array(selected_names, dtype=str))

    # fade ONLY non-selected countries
    codes[~is_selected & ~in_scope] = 0
    codes[~is_selected & ~in_brush] = 0

    # ------------------------------------------------------------
    # Assign selected-country codes
    # (two states handled via colour mapping, not codes)
    # ------------------------------------------------------------
    name_to_code = {name: 2 + i for i, name in enumerate(selected_names)}

    for i, cname in enumerate(countries):
        code = name_to_code.get(cname)
        if code is not None:
            codes[i] = code

    # ------------------------------------------------------------
    # Colour mapping
    # ------------------------------------------------------------
    code_to_colour = {
        0: PCP_OUT_SCOPE_GREY,  # out-of-scope (dark in dark mode)
        1: PCP_IN_SCOPE_GREY,  # in-scope (light in dark mode)
    }

    # selected countries
    for i, name in enumerate(selected_names):
        code = 2 + i
        code_to_colour[code] = sel_colour_map[name]["normal"]

    # flip selected colours in dark mode
    if theme == "dark":
        for i, cname in enumerate(countries):
            if cname in sel_colour_map and not (in_scope[i] and in_brush[i]):
                code = name_to_code[cname]
                code_to_colour[code] = sel_colour_map[cname]["light"]

    # ------------------------------------------------------------
    # Build colourscale
    # ------------------------------------------------------------
    cmax = max(code_to_colour.keys())
    colourscale = _build_discrete_colorscale(code_to_colour, cmax=cmax)

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

