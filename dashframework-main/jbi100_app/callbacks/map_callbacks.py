# jbi100_app/callbacks/map_callbacks.py
from __future__ import annotations

from dash import Input, Output, callback
import pandas as pd

from jbi100_app.data.geo_utils import geo_mask
from jbi100_app.plots.map import build_map_figure
from jbi100_app.state.selection_store import normalize_selection_store, names_from_store
from jbi100_app.data.plotly_country import get_plot_df


def _safe_df() -> pd.DataFrame:
    return get_plot_df()


@callback(
    Output("vis-map", "figure"),
    Output("vis-selected-text", "children"),
    Input("vis-metric", "value"),
    Input("vis-geo-scale", "value"),
    Input("vis-selection-store", "data"),
    Input("pcp-brush-store", "data"),
)
def update_map(metric, geo_scale, selection_store, brush_data):
    df = _safe_df()

    selection_store = normalize_selection_store(selection_store)
    selected_names = names_from_store(selection_store)
    focus = selected_names[0] if selected_names else None

    # PCP/scatter/hist filter store -> brush outline on the map
    brush = []
    if isinstance(brush_data, dict) and brush_data.get("countries"):
        brush = [str(x) for x in brush_data.get("countries", []) if x]

    # Status text
    if selected_names and brush:
        msg = f"Selected: {', '.join(selected_names)} | Brush: {len(brush)} countries"
    elif selected_names:
        msg = f"Selected: {', '.join(selected_names)}"
    elif brush:
        msg = f"Selected: (none) | Brush: {len(brush)} countries"
    else:
        msg = "Selected: (none)"

    # Geo scope (continent/region) based on first selected country (your existing behavior)
    in_mask = geo_mask(df, geo_scale or "global", focus) if not df.empty else None

    # ✅ Do NOT filter df by brush — just highlight those countries
    fig = build_map_figure(
        df=df,
        metric=metric,
        geo_scale=geo_scale or "global",
        in_mask=in_mask,
        selection_store=selection_store,
        brush_countries=brush,  # <-- this draws the highlight outlines
    )
    return fig, msg
