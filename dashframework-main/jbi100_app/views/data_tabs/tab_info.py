from dash import html
from urllib.parse import quote


def format_population(pop):
    """Human-readable population formatting."""
    try:
        pop = float(pop)
        if pop >= 1_000_000:
            return f"{pop / 1_000_000:.1f} million"
        if pop >= 1_000:
            return f"{pop / 1_000:.1f} thousand"
        return str(int(pop))
    except:
        return "Unknown"


def format_area(area):
    """Human-readable area formatting."""
    try:
        area = float(area[:-6].replace(',', ''))
        return f"{area:,.0f} km²"
    except:
        return "Unknown"


def render_info_tab(attrs, geo_tags, geo_scale, country_info_df):
    """
    Renders Info tab content using the country_info dataset.
    """

    # ----- No country selected -----
    if not geo_tags:
        return html.Div([
            html.H3("Country Overview"),
            html.P("Select a country in the left panel or by clicking on the map."),
        ])

    # Only use the first selected country
    country = geo_tags[0]["id"].upper()

    if country not in country_info_df["Country"].values:
        return html.Div([
            html.H3("Country Overview"),
            html.P("No information available for the selected country."),
        ])

    row = country_info_df[country_info_df["Country"] == country].iloc[0]

    name = row.get("Written_name", country)
    capital = row.get("Capital", "Unknown")
    gov_type = row.get("Government_Type", "Unknown")
    suffrage = row.get("Suffrage_Age", "Unknown")
    pop = format_population(row.get("Total_Population"))
    area = format_area(row.get("Area_Total"))
    continent = row.get("Continent", "Unknown")
    subregion = row.get("Region", "Unknown")
    desc = row.get("Description", "")
    wiki = row.get("Wiki_link", "")

    # ----- Layout -----
    return html.Div(
        style={"maxWidth": "650px"},
        children=[

            html.H2(name),

            html.P(desc, style={"fontSize": "18px", "marginBottom": "20px"}),

            html.H3("Basic Facts", style={"marginTop": "20px"}),

            html.Ul([
                html.Li([html.B("Capital: "), capital]),
                html.Li([html.B("Government: "), gov_type]),
                html.Li([html.B("Suffrage Age: "), suffrage]),
                html.Li([html.B("Continent: "), continent.title() if isinstance(continent, str) else continent]),
                html.Li([html.B("Subregion: "), subregion]),
                html.Li([html.B("Population: "), pop]),
                html.Li([html.B("Area: "), area]),
            ]),

            html.Br(),

            # Optional Wikipedia link
            html.Div([
                html.A(
                    "↗ More details on Wikipedia",
                    href=wiki if wiki else f"https://en.wikipedia.org/wiki/{quote(name)}",
                    target="_blank",
                    style={"fontSize": "16px"}
                )
            ]) if wiki or name else html.Div(),

            html.Div([
                html.A(
                    "↗ More details on Wikipedia",
                    href=wiki if wiki else f"https://en.wikipedia.org/wiki/{quote(name)}",
                    target="_blank",
                    style={"fontSize": "16px"}
                )
            ]) if wiki or name else html.Div(),
        ]
    )
