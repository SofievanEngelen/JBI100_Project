import dash
from dash import Input, Output, State, no_update
import plotly.express as px

from main import app
from jbi100_app.data_loader import (
    DATASETS,
    CATEGORY_ATTRIBUTES,
    ALL_COUNTRIES,
    COUNTRY_TO_REGION,
    COUNTRY_TO_CONTINENT,
)


# ----------------------------------------
# Populate attributes when category changes
# ----------------------------------------
@app.callback(
    Output("attr-dropdown", "options"),
    Output("attr-dropdown", "value"),
    Input("category-dropdown", "value")
)
def update_attribute_dropdown(category):
    if not category:
        return [], None

    attrs = CATEGORY_ATTRIBUTES.get(category, [])

    options = [
        {"label": pretty, "value": raw}
        for raw, pretty in attrs
    ]

    return options, None


# ----------------------------------------
# Update region dropdown based on view radio
# ----------------------------------------
@app.callback(
    Output("region-dropdown", "options"),
    Output("region-dropdown", "value"),
    Input("view-radio", "value")
)
def update_region_dropdown(view):
    if view == "Global":
        return [{"label": "Global", "value": "Global"}], "Global"

    if view == "Continent":
        continents = sorted(set(COUNTRY_TO_CONTINENT.values()))
        return [{"label": c, "value": c} for c in continents], continents[0]

    if view == "Region":
        regions = sorted(set(COUNTRY_TO_REGION.values()))
        return [{"label": r, "value": r} for r in regions], regions[0]

    return [], None


@app.callback(
    Output("current-page", "data", allow_duplicate=True),
    Output("geo-scale", "value", allow_duplicate=True),
    Output("map-click", "data"),
    Output("mun-map", "clickData"),
    Input("mun-map", "clickData"),
    Input("mun-map", "relayoutData"),   # ⬅ NEW
    State("mun-map", "relayoutData"),
    prevent_initial_call=True
)
def handle_map_click(clickData, relayout, relayout_prev):
    if relayout != relayout_prev:
        return no_update, no_update, no_update, None

    if not clickData:
        return no_update, no_update, no_update, no_update

    # Extract clicked country
    point = clickData["points"][0]
    clicked_country = point.get("hovertext")

    if not clicked_country:
        return no_update, no_update, no_update, None

    # Real click: switch and set country
    return (
        "data",
        "country",
        clicked_country,
        None
    )


@app.callback(
    Output("map-click", "data", allow_duplicate=True),
    Input("mun-map", "clickData"),
    prevent_initial_call=True
)
def debug_click(clickData):
    print("\n========= CLICKDATA DEBUG START =========")
    print(clickData)
    print("========= CLICKDATA DEBUG END   =========\n")
    return no_update



# ----------------------------------------
# Country search filtered by selected region
# ----------------------------------------
@app.callback(
    Output("search-country", "options"),
    Input("region-dropdown", "value"),
    Input("view-radio", "value")
)
def update_country_search(region, view):
    if view == "Global":
        return [{"label": c, "value": c} for c in ALL_COUNTRIES]

    elif view == "Continent":
        region_countries = [
            c for c in ALL_COUNTRIES if COUNTRY_TO_CONTINENT.get(c) == region
        ]
        return [{"label": c, "value": c} for c in region_countries]

    elif view == "Region":
        region_countries = [
            c for c in ALL_COUNTRIES if COUNTRY_TO_REGION.get(c) == region
        ]
        return [{"label": c, "value": c} for c in region_countries]

    return []


# ----------------------------------------
# Choropleth MAP
# ----------------------------------------
@app.callback(
    Output("mun-map", "figure"),
    Input("category-dropdown", "value"),
    Input("attr-dropdown", "value"),
    Input("view-radio", "value"),
    Input("region-dropdown", "value"),
    Input("search-country", "value")
)
def update_map(category, attribute, view, region_value, search_country):
    # Prevent empty map
    if not category or not attribute:
        return px.choropleth()

    df = DATASETS[category].copy()

    # Filter based on selected region scope
    if view == "Continent":
        df = df[df["Continent"] == region_value]
    elif view == "Region":
        df = df[df["Region"] == region_value]

    # Drop missing
    df = df[df[attribute].notna()]

    # Ranking
    df = df.sort_values([attribute], ascending=False)
    df["Rank"] = df[attribute].rank(method="dense", ascending=False).astype(int)

    custom_cols = ["Region", attribute, "Rank"]

    hovertemplate = (
            "<b>%{hovertext}</b><br>"
            "Region: %{customdata[0]}<br>"
            f"{attribute}: " + "%{customdata[1]:,.2f}<br>"
                               "Rank: %{customdata[2]}<extra></extra>"
    )

    fig = px.choropleth(
        df,
        locations="Country",
        locationmode="country names",
        color=attribute,
        hover_name="Country",
        custom_data=custom_cols,
        projection="natural earth",
        color_continuous_scale="YlOrRd",
    )

    fig.update_traces(ids=df["Country"])
    fig.update_layout(clickmode="event+select")

    fig.update_traces(
        hovertemplate=hovertemplate,
        selected=dict(marker=dict(opacity=1)),
        unselected=dict(marker=dict(opacity=1))
    )

    # Highlight selected country
    if search_country and search_country in df["Country"].values:
        highlight = df[df["Country"] == search_country]

        fig.add_scattergeo(
            locations=highlight["Country"],
            locationmode="country names",
            mode="markers+text",
            text=highlight["Country"],
            textposition="top center",
            marker=dict(size=14, color="black", line=dict(width=2, color="white")),
            showlegend=False,
        )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(
            title=attribute,
            orientation="h",  # horizontal bar
            thickness=12,  # slim bar height
            len=0.7,  # width relative to page
            x=0.5,  # center horizontally
            xanchor="center",
            y=0.02,  # near bottom
            yanchor="bottom",
            outlinewidth=0,  # no border
            ticks="outside",
        ),
    )

    return fig
