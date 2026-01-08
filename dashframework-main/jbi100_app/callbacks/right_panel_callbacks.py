from __future__ import annotations

from dash import Input, Output, callback

@callback(
    Output("vis-right-wrap-scatter", "style"),
    Output("vis-right-wrap-hist", "style"),
    Output("vis-right-wrap-violin", "style"),
    Output("vis-right-wrap-radar", "style"),
    Output("vis-controls-scatter", "style"),
    Output("vis-controls-hist", "style"),
    Output("vis-controls-violin", "style"),
    Output("vis-controls-radar", "style"),
    Input("vis-right-viz", "value"),
)
def toggle_right_panel(viz_key):
    plot_show = {"display": "block", "height": "100%", "minHeight": 0}
    plot_hide = {"display": "none", "height": "100%", "minHeight": 0}

    ctrl_scatter = {"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px"}
    ctrl_hist = {"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "18px", "alignItems": "center"}
    ctrl_one = {"display": "block"}
    ctrl_none = {"display": "none"}

    viz_key = (viz_key or "scatter").lower().strip()

    if viz_key == "hist":
        return plot_hide, plot_show, plot_hide, plot_hide, ctrl_none, ctrl_hist, ctrl_none, ctrl_none

    if viz_key == "violin":
        return plot_hide, plot_hide, plot_show, plot_hide, ctrl_none, ctrl_none, ctrl_one, ctrl_none

    if viz_key == "radar":
        return plot_hide, plot_hide, plot_hide, plot_show, ctrl_none, ctrl_none, ctrl_none, ctrl_none

    # scatter default
    return plot_show, plot_hide, plot_hide, plot_hide, ctrl_scatter, ctrl_none, ctrl_none, ctrl_none
