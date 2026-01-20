# jbi100_app/data/geo_utils.py
from __future__ import annotations

import pandas as pd


# =============================================================================
# Country normalisation
# =============================================================================

def normalise_country_key(name: object) -> str:
    """
    Normalise a country name into a canonical uppercase key.

    Whitespace is collapsed and casing is standardised.
    """
    if not isinstance(name, str):
        return ""
    return " ".join(name.strip().upper().split())


def normalise_country_display(name: object) -> str:
    """
    Normalise a country name for display purposes.
    """
    if not isinstance(name, str):
        return ""
    return name.strip()


# =============================================================================
# UN countries list
# =============================================================================

UN_COUNTRIES = {
    "AFGHANISTAN", "ALBANIA", "ALGERIA", "ANDORRA", "ANGOLA",
    "ANTIGUA AND BARBUDA", "ARGENTINA", "ARMENIA", "AUSTRALIA",
    "AUSTRIA", "AZERBAIJAN", "BAHAMAS, THE", "BAHRAIN",
    "BANGLADESH", "BARBADOS", "BELARUS", "BELGIUM", "BELIZE",
    "BENIN", "BHUTAN", "BOLIVIA", "BOSNIA AND HERZEGOVINA",
    "BOTSWANA", "BRAZIL", "BRUNEI", "BULGARIA", "BURKINA FASO",
    "BURUNDI", "CABO VERDE", "CAMBODIA", "CAMEROON", "CANADA",
    "CENTRAL AFRICAN REPUBLIC", "CHAD", "CHILE", "CHINA",
    "COLOMBIA", "COMOROS", "CONGO, REPUBLIC OF THE",
    "COSTA RICA", "COTE D'IVOIRE", "CROATIA", "CUBA", "CYPRUS",
    "CZECHIA", "KOREA, NORTH",
    "CONGO, DEMOCRATIC REPUBLIC OF THE", "DENMARK", "DJIBOUTI",
    "DOMINICA", "DOMINICAN REPUBLIC", "ECUADOR", "EGYPT",
    "EL SALVADOR", "EQUATORIAL GUINEA", "ERITREA", "ESTONIA",
    "ESWATINI", "ETHIOPIA", "FIJI", "FINLAND", "FRANCE",
    "GABON", "GAMBIA, THE", "GEORGIA", "GERMANY", "GHANA",
    "GREECE", "GRENADA", "GUATEMALA", "GUINEA",
    "GUINEA-BISSAU", "GUYANA", "HAITI", "HONDURAS", "HUNGARY",
    "ICELAND", "INDIA", "INDONESIA", "IRAN", "IRAQ", "IRELAND",
    "ISRAEL", "ITALY", "JAMAICA", "JAPAN", "JORDAN",
    "KAZAKHSTAN", "KENYA", "KIRIBATI", "KUWAIT", "KYRGYZSTAN",
    "LAOS", "LATVIA", "LEBANON", "LESOTHO", "LIBERIA", "LIBYA",
    "LIECHTENSTEIN", "LITHUANIA", "LUXEMBOURG", "MADAGASCAR",
    "MALAWI", "MALAYSIA", "MALDIVES", "MALI", "MALTA",
    "MARSHALL ISLANDS", "MAURITANIA", "MAURITIUS", "MEXICO",
    "MICRONESIA, FEDERATED STATES OF", "MONACO", "MONGOLIA",
    "MONTENEGRO", "MOROCCO", "MOZAMBIQUE", "BURMA", "NAMIBIA",
    "NAURU", "NEPAL", "NETHERLANDS", "NEW ZEALAND",
    "NICARAGUA", "NIGER", "NIGERIA", "NORTH MACEDONIA",
    "NORWAY", "OMAN", "PAKISTAN", "PALAU", "PANAMA",
    "PAPUA NEW GUINEA", "PARAGUAY", "PERU", "PHILIPPINES",
    "POLAND", "PORTUGAL", "QATAR", "KOREA, SOUTH", "MOLDOVA",
    "ROMANIA", "RUSSIA", "RWANDA", "SAINT KITTS AND NEVIS",
    "SAINT LUCIA", "SAINT VINCENT AND THE GRENADINES", "SAMOA",
    "SAN MARINO", "SAO TOME AND PRINCIPE", "SAUDI ARABIA",
    "SENEGAL", "SERBIA", "SEYCHELLES", "SIERRA LEONE",
    "SINGAPORE", "SLOVAKIA", "SLOVENIA", "SOLOMON ISLANDS",
    "SOMALIA", "SOUTH AFRICA", "SOUTH SUDAN", "SPAIN",
    "SRI LANKA", "SUDAN", "SURINAME", "SWEDEN", "SWITZERLAND",
    "SYRIA", "TAJIKISTAN", "TANZANIA", "THAILAND",
    "TIMOR-LESTE", "TOGO", "TONGA", "TRINIDAD AND TOBAGO",
    "TUNISIA", "TURKEY (TURKIYE)", "TURKMENISTAN", "TUVALU",
    "UGANDA", "UKRAINE", "UNITED ARAB EMIRATES",
    "UNITED KINGDOM", "UNITED STATES", "URUGUAY",
    "UZBEKISTAN", "VANUATU", "VENEZUELA", "VIETNAM", "YEMEN",
    "ZAMBIA", "ZIMBABWE",
}


