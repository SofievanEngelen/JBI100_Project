from dash import html, dash_table

def render_numbers_tab(df):
    if df is None or df.empty:
        return html.Div("No data available for the selected attributes or region.")

    return html.Div([
        html.H3("Numbers"),
        dash_table.DataTable(
            data=df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in df.columns],
            style_table={"overflowX": "auto"},
            page_size=15
        )
    ])

