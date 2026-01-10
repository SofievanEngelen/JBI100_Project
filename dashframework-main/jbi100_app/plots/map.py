# jbi100_app/plots/map.py
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from jbi100_app.data.constants import (
    COLOR_SCALE,
    BASE_GREY,
    SMALL_COUNTRY_AREA_KM2,
)
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

    geo_scale = (geo_scale or "global").lower().strip()

    # ------------------------------------------------------------
    # Determine whether continent/region scope is active
    # (this logic is UNCHANGED)
    # ------------------------------------------------------------
    scope_active = False
    if geo_scale in ("continent", "region") and in_mask is not None and len(in_mask) == len(plot_df):
        mask_bool = in_mask.to_numpy(dtype=bool)
        scope_active = bool(mask_bool.any() and (~mask_bool).any())

    # ------------------------------------------------------------
    # Shared horizontal colorbar (UNCHANGED)
    # ------------------------------------------------------------
    colorbar_cfg = dict(
        title=None,
        orientation="h",
        x=0.5,
        xanchor="center",
        y=1.08,
        yanchor="top",
        len=1.0,
        thickness=18,
        tickfont=dict(size=14),
    )

    zmin = float(plot_df["_z"].min())
    zmax = float(plot_df["_z"].max())

    # ------------------------------------------------------------
    # Base choropleth(s)
    # ------------------------------------------------------------
    if scope_active:
        # =========================
        # Continent / Region mode
        # (COMPLETELY UNCHANGED)
        # =========================
        mask_bool = in_mask.to_numpy(dtype=bool)  # type: ignore[union-attr]
        in_df = plot_df.loc[mask_bool].copy()
        out_df = plot_df.loc[~mask_bool].copy()

        if not out_df.empty:
            fig.add_trace(
                go.Choropleth(
                    locations=out_df["_PLOTLY_NAME"],
                    locationmode="country names",
                    z=[1.0] * len(out_df),
                    text=out_df["Country"],
                    customdata=np.stack([out_df["Country"]], axis=-1),
                    colorscale=[[0, "rgba(255,255,255,1)"], [1, "rgba(255,255,255,1)"]],
                    showscale=False,
                    marker_line_color="rgba(200,200,200,0.55)",
                    marker_line_width=0.6,
                    hoverinfo="skip",
                )
            )

        fig.add_trace(
            go.Choropleth(
                locations=in_df["_PLOTLY_NAME"],
                locationmode="country names",
                z=in_df["_z"],
                zmin=zmin,
                zmax=zmax,
                text=in_df["Country"],
                customdata=np.stack([in_df["Country"]], axis=-1),
                colorscale=COLOR_SCALE,
                colorbar=colorbar_cfg,
                marker_line_color="rgba(255,255,255,0.35)",
                marker_line_width=0.5,
                hovertemplate="<b>%{text}</b><br>"
                + pretty_metric(metric)
                + ": %{z}<extra></extra>",
            )
        )

    else:
        # =========================
        # GLOBAL MODE
        # =========================
        brush_set = set(str(x) for x in (brush_countries or []) if x)

        filter_active = False
        if brush_set:
            brushed_mask = plot_df["Country"].astype(str).isin(brush_set).to_numpy(dtype=bool)
            filter_active = bool(brushed_mask.any() and (~brushed_mask).any())

        if filter_active:
            in_df = plot_df.loc[brushed_mask].copy()
            out_df = plot_df.loc[~brushed_mask].copy()

            # OUTSIDE FILTER — SAME AS CONTINENT/REGION OUT-OF-SCOPE
            if not out_df.empty:
                fig.add_trace(
                    go.Choropleth(
                        locations=out_df["_PLOTLY_NAME"],
                        locationmode="country names",
                        z=[1.0] * len(out_df),
                        text=out_df["Country"],
                        customdata=np.stack([out_df["Country"]], axis=-1),
                        colorscale=[[0, "rgba(255,255,255,1)"], [1, "rgba(255,255,255,1)"]],
                        showscale=False,
                        marker_line_color="rgba(200,200,200,0.55)",
                        marker_line_width=0.6,
                        hoverinfo="skip",
                    )
                )

            # INSIDE FILTER — NORMAL GLOBAL COLOURING
            fig.add_trace(
                go.Choropleth(
                    locations=in_df["_PLOTLY_NAME"],
                    locationmode="country names",
                    z=in_df["_z"],
                    zmin=zmin,
                    zmax=zmax,
                    text=in_df["Country"],
                    customdata=np.stack([in_df["Country"]], axis=-1),
                    colorscale=COLOR_SCALE,
                    colorbar=colorbar_cfg,
                    marker_line_color="rgba(255,255,255,0.35)",
                    marker_line_width=0.5,
                    hovertemplate="<b>%{text}</b><br>"
                    + pretty_metric(metric)
                    + ": %{z}<extra></extra>",
                )
            )

        else:
            # ORIGINAL GLOBAL BEHAVIOUR (UNCHANGED)
            fig.add_trace(
                go.Choropleth(
                    locations=plot_df["_PLOTLY_NAME"],
                    locationmode="country names",
                    z=plot_df["_z"],
                    zmin=zmin,
                    zmax=zmax,
                    text=plot_df["Country"],
                    customdata=np.stack([plot_df["Country"]], axis=-1),
                    colorscale=COLOR_SCALE,
                    colorbar=colorbar_cfg,
                    marker_line_color="rgba(255,255,255,0.35)",
                    marker_line_width=0.5,
                    hovertemplate="<b>%{text}</b><br>"
                    + pretty_metric(metric)
                    + ": %{z}<extra></extra>",
                )
            )

    # ------------------------------------------------------------
    # Brush outline (UNCHANGED)
    # ------------------------------------------------------------
    if brush_countries:
        brush_df = plot_df[plot_df["Country"].isin(brush_countries)].copy()
        if not brush_df.empty:
            fig.add_trace(
                go.Choropleth(
                    locations=brush_df["_PLOTLY_NAME"],
                    locationmode="country names",
                    z=[1.0] * len(brush_df),
                    text=brush_df["Country"],
                    customdata=np.stack([brush_df["Country"]], axis=-1),
                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                    showscale=False,
                    marker_line_color="rgba(255,255,255,0.35)",
                    marker_line_width=1.5,
                    hoverinfo="skip",
                )
            )

    # ------------------------------------------------------------
    # Selected countries (UNCHANGED)
    # ------------------------------------------------------------
    for item in selection_store:
        cname = item.get("country_name")
        ccol = item.get("colour_rgb") or "rgb(180,35,24)"
        if not cname:
            continue

        row = plot_df.loc[plot_df["Country"] == cname]
        if row.empty:
            continue

        plotly_name = row.iloc[0].get("_PLOTLY_NAME")
        iso3 = row.iloc[0].get("_ISO3")
        area = pd.to_numeric(row.iloc[0].get("land_area_km2"), errors="coerce")

        is_small = bool(np.isfinite(area) and area < SMALL_COUNTRY_AREA_KM2)

        if is_small:
            if isinstance(iso3, str) and iso3.strip():
                fig.add_trace(
                    go.Scattergeo(
                        locations=[iso3],
                        locationmode="ISO-3",
                        mode="markers",
                        marker=dict(size=12, color=ccol, line=dict(width=1.5, color="white")),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
            elif isinstance(plotly_name, str) and plotly_name.strip():
                fig.add_trace(
                    go.Scattergeo(
                        locations=[plotly_name],
                        locationmode="country names",
                        mode="markers",
                        marker=dict(size=12, color=ccol, line=dict(width=1.5, color="white")),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
            continue

        if isinstance(plotly_name, str) and plotly_name.strip():
            fig.add_trace(
                go.Choropleth(
                    locations=[plotly_name],
                    locationmode="country names",
                    z=[1.0],
                    text=[cname],
                    customdata=[[cname]],
                    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                    showscale=False,
                    marker_line_color=ccol,
                    marker_line_width=2.8,
                    hoverinfo="skip",
                )
            )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=0, b=0),
        title=None,
        geo=dict(
            showframe=False,
            showcoastlines=False,
            projection_type="natural earth",
        ),
    )

    return fig