# =============================================================================
# Continents and regions
# =============================================================================

CONTINENTS: dict[str, list[str]] = {
    "AFRICA": [
        "ALGERIA", "ANGOLA", "BENIN", "BOTSWANA", "BURKINA FASO",
        "BURUNDI", "CABO VERDE", "CAMEROON",
        "CENTRAL AFRICAN REPUBLIC", "CHAD", "COMOROS",
        "CONGO, DEMOCRATIC REPUBLIC OF THE",
        "CONGO, REPUBLIC OF THE", "COTE D'IVOIRE", "DJIBOUTI",
        "EGYPT", "EQUATORIAL GUINEA", "ERITREA", "ESWATINI",
        "ETHIOPIA", "GABON", "GAMBIA, THE", "GHANA", "GUINEA",
        "GUINEA-BISSAU", "KENYA", "LESOTHO", "LIBERIA",
        "LIBYA", "MADAGASCAR", "MALAWI", "MALI", "MAURITANIA",
        "MAURITIUS", "MOROCCO", "MOZAMBIQUE", "NAMIBIA",
        "NIGER", "NIGERIA", "RWANDA", "SAO TOME AND PRINCIPE",
        "SENEGAL", "SEYCHELLES", "SIERRA LEONE", "SOMALIA",
        "SOUTH AFRICA", "SOUTH SUDAN", "SUDAN", "TANZANIA",
        "TOGO", "TUNISIA", "UGANDA", "ZAMBIA", "ZIMBABWE",
    ],
    "ASIA": [
        "AFGHANISTAN", "ARMENIA", "AZERBAIJAN", "BAHRAIN",
        "BANGLADESH", "BHUTAN", "BRUNEI", "CAMBODIA", "CHINA",
        "CYPRUS", "GEORGIA", "INDIA", "INDONESIA", "IRAN",
        "IRAQ", "ISRAEL", "JAPAN", "JORDAN", "KAZAKHSTAN",
        "KOREA, NORTH", "KOREA, SOUTH", "KUWAIT",
        "KYRGYZSTAN", "LAOS", "LEBANON", "MALAYSIA",
        "MALDIVES", "MONGOLIA", "MYANMAR", "NEPAL", "OMAN",
        "PAKISTAN", "PHILIPPINES", "QATAR", "SAUDI ARABIA",
        "SINGAPORE", "SRI LANKA", "SYRIA", "TAJIKISTAN",
        "THAILAND", "TIMOR-LESTE", "TURKEY (TURKIYE)",
        "TURKMENISTAN", "UNITED ARAB EMIRATES", "UZBEKISTAN",
        "VIETNAM", "YEMEN",
    ],
    "EUROPE": [
        "ALBANIA", "ANDORRA", "AUSTRIA", "BELARUS", "BELGIUM",
        "BOSNIA AND HERZEGOVINA", "BULGARIA", "CROATIA",
        "CZECHIA", "DENMARK", "ESTONIA", "FINLAND", "FRANCE",
        "GERMANY", "GREECE", "HUNGARY", "ICELAND", "IRELAND",
        "ITALY", "LATVIA", "LIECHTENSTEIN", "LITHUANIA",
        "LUXEMBOURG", "MALTA", "MOLDOVA", "MONACO",
        "MONTENEGRO", "NETHERLANDS", "NORTH MACEDONIA",
        "NORWAY", "POLAND", "PORTUGAL", "ROMANIA", "RUSSIA",
        "SAN MARINO", "SERBIA", "SLOVAKIA", "SLOVENIA",
        "SPAIN", "SWEDEN", "SWITZERLAND", "UKRAINE",
        "UNITED KINGDOM",
    ],
    "NORTH AMERICA": ["CANADA", "UNITED STATES", "MEXICO"],
    "SOUTH AMERICA": [
        "ARGENTINA", "BOLIVIA", "BRAZIL", "CHILE", "COLOMBIA",
        "ECUADOR", "GUYANA", "PARAGUAY", "PERU", "SURINAME",
        "URUGUAY", "VENEZUELA", "ANTIGUA AND BARBUDA",
        "BAHAMAS, THE", "BARBADOS", "CUBA", "DOMINICA",
        "DOMINICAN REPUBLIC", "GRENADA", "HAITI", "JAMAICA",
        "SAINT KITTS AND NEVIS", "SAINT LUCIA",
        "SAINT VINCENT AND THE GRENADINES", "BELIZE",
        "COSTA RICA", "EL SALVADOR", "GUATEMALA", "HONDURAS",
        "NICARAGUA", "PANAMA", "TRINIDAD AND TOBAGO",
    ],
    "OCEANIA": [
        "AUSTRALIA", "FIJI", "KIRIBATI", "MARSHALL ISLANDS",
        "MICRONESIA, FEDERATED STATES OF", "NAURU",
        "NEW ZEALAND", "PALAU", "PAPUA NEW GUINEA", "SAMOA",
        "SOLOMON ISLANDS", "TONGA", "TUVALU", "VANUATU",
    ],
}


