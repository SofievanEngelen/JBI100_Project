from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.plots.common import coerce_numeric
from jbi100_app.data.constants import (
    COLOUR_SCALE,
    DIVERGING_COLOUR_SCALE,
    SMALL_COUNTRY_AREA_KM2,
)
from jbi100_app.data.attributes import (
    attribute_display_label,
    is_diverging_attribute,
)
from jbi100_app.state.selection_store import SelectedCountry


_TRANSPARENT = "rgba(0,0,0,0)"


# =============================================================================
# Helpers
# =============================================================================

def _key(name: object) -> str:
    """
    Normalise a country name into an uppercase key.

    Used to match against internal country keys.
    """
    if not isinstance(name, str):
        return ""
    return name.strip().upper()


# =============================================================================
# Map figure
# =============================================================================

def build_map_figure(
    df: pd.DataFrame,
    metric: str,
    geo_scale: str,
    in_mask: pd.Series | None,
    selection_store: list[SelectedCountry],
    brush_country_keys: list[str] | None = None,
    theme: str = "light",
) -> go.Figure:
    """
    Build a choropleth world map for a given metric.

    The map supports:
    - geographic scoping (continent / region)
    - brushing from other plots
    - explicit country selection with outline emphasis
    - diverging and sequential colour scales

    Parameters
    ----------
    df:
        Source dataframe containing country-level data.
    metric:
        Attribute to visualise.
    geo_scale:
        Current geographic scale.
    in_mask:
        Boolean mask indicating which rows are in scope.
    selection_store:
        Selected countries with assigned colours.
    brush_country_keys:
        Optional list of brushed country keys.
    theme:
        Visual theme ("light" or "dark").

    Returns
    -------
    go.Figure
        Configured Plotly map figure.
    """
    fig = go.Figure()
    template = "plotly_dark" if theme == "dark" else "plotly_white"

    # ------------------------------------------------------------
    # Theme-aware out-of-scope styling
    # ------------------------------------------------------------
    if theme == "dark":
        out_of_scope_fill = "rgb(31, 31, 31)"
        out_of_scope_line = "rgba(130,130,130,0.6)"
    else:
        out_of_scope_fill = "white"
        out_of_scope_line = "rgba(180,180,180,0.6)"

    # ------------------------------------------------------------
    # Safety checks
    # ------------------------------------------------------------
    if df is None or df.empty or not metric or metric not in df.columns:
        fig.update_layout(
            template=template,
            margin=dict(l=0, r=0, t=0, b=0),
        )
        return fig

    plot_df = df.copy()
    plot_df["_z"] = coerce_numeric(plot_df[metric])

    if in_mask is None or len(in_mask) != len(plot_df):
        in_mask = pd.Series(True, index=plot_df.index)

    brush_set = set(brush_country_keys or [])

    # ------------------------------------------------------------
    # Colour scale logic (metadata-driven)
    # ------------------------------------------------------------
    z_visible = plot_df.loc[in_mask, "_z"]
    z_visible = z_visible[np.isfinite(z_visible)]

    use_diverging = is_diverging_attribute(metric)

    if use_diverging:
        if z_visible.empty:
            vmax_abs = 1.0
        else:
            vmax_abs = float(np.nanmax(np.abs(z_visible)))
            if not np.isfinite(vmax_abs) or vmax_abs == 0:
                vmax_abs = 1.0

        coloraxis = dict(
            colorscale=DIVERGING_COLOUR_SCALE,
            cmin=-vmax_abs,
            cmax=vmax_abs,
            cmid=0,
            colorbar=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=1.02,
                yanchor="bottom",
                len=0.7,
                thickness=14,
            ),
        )

    else:
        if z_visible.empty:
            vmin, vmax = 0.0, 1.0
        elif z_visible.nunique() == 1:
            v = float(z_visible.iloc[0])
            vmin, vmax = v - 1.0, v + 1.0
        else:
            vmin, vmax = np.percentile(z_visible, [2, 98])
            vmin, vmax = float(vmin), float(vmax)

            if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
                vmin = float(z_visible.min())
                vmax = float(z_visible.max())

        coloraxis = dict(
            colorscale=COLOUR_SCALE,
            cmin=vmin,
            cmax=vmax,
            colorbar=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=1.02,
                yanchor="bottom",
                len=0.7,
                thickness=14,
            ),
        )

    # ------------------------------------------------------------
    # 1) Base choropleth (owns colour scale)
    # ------------------------------------------------------------
    fig.add_trace(
        go.Choropleth(
            locations=plot_df["_PLOTLY_NAME"],
            locationmode="country names",
            z=plot_df["_z"],
            coloraxis="coloraxis",
            marker_line_color="rgba(255,255,255,0.35)",
            marker_line_width=0.5,
            text=plot_df["Country"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                + attribute_display_label(metric)
                + ": %{z:,.3g}<extra></extra>"
            ),
        )
    )

    # ------------------------------------------------------------
    # 2) Out-of-scope countries → white-out overlay
    # ------------------------------------------------------------
    out_mask = ~in_mask

    if out_mask.any():
        fig.add_trace(
            go.Choropleth(
                locations=plot_df.loc[out_mask, "_PLOTLY_NAME"],
                locationmode="country names",
                z=[1] * int(out_mask.sum()),
                colorscale=[
                    [0, out_of_scope_fill],
                    [1, out_of_scope_fill],
                ],
                showscale=False,
                marker_line_color=out_of_scope_line,
                marker_line_width=0.5,
                hoverinfo="skip",
            )
        )

    # ------------------------------------------------------------
    # 3) Selected countries → outline emphasis
    # ------------------------------------------------------------
    for item in selection_store:
        country_name = item.get("country_name")
        if not country_name:
            continue

        country_key = _key(country_name)
        row = plot_df.loc[plot_df["_CountryKey"] == country_key]
        if row.empty:
            continue

        row = row.iloc[0]
        plotly_name = row.get("_PLOTLY_NAME")
        iso3 = row.get("_ISO3")

        # Geographic scope
        in_geo = True
        if in_mask is not None:
            m = plot_df["_CountryKey"] == country_key
            if m.any():
                in_geo = bool(in_mask.loc[m].iloc[0])

        # Brush scope
        in_filter = (not brush_set) or (country_key in brush_set)
        in_scope = in_geo and in_filter

        outline_colour = (
            item["colour_rgb"]
            if in_scope
            else item["colour_rgb_light"]
        )

        area = pd.to_numeric(row.get("land_area_km2"), errors="coerce")
        is_small = bool(
            np.isfinite(area) and area < SMALL_COUNTRY_AREA_KM2
        )

        # Small countries → point outline
        if is_small and isinstance(iso3, str):
            fig.add_trace(
                go.Scattergeo(
                    locations=[iso3],
                    locationmode="ISO-3",
                    mode="markers",
                    marker=dict(
                        size=12,
                        color=_TRANSPARENT,
                        line=dict(width=2.2, color=outline_colour),
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )
        else:
            # Normal countries → boundary outline
            fig.add_trace(
                go.Choropleth(
                    locations=[plotly_name],
                    locationmode="country names",
                    z=[1],
                    colorscale=[
                        [0, _TRANSPARENT],
                        [1, _TRANSPARENT],
                    ],
                    showscale=False,
                    marker_line_color=outline_colour,
                    marker_line_width=2.8 if in_scope else 1.8,
                    hoverinfo="skip",
                )
            )

    # ------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------
    fig.update_layout(
        template=template,
        margin=dict(l=0, r=0, t=30, b=0),
        geo=dict(
            showframe=False,
            showcoastlines=False,
        ),
        coloraxis=coloraxis,
    )

    return fig
