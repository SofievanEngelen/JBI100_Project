from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.data.constants import COLOR_SCALE, SMALL_COUNTRY_AREA_KM2
from jbi100_app.plots.common import coerce_numeric, pretty_metric
from jbi100_app.state.selection_store import SelectedCountry


def build_map_figure(
    df: pd.DataFrame,
    metric: str,
    geo_scale: str,
    in_mask: pd.Series | None,
    selection_store: list[SelectedCountry],
    brush_countries: list[str] | None,
) -> go.Figure:
    fig = go.Figure()

    if df is None or df.empty or not metric or metric not in df.columns:
        fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=0, b=0))
        return fig

    plot_df = df.copy()
    plot_df["_z"] = coerce_numeric(plot_df[metric])

    selected_names = {s["country_name"] for s in selection_store}
    brush_set = set(brush_countries or [])

    # ------------------------------------------------------------------
    # 1️⃣ Base choropleth: ALL countries, metric colours
    # ------------------------------------------------------------------
    fig.add_trace(
        go.Choropleth(
            locations=plot_df["_PLOTLY_NAME"],
            locationmode="country names",
            z=plot_df["_z"],
            colorscale=COLOR_SCALE,
            marker_line_color="rgba(255,255,255,0.35)",
            marker_line_width=0.5,
            colorbar=dict(orientation="h"),
            hovertemplate="<b>%{text}</b><br>"
            + pretty_metric(metric)
            + ": %{z}<extra></extra>",
            text=plot_df["Country"],
        )
    )

    # ------------------------------------------------------------------
    # 2️⃣ Out-of-scope countries → white (but still visible)
    # ------------------------------------------------------------------
    out_mask = pd.Series(False, index=plot_df.index)

    if in_mask is not None:
        out_mask |= ~in_mask

    if brush_set:
        out_mask |= ~plot_df["Country"].isin(brush_set)

    # do NOT white-out selected countries
    out_mask &= ~plot_df["Country"].isin(selected_names)

    if out_mask.any():
        fig.add_trace(
            go.Choropleth(
                locations=plot_df.loc[out_mask, "_PLOTLY_NAME"],
                locationmode="country names",
                z=[0] * int(out_mask.sum()),
                colorscale=[[0, "white"], [1, "white"]],
                showscale=False,
                marker_line_color="rgba(180,180,180,0.6)",
                marker_line_width=0.5,
                hoverinfo="skip",
            )
        )

    # ------------------------------------------------------------------
    # 3️⃣ Selected countries → outline only
    # ------------------------------------------------------------------
    for item in selection_store:
        cname = item["country_name"]

        # scope check
        in_geo = True
        if in_mask is not None:
            row = plot_df["Country"] == cname
            if row.any():
                in_geo = bool(in_mask.loc[row].iloc[0])

        in_filter = not brush_set or cname in brush_set
        in_scope = in_geo and in_filter

        outline_color = item["colour_rgb"] if in_scope else item["colour_rgb_light"]

        row = plot_df.loc[plot_df["Country"] == cname]
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
                            color="white",
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
                    z=[0],
                    colorscale=[[0, "white"], [1, "white"]],
                    showscale=False,
                    marker_line_color=outline_color,
                    marker_line_width=2.8 if in_scope else 1.8,
                    hoverinfo="skip",
                )
            )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        geo=dict(showframe=False, showcoastlines=False),
    )

    return fig