REGIONS: dict[str, list[str]] = {
    "NORTHERN AFRICA": [
        "ALGERIA", "EGYPT", "LIBYA", "MOROCCO", "SUDAN",
        "TUNISIA",
    ],
    "WESTERN AFRICA": [
        "BENIN", "BURKINA FASO", "CABO VERDE", "COTE D'IVOIRE",
        "GAMBIA, THE", "GHANA", "GUINEA", "GUINEA-BISSAU",
        "LIBERIA", "MALI", "MAURITANIA", "NIGER", "NIGERIA",
        "SENEGAL", "SIERRA LEONE", "TOGO",
    ],
    "MIDDLE AFRICA": [
        "ANGOLA", "CAMEROON", "CENTRAL AFRICAN REPUBLIC",
        "CHAD", "CONGO, DEMOCRATIC REPUBLIC OF THE",
        "CONGO, REPUBLIC OF THE", "EQUATORIAL GUINEA", "GABON",
        "SAO TOME AND PRINCIPE",
    ],
    "EASTERN AFRICA": [
        "BURUNDI", "COMOROS", "DJIBOUTI", "ERITREA", "ETHIOPIA",
        "KENYA", "MADAGASCAR", "MALAWI", "MAURITIUS",
        "MOZAMBIQUE", "RWANDA", "SEYCHELLES", "SOMALIA",
        "SOUTH SUDAN", "TANZANIA", "UGANDA", "ZAMBIA",
        "ZIMBABWE",
    ],
    "SOUTHERN AFRICA": [
        "BOTSWANA", "ESWATINI", "LESOTHO", "NAMIBIA",
        "SOUTH AFRICA",
    ],
    "NORTHERN AMERICA": ["CANADA", "UNITED STATES"],
    "CENTRAL AMERICA": [
        "BELIZE", "COSTA RICA", "EL SALVADOR", "GUATEMALA",
        "HONDURAS", "MEXICO", "NICARAGUA", "PANAMA",
    ],
    "CARIBBEAN": [
        "ANTIGUA AND BARBUDA", "BAHAMAS, THE", "BARBADOS",
        "CUBA", "DOMINICA", "DOMINICAN REPUBLIC", "GRENADA",
        "HAITI", "JAMAICA", "SAINT KITTS AND NEVIS",
        "SAINT LUCIA", "SAINT VINCENT AND THE GRENADINES",
        "TRINIDAD AND TOBAGO",
    ],
    "SOUTH AMERICA": [
        "ARGENTINA", "BOLIVIA", "BRAZIL", "CHILE", "COLOMBIA",
        "ECUADOR", "GUYANA", "PARAGUAY", "PERU", "SURINAME",
        "URUGUAY", "VENEZUELA",
    ],
    "CENTRAL ASIA": [
        "KAZAKHSTAN", "KYRGYZSTAN", "TAJIKISTAN",
        "TURKMENISTAN", "UZBEKISTAN",
    ],
    "EASTERN ASIA": [
        "CHINA", "JAPAN", "KOREA, NORTH", "KOREA, SOUTH",
        "MONGOLIA",
    ],
    "SOUTH-EASTERN ASIA": [
        "BRUNEI", "CAMBODIA", "INDONESIA", "LAOS",
        "MALAYSIA", "BURMA", "PHILIPPINES", "SINGAPORE",
        "THAILAND", "TIMOR-LESTE", "VIETNAM",
    ],
    "SOUTHERN ASIA": [
        "AFGHANISTAN", "BANGLADESH", "BHUTAN", "INDIA", "IRAN",
        "MALDIVES", "NEPAL", "PAKISTAN", "SRI LANKA",
    ],
    "WESTERN ASIA": [
        "ARMENIA", "AZERBAIJAN", "BAHRAIN", "CYPRUS",
        "GEORGIA", "IRAQ", "ISRAEL", "JORDAN", "KUWAIT",
        "LEBANON", "OMAN", "QATAR", "SAUDI ARABIA", "SYRIA",
        "TURKEY (TURKIYE)", "UNITED ARAB EMIRATES", "YEMEN",
    ],
    "EASTERN EUROPE": [
        "BELARUS", "BULGARIA", "CZECHIA", "HUNGARY",
        "MOLDOVA", "POLAND", "ROMANIA", "RUSSIA",
        "SLOVAKIA", "UKRAINE",
    ],
    "NORTHERN EUROPE": [
        "DENMARK", "ESTONIA", "FINLAND", "ICELAND", "IRELAND",
        "LATVIA", "LITHUANIA", "NORWAY", "SWEDEN",
        "UNITED KINGDOM",
    ],
    "SOUTHERN EUROPE": [
        "ALBANIA", "ANDORRA", "BOSNIA AND HERZEGOVINA",
        "CROATIA", "GREECE", "ITALY", "MALTA", "MONTENEGRO",
        "NORTH MACEDONIA", "PORTUGAL", "SAN MARINO", "SERBIA",
        "SLOVENIA", "SPAIN",
    ],
    "WESTERN EUROPE": [
        "AUSTRIA", "BELGIUM", "FRANCE", "GERMANY",
        "LIECHTENSTEIN", "LUXEMBOURG", "MONACO",
        "NETHERLANDS", "SWITZERLAND",
    ],
    "AUSTRALIA AND NEW ZEALAND": ["AUSTRALIA", "NEW ZEALAND"],
    "MELANESIA": [
        "FIJI", "PAPUA NEW GUINEA", "SOLOMON ISLANDS",
        "VANUATU",
    ],
    "MICRONESIA": [
        "KIRIBATI", "MARSHALL ISLANDS",
        "MICRONESIA, FEDERATED STATES OF", "NAURU", "PALAU",
    ],
    "POLYNESIA": ["SAMOA", "TONGA", "TUVALU"],
}


