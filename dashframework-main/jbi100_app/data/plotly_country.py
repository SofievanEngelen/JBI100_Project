# jbi100_app/data/plotly_country.py
from __future__ import annotations

import pandas as pd

from jbi100_app.data.data_loader import DATA_INFO, UN_COUNTRIES


# =============================================================================
# Helpers: naming and Plotly country mapping
# (moved from visualisation_callbacks.py)
# =============================================================================

_META_FALLBACK_COLS = ["Country", "Region", "Continent"]


def _canon_un_name(name: str) -> str:
    """
    Convert a country name to a canonical UN-style uppercase form.
    """
    if name is None:
        return ""

    s = str(name).strip().upper()
    s = " ".join(s.split())
    return s


# Explicit fixes where UN naming does not match Plotly expectations
_UN_TO_PLOTLY_FIX: dict[str, str] = {
    "UNITED STATES": "United States",
    "UNITED KINGDOM": "United Kingdom",
    "COTE D'IVOIRE": "Côte d'Ivoire",
    "CONGO, REPUBLIC OF THE": "Congo",
    "CONGO, DEMOCRATIC REPUBLIC OF THE": "Democratic Republic of the Congo",
    "KOREA, SOUTH": "South Korea",
    "KOREA, NORTH": "North Korea",
    "BAHAMAS, THE": "The Bahamas",
    "GAMBIA, THE": "The Gambia",
    "MICRONESIA, FEDERATED STATES OF": "Micronesia",
    "TURKEY (TURKIYE)": "Turkey",
    "BURMA": "Myanmar",
    "NORTH MACEDONIA": "North Macedonia",
    "CABO VERDE": "Cape Verde",
    "TIMOR-LESTE": "Timor-Leste",
    "SAO TOME AND PRINCIPE": "Sao Tome and Principe",
}

_SMALL_WORDS = {"of", "the", "and", "to", "in", "on", "for"}


def _smart_title(text: str) -> str:
    """
    Title-case a country name while keeping short connector words lower-case.
    """
    parts = text.lower().split()
    out: list[str] = []

    for i, word in enumerate(parts):
        if i > 0 and word in _SMALL_WORDS:
            out.append(word)
        else:
            out.append(word[:1].upper() + word[1:])

    return " ".join(out)


def _un_to_plotly_name(un_name: str) -> str:
    """
    Convert a canonical UN country name to a Plotly-compatible country name.
    """
    un = _canon_un_name(un_name)
    if not un:
        return ""

    if un in _UN_TO_PLOTLY_FIX:
        return _UN_TO_PLOTLY_FIX[un]

    # Remove parenthetical qualifiers
    if "(" in un:
        un = un.split("(", 1)[0].strip()

    # Convert "X, Y" → "Y X"
    if "," in un:
        left, right = [p.strip() for p in un.split(",", 1)]
        un = f"{right} {left}".strip()

    return _smart_title(un)


# =============================================================================
# ISO-3 overrides for microstates
# =============================================================================

ISO3_OVERRIDES: dict[str, str] = {
    "ANDORRA": "AND",
    "ANTIGUA AND BARBUDA": "ATG",
    "BARBADOS": "BRB",
    "LIECHTENSTEIN": "LIE",
    "SAN MARINO": "SMR",
    "MONACO": "MCO",
    "MALTA": "MLT",
    "SINGAPORE": "SGP",
    "SEYCHELLES": "SYC",
    "DOMINICA": "DMA",
    "SAINT KITTS AND NEVIS": "KNA",
    "SAINT LUCIA": "LCA",
    "SAINT VINCENT AND THE GRENADINES": "VCT",
    "GRENADA": "GRD",
    "MARSHALL ISLANDS": "MHL",
    "NAURU": "NRU",
    "PALAU": "PLW",
    "TUVALU": "TUV",
}


def _to_iso3(country_name: str) -> str | None:
    """
    Return an ISO-3 country code override for known microstates.
    """
    if not country_name:
        return None

    key = _canon_un_name(country_name)
    return ISO3_OVERRIDES.get(key)


# =============================================================================
# Public API
# =============================================================================

def get_plot_df() -> pd.DataFrame:
    """
    Return a Plotly-ready dataframe derived from DATA_INFO.

    Adds the following derived columns:
    - _UN_NAME:
        Canonical UN-style uppercase country name.
    - _PLOTLY_NAME:
        Country name matching Plotly choropleth expectations.
    - _ISO3:
        ISO-3 code for microstates (where required).

    The dataframe is filtered to UN member states only.
    """
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=_META_FALLBACK_COLS)

    df = DATA_INFO.copy()

    # Ensure required metadata columns exist
    for col in _META_FALLBACK_COLS:
        if col not in df.columns:
            df[col] = "Unknown"

    df["Country"] = df["Country"].astype(str)

    # Canonical UN name
    df["_UN_NAME"] = df["Country"].map(_canon_un_name)

    # Filter to UN member states
    df = df[df["_UN_NAME"].isin(UN_COUNTRIES)].copy()

    # Derived Plotly naming and ISO-3 codes
    df["_PLOTLY_NAME"] = df["Country"].map(_un_to_plotly_name)
    df["_ISO3"] = df["Country"].map(_to_iso3)

    return df
