# jbi100_app/data/plotly_country.py
from __future__ import annotations

import pandas as pd

from jbi100_app.data.data_loader import DATA_INFO, UN_COUNTRIES

# ============================================================
# Helpers: naming + plotly country mapping
# (moved from visualisation_callbacks.py)
# ============================================================

_META_FALLBACK_COLS = ["Country", "Region", "Continent"]

def _canon_un_name(x: str) -> str:
    if x is None:
        return ""
    s = str(x).strip().upper()
    s = " ".join(s.split())
    return s


_UN_TO_PLOTLY_FIX = {
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

def _smart_title(s: str) -> str:
    parts = s.lower().split()
    out = []
    for i, w in enumerate(parts):
        if i > 0 and w in _SMALL_WORDS:
            out.append(w)
        else:
            out.append(w[:1].upper() + w[1:])
    return " ".join(out)

def _un_to_plotly_name(un_name: str) -> str:
    un = _canon_un_name(un_name)
    if not un:
        return ""
    if un in _UN_TO_PLOTLY_FIX:
        return _UN_TO_PLOTLY_FIX[un]
    if "(" in un:
        un = un.split("(", 1)[0].strip()
    if "," in un:
        left, right = [p.strip() for p in un.split(",", 1)]
        un = f"{right} {left}".strip()
    return _smart_title(un)


# ============================================================
# ISO-3 overrides for microstates
# ============================================================
ISO3_OVERRIDES = {
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
    if not country_name:
        return None
    key = _canon_un_name(country_name)
    return ISO3_OVERRIDES.get(key)


def get_plot_df() -> pd.DataFrame:
    """
    Returns a copy of DATA_INFO with required derived columns for Plotly:
      - _UN_NAME (canonical uppercase)
      - filtered to UN_COUNTRIES
      - _PLOTLY_NAME (name matching plotly choropleth 'country names')
      - _ISO3 (iso-3 for microstates)
    """
    if DATA_INFO is None or getattr(DATA_INFO, "empty", True):
        return pd.DataFrame(columns=_META_FALLBACK_COLS)

    df = DATA_INFO.copy()

    # Ensure expected meta cols exist
    for c in _META_FALLBACK_COLS:
        if c not in df.columns:
            df[c] = "Unknown"

    df["Country"] = df["Country"].astype(str)

    df["_UN_NAME"] = df["Country"].map(_canon_un_name)

    # Filter to UN list
    df = df[df["_UN_NAME"].isin(UN_COUNTRIES)].copy()

    # Derived plotly naming + iso3
    df["_PLOTLY_NAME"] = df["Country"].map(_un_to_plotly_name)
    df["_ISO3"] = df["Country"].map(_to_iso3)

    return df