COUNTRY_TO_REGION: dict[str, str] = {
    country: region
    for region, countries in REGIONS.items()
    for country in countries
}

COUNTRY_TO_CONTINENT: dict[str, str] = {
    country: continent
    for continent, countries in CONTINENTS.items()
    for country in countries
}


# =============================================================================
# Apply geography to dataframe
# =============================================================================

def apply_geography(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply geographic metadata (continent and region) to a dataframe.

    The dataframe must contain a 'Country' column.
    """
    if df is None or df.empty or "Country" not in df.columns:
        return df

    out = df.copy()

    out["Country"] = out["Country"].apply(normalise_country_display)
    out["_CountryKey"] = out["Country"].apply(normalise_country_key)

    # Filter to UN-recognised countries
    out = out[out["_CountryKey"].isin(UN_COUNTRIES)].copy()

    out["Continent"] = (
        out["_CountryKey"].map(COUNTRY_TO_CONTINENT).fillna("Unknown")
    )
    out["Region"] = (
        out["_CountryKey"].map(COUNTRY_TO_REGION).fillna("Unknown")
    )

    return out


# =============================================================================
# Geographic scope mask
# =============================================================================

def geo_mask(
    df: pd.DataFrame,
    geo_scale: str,
    focus_country: str | None,
) -> pd.Series:
    """
    Return a boolean mask selecting rows within the same
    continent or region as the focus country.
    """
    if df is None or df.empty:
        return pd.Series([], dtype=bool)

    geo_scale = (geo_scale or "global").lower().strip()

    if geo_scale not in ("continent", "region"):
        return pd.Series(True, index=df.index)

    if not focus_country:
        return pd.Series(True, index=df.index)

    row = df.loc[df["Country"] == focus_country]
    if row.empty:
        return pd.Series(True, index=df.index)

    key = row.iloc[0]["Continent" if geo_scale == "continent" else "Region"]

    return (
        df["Continent" if geo_scale == "continent" else "Region"] == key
    )
