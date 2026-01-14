# jbi100_app/data/constants.py
from __future__ import annotations

# -----------------------------
# Selection palette (requested)
# -----------------------------
# SELECTION_COLOR_POOL = [
#     "rgb(41, 102, 43)",   #4DF1CE - Dark Green
#     "rgb(174, 0, 255)",   #AE00FF - Purple
#     "rgb(80, 185, 83)",   #50B953 - Green
#     "rgb(64, 35, 255)",   #4023FF - Dark Blue -> orange
#     "rgb(100, 217, 240)", #64D9F0 - Light Blue - yellow
#     "rgb(241, 110, 195)", #F16EC3 - Pink
# ]
SELECTION_COLOR_POOL = [
    "rgb(255, 120, 9)",     # Orange
    "rgb(174, 0, 255)",    # Purple
    "rgb(204, 121, 167)",  # Magenta
    # "rgb(0, 158, 115)",    # Green
    "rgb(240, 228, 66)",   # Yellow
    "rgb(180, 35, 24)",    # Red
    "rgb(98, 49, 7)",  # Brown
]

SELECTION_COLOR_POOL_LIGHT = [
    "rgb(241, 193, 163)",  # light orange
    "rgb(220, 179, 255)",  # light purple
    "rgb(235, 203, 219)",  # light magenta
    # "rgb(184, 226, 214)",  # light green
    "rgb(250, 244, 181)",  # light yellow
    "rgb(232, 190, 186)",  # light red
    "rgb(176, 117, 65)",  # light brown
]

# ---------------------------------
# Filtering / base colours (global)
# ---------------------------------
BASE_GREY = "rgb(105, 105, 105)"     # #696969 (not filtered out)
FADED_GREY = "rgb(242, 242, 242)"    # #F2F2F2 (filtered out)

# Helpful RGBA helpers for fills/lines
BASE_GREY_10 = "rgba(105,105,105,0.10)"
BASE_GREY_12 = "rgba(105,105,105,0.12)"
BASE_GREY_25 = "rgba(105,105,105,0.25)"
BASE_GREY_35 = "rgba(105,105,105,0.35)"
BASE_GREY_55 = "rgba(105,105,105,0.55)"

FADED_GREY_10 = "rgba(242,242,242,0.10)"
FADED_GREY_15 = "rgba(242,242,242,0.15)"

# -----------------------------
# App / data constants used elsewhere
# -----------------------------
MAX_SELECTED_COUNTRIES = 6

# Columns you don’t want treated as numeric metrics
META_COLS = {
    "Country", "_CountryKey", "Region", "Continent",
    "_PLOTLY_NAME", "_ISO3",
}

# Map styling
SMALL_COUNTRY_AREA_KM2 = 1500  # tweak if you like

# Plotly choropleth colourscale (your app already expects this name)
# Keep your current scale here if you had one; this is a safe default.
COLOR_SCALE = "PuBu"

# Histogram styling (only used for histogram internals)
HIST_IN_SCOPE_RGBA = BASE_GREY
HIST_OUT_SCOPE_RGBA = FADED_GREY
HIST_BRUSH_RGBA = "rgba(163,22,33,0.45)"    # brush overlay bars
KDE_IN_SCOPE_RGBA = "rgba(105,105,105,0.85)"  # density line

# Attributes that should use log scale
LOG_SCALE_ATTRS = {
    "GDP",
    "GDP per capita",
    "CO2 emissions",
    "Population",
}
