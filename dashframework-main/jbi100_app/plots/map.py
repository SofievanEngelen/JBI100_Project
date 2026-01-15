from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.data.constants import COLOR_SCALE, SMALL_COUNTRY_AREA_KM2
from jbi100_app.plots.common import coerce_numeric, pretty_metric
from jbi100_app.state.selection_store import SelectedCountry

_TRANSPARENT = "rgba(0,0,0,0)"


def _key(name: object) -> str:
    if not isinstance(name, str):
        return ""
    return name.strip().upper()


def build_map_figure(
    df: pd.DataFrame,
    metric: str,
    geo_scale: str,
    in_mask: pd.Series | None,
    selection_store: list[SelectedCountry],
    brush_country_keys: list[str] | None,
) -> go.Figure:
    fig = go.Figure()

    if df is None or df.empty or not metric or metric not in df.columns:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0))
        return fig

    plot_df = df.copy()
    plot_df["_z"] = coerce_numeric(plot_df[metric])

    brush_set = set(brush_country_keys or [])

    # ------------------------------------------------------------------
    # Colour scale logic (NEW)
    # ------------------------------------------------------------------
    finite = plot_df["_z"][np.isfinite(plot_df["_z"])]
    if finite.empty:
        vmin = vmax = 0.0
    else:
        vmin = float(finite.min())
        vmax = float(finite.max())

    use_diverging = (vmin < 0) and (vmax > 0)

    if use_diverging:
        vmax_abs = max(abs(vmin), abs(vmax))
        coloraxis = dict(
            colorscale="RdBu",
            cmin=-vmax_abs,
            cmax=vmax_abs,
            cmid=0,
            colorbar=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=0.96,
                yanchor="bottom",
                len=0.7,
                thickness=14,
            ),
        )
    else:
        coloraxis = dict(
            colorscale=COLOR_SCALE,
            cmin=vmin,
            cmax=vmax,
            colorbar=dict(
                orientation="h",
                x=0.5,
                xanchor="center",
                y=0.96,
                yanchor="bottom",
                len=0.7,
                thickness=14,
            ),
        )

    # ------------------------------------------------------------------
    # 1) Base choropleth: ALL countries with metric scale
    # ------------------------------------------------------------------
    fig.add_trace(
        go.Choropleth(
            locations=plot_df["_PLOTLY_NAME"],
            locationmode="country names",
            z=plot_df["_z"],
            coloraxis="coloraxis",
            marker_line_color="rgba(255,255,255,0.35)",
            marker_line_width=0.5,
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"{pretty_metric(metric)}: %{{z}}<extra></extra>"
            ),
            text=plot_df["Country"],
        )
    )

    # ------------------------------------------------------------------
    # 2) Out-of-scope countries: white-out (still visible)
    #    - out of continent/region scope OR outside PCP/scatter filter
    # ------------------------------------------------------------------
    out_mask = pd.Series(False, index=plot_df.index)

    if in_mask is not None:
        out_mask |= ~in_mask

    if brush_set:
        out_mask |= ~plot_df["_CountryKey"].isin(brush_set)

    if out_mask.any():
        fig.add_trace(
            go.Choropleth(
                locations=plot_df.loc[out_mask, "_PLOTLY_NAME"],
                locationmode="country names",
                z=[1] * int(out_mask.sum()),
                colorscale=[[0, "white"], [1, "white"]],
                showscale=False,
                marker_line_color="rgba(180,180,180,0.6)",
                marker_line_width=0.5,
                hoverinfo="skip",
            )
        )

    # ------------------------------------------------------------------
    # 3) Selected countries: BORDER ONLY (transparent fill overlay)
    # ------------------------------------------------------------------
    for item in selection_store:
        cname = item.get("country_name")
        if not cname:
            continue

        ck = _key(cname)

        # determine "in scope" for choosing strong vs light border colour
        in_geo = True
        if in_mask is not None:
            rowmask = plot_df["_CountryKey"] == ck
            if rowmask.any():
                in_geo = bool(in_mask.loc[rowmask].iloc[0])

        in_filter = (not brush_set) or (ck in brush_set)
        in_scope = in_geo and in_filter

        outline_color = item["colour_rgb"] if in_scope else item["colour_rgb_light"]

        row = plot_df.loc[plot_df["_CountryKey"] == ck]
        if row.empty:
            continue

        plotly_name = row.iloc[0].get("_PLOTLY_NAME")
        iso3 = row.iloc[0].get("_ISO3")
        area = pd.to_numeric(row.iloc[0].get("land_area_km2"), errors="coerce")
        is_small = bool(np.isfinite(area) and area < SMALL_COUNTRY_AREA_KM2)

        if is_small:
            if isinstance(iso3, str) and iso3:
                fig.add_trace(
                    go.Scattergeo(
                        locations=[iso3],
                        locationmode="ISO-3",
                        mode="markers",
                        marker=dict(
                            size=12,
                            color=_TRANSPARENT,
                            line=dict(width=2.2, color=outline_color),
                        ),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )
        else:
            fig.add_trace(
                go.Choropleth(
                    locations=[plotly_name],
                    locationmode="country names",
                    z=[1],
                    colorscale=[[0, _TRANSPARENT], [1, _TRANSPARENT]],
                    showscale=False,
                    marker_line_color=outline_color,
                    marker_line_width=2.8 if in_scope else 1.8,
                    hoverinfo="skip",
                )
            )

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(showframe=False, showcoastlines=False),
        coloraxis=coloraxis,
    )

    return fig
