# jbi100_app/data/constants.py
from __future__ import annotations


# =============================================================================
# Selection colour palette
# =============================================================================
# Earlier experimental palettes retained in comments for reference.

SELECTION_COLOUR_POOL: list[str] = [
    "rgb(255, 120, 9)",     # Orange
    "rgb(174, 0, 255)",     # Purple
    "rgb(204, 121, 167)",   # Magenta
    # "rgb(0, 158, 115)",    # Green (unused)
    "rgb(240, 228, 66)",    # Yellow
    "rgb(180, 35, 24)",     # Red
    "rgb(98, 49, 7)",       # Brown
]

SELECTION_COLOUR_POOL_LIGHT: list[str] = [
    "rgb(241, 193, 163)",   # Light orange
    "rgb(220, 179, 255)",   # Light purple
    "rgb(235, 203, 219)",   # Light magenta
    # "rgb(184, 226, 214)", # Light green (unused)
    "rgb(250, 244, 181)",   # Light yellow
    "rgb(232, 190, 186)",   # Light red
    "rgb(176, 117, 65)",    # Light brown
]


# =============================================================================
# Filtering and base colours
# =============================================================================

BASE_GREY = "rgb(105, 105, 105)"      # In-scope / active
FADED_GREY = "rgb(242, 242, 242)"     # Out-of-scope / filtered

# RGBA helpers for fills and overlays
BASE_GREY_10 = "rgba(105,105,105,0.10)"
BASE_GREY_12 = "rgba(105,105,105,0.12)"
BASE_GREY_25 = "rgba(105,105,105,0.25)"
BASE_GREY_35 = "rgba(105,105,105,0.35)"
BASE_GREY_55 = "rgba(105,105,105,0.55)"

FADED_GREY_10 = "rgba(242,242,242,0.10)"
FADED_GREY_15 = "rgba(242,242,242,0.15)"


# =============================================================================
# Application and data limits
# =============================================================================

MAX_SELECTED_COUNTRIES = 6

# Columns that should not be treated as numeric attributes
META_COLS = {
    "Country",
    "_CountryKey",
    "Region",
    "Continent",
    "_PLOTLY_NAME",
    "_ISO3",
}


# =============================================================================
# Map styling
# =============================================================================

SMALL_COUNTRY_AREA_KM2 = 1500  # Threshold for microstate marker rendering

# Plotly colour scales
COLOUR_SCALE = "PuBu"
DIVERGING_COLOUR_SCALE = "RdBu"


# =============================================================================
# Histogram styling
# =============================================================================

HIST_IN_SCOPE_RGBA = BASE_GREY
HIST_OUT_SCOPE_RGBA = FADED_GREY
HIST_BRUSH_RGBA = "rgba(163,22,33,0.45)"     # Brushed bin overlay
KDE_IN_SCOPE_RGBA = "rgba(105,105,105,0.85)" # Density line


# =============================================================================
# Log-scale attributes
# =============================================================================

LOG_SCALE_ATTRS = {
    "GDP",
    "GDP per capita",
    "CO2 emissions",
    "Population",
}
