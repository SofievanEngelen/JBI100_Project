# jbi100_app/data/data_loader.py
from __future__ import annotations

from pathlib import Path
import os
import pandas as pd

# ============================================================
# Paths
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

# Optional multi-csv folder: jbi100_app/data/data/
DATA_DIR_PATH = BASE_DIR / "data"
if not DATA_DIR_PATH.exists():
    DATA_DIR_PATH = BASE_DIR
DATA_DIR = str(DATA_DIR_PATH)

# ============================================================
# UN countries list (unchanged)
# ============================================================
UN_COUNTRIES = {
    'AFGHANISTAN', 'ALBANIA', 'ALGERIA', 'ANDORRA', 'ANGOLA', 'ANTIGUA AND BARBUDA', 'ARGENTINA', 'ARMENIA',
    'AUSTRALIA', 'AUSTRIA', 'AZERBAIJAN', 'BAHAMAS, THE', 'BAHRAIN', 'BANGLADESH', 'BARBADOS', 'BELARUS',
    'BELGIUM', 'BELIZE', 'BENIN', 'BHUTAN', 'BOLIVIA', 'BOSNIA AND HERZEGOVINA', 'BOTSWANA', 'BRAZIL',
    'BRUNEI', 'BULGARIA', 'BURKINA FASO', 'BURUNDI', 'CABO VERDE', 'CAMBODIA', 'CAMEROON', 'CANADA',
    'CENTRAL AFRICAN REPUBLIC', 'CHAD', 'CHILE', 'CHINA', 'COLOMBIA', 'COMOROS', 'CONGO, REPUBLIC OF THE',
    'COSTA RICA', "COTE D'IVOIRE", 'CROATIA', 'CUBA', 'CYPRUS', 'CZECHIA', 'KOREA, NORTH',
    'CONGO, DEMOCRATIC REPUBLIC OF THE', 'DENMARK', 'DJIBOUTI', 'DOMINICA', 'DOMINICAN REPUBLIC', 'ECUADOR',
    'EGYPT', 'EL SALVADOR', 'EQUATORIAL GUINEA', 'ERITREA', 'ESTONIA', 'ESWATINI', 'ETHIOPIA', 'FIJI',
    'FINLAND', 'FRANCE', 'GABON', 'GAMBIA, THE', 'GEORGIA', 'GERMANY', 'GHANA', 'GREECE', 'GRENADA',
    'GUATEMALA', 'GUINEA', 'GUINEA-BISSAU', 'GUYANA', 'HAITI', 'HONDURAS', 'HUNGARY', 'ICELAND', 'INDIA',
    'INDONESIA', 'IRAN', 'IRAQ', 'IRELAND', 'ISRAEL', 'ITALY', 'JAMAICA', 'JAPAN', 'JORDAN', 'KAZAKHSTAN',
    'KENYA', 'KIRIBATI', 'KUWAIT', 'KYRGYZSTAN', 'LAOS', 'LATVIA', 'LEBANON', 'LESOTHO', 'LIBERIA', 'LIBYA',
    'LIECHTENSTEIN', 'LITHUANIA', 'LUXEMBOURG', 'MADAGASCAR', 'MALAWI', 'MALAYSIA', 'MALDIVES', 'MALI',
    'MALTA', 'MARSHALL ISLANDS', 'MAURITANIA', 'MAURITIUS', 'MEXICO', 'MICRONESIA, FEDERATED STATES OF',
    'MONACO', 'MONGOLIA', 'MONTENEGRO', 'MOROCCO', 'MOZAMBIQUE', 'BURMA', 'NAMIBIA', 'NAURU', 'NEPAL',
    'NETHERLANDS', 'NEW ZEALAND', 'NICARAGUA', 'NIGER', 'NIGERIA', 'NORTH MACEDONIA', 'NORWAY', 'OMAN',
    'PAKISTAN', 'PALAU', 'PANAMA', 'PAPUA NEW GUINEA', 'PARAGUAY', 'PERU', 'PHILIPPINES', 'POLAND',
    'PORTUGAL', 'QATAR', 'KOREA, SOUTH', 'MOLDOVA', 'ROMANIA', 'RUSSIA', 'RWANDA', 'SAINT KITTS AND NEVIS',
    'SAINT LUCIA', 'SAINT VINCENT AND THE GRENADINES', 'SAMOA', 'SAN MARINO', 'SAO TOME AND PRINCIPE',
    'SAUDI ARABIA', 'SENEGAL', 'SERBIA', 'SEYCHELLES', 'SIERRA LEONE', 'SINGAPORE', 'SLOVAKIA', 'SLOVENIA',
    'SOLOMON ISLANDS', 'SOMALIA', 'SOUTH AFRICA', 'SOUTH SUDAN', 'SPAIN', 'SRI LANKA', 'SUDAN', 'SURINAME',
    'SWEDEN', 'SWITZERLAND', 'SYRIA', 'TAJIKISTAN', 'TANZANIA', 'THAILAND', 'TIMOR-LESTE', 'TOGO', 'TONGA',
    'TRINIDAD AND TOBAGO', 'TUNISIA', 'TURKEY (TURKIYE)', 'TURKMENISTAN', 'TUVALU', 'UGANDA', 'UKRAINE',
    'UNITED ARAB EMIRATES', 'UNITED KINGDOM', 'UNITED STATES', 'URUGUAY', 'UZBEKISTAN', 'VANUATU',
    'VENEZUELA', 'VIETNAM', 'YEMEN', 'ZAMBIA', 'ZIMBABWE'
}

# ============================================================
# Continents / Regions dictionaries (unchanged)
# ============================================================
CONTINENTS = {
    "AFRICA": [
        "ALGERIA", "ANGOLA", "BENIN", "BOTSWANA", "BURKINA FASO", "BURUNDI",
        "CABO VERDE", "CAMEROON", "CENTRAL AFRICAN REPUBLIC", "CHAD", "COMOROS",
        "CONGO, DEMOCRATIC REPUBLIC OF THE", "CONGO, REPUBLIC OF THE",
        "COTE D'IVOIRE", "DJIBOUTI", "EGYPT", "EQUATORIAL GUINEA", "ERITREA",
        "ESWATINI", "ETHIOPIA", "GABON", "GAMBIA, THE", "GHANA", "GUINEA",
        "GUINEA-BISSAU", "KENYA", "LESOTHO", "LIBERIA", "LIBYA", "MADAGASCAR",
        "MALAWI", "MALI", "MAURITANIA", "MAURITIUS", "MOROCCO", "MOZAMBIQUE",
        "NAMIBIA", "NIGER", "NIGERIA", "RWANDA", "SAO TOME AND PRINCIPE",
        "SENEGAL", "SEYCHELLES", "SIERRA LEONE", "SOMALIA", "SOUTH AFRICA",
        "SOUTH SUDAN", "SUDAN", "TANZANIA", "TOGO", "TUNISIA", "UGANDA",
        "ZAMBIA", "ZIMBABWE"
    ],
    "ASIA": [
        "AFGHANISTAN", "ARMENIA", "AZERBAIJAN", "BAHRAIN", "BANGLADESH",
        "BHUTAN", "BRUNEI", "CAMBODIA", "CHINA", "CYPRUS", "GEORGIA", "INDIA",
        "INDONESIA", "IRAN", "IRAQ", "ISRAEL", "JAPAN", "JORDAN", "KAZAKHSTAN",
        "KOREA, NORTH", "KOREA, SOUTH", "KUWAIT", "KYRGYZSTAN", "LAOS",
        "LEBANON", "MALAYSIA", "MALDIVES", "MONGOLIA", "MYANMAR", "NEPAL",
        "OMAN", "PAKISTAN", "PHILIPPINES", "QATAR", "SAUDI ARABIA", "SINGAPORE",
        "SRI LANKA", "SYRIA", "TAJIKISTAN", "THAILAND", "TIMOR-LESTE",
        "TURKEY (TURKIYE)", "TURKMENISTAN", "UNITED ARAB EMIRATES", "UZBEKISTAN",
        "VIETNAM", "YEMEN"
    ],
    "EUROPE": [
        "ALBANIA", "ANDORRA", "AUSTRIA", "BELARUS", "BELGIUM",
        "BOSNIA AND HERZEGOVINA", "BULGARIA", "CROATIA", "CZECHIA",
        "DENMARK", "ESTONIA", "FINLAND", "FRANCE", "GERMANY", "GREECE",
        "HUNGARY", "ICELAND", "IRELAND", "ITALY", "LATVIA", "LIECHTENSTEIN",
        "LITHUANIA", "LUXEMBOURG", "MALTA", "MOLDOVA", "MONACO", "MONTENEGRO",
        "NETHERLANDS", "NORTH MACEDONIA", "NORWAY", "POLAND", "PORTUGAL",
        "ROMANIA", "RUSSIA", "SAN MARINO", "SERBIA", "SLOVAKIA", "SLOVENIA",
        "SPAIN", "SWEDEN", "SWITZERLAND", "UKRAINE", "UNITED KINGDOM"
    ],
    "NORTH AMERICA": ["CANADA", "UNITED STATES", "MEXICO"],
    "SOUTH AMERICA": ["ARGENTINA", "BOLIVIA", "BRAZIL", "CHILE", "COLOMBIA", "ECUADOR", "GUYANA", "PARAGUAY",
                      "PERU", "SURINAME", "URUGUAY", "VENEZUELA", "ANTIGUA AND BARBUDA", "BAHAMAS, THE", "BARBADOS", "CUBA", "DOMINICA",
        "DOMINICAN REPUBLIC", "GRENADA", "HAITI", "JAMAICA",
        "SAINT KITTS AND NEVIS", "SAINT LUCIA", "SAINT VINCENT AND THE GRENADINES", "BELIZE", "COSTA RICA", "EL SALVADOR", "GUATEMALA", "HONDURAS", "NICARAGUA", "PANAMA"
        "TRINIDAD AND TOBAGO"],
    "OCEANIA": [
        "AUSTRALIA", "FIJI", "KIRIBATI", "MARSHALL ISLANDS",
        "MICRONESIA, FEDERATED STATES OF", "NAURU", "NEW ZEALAND",
        "PALAU", "PAPUA NEW GUINEA", "SAMOA", "SOLOMON ISLANDS",
        "TONGA", "TUVALU", "VANUATU"
    ],
}

COUNTRY_TO_CONTINENT = {
    country: continent
    for continent, countries in CONTINENTS.items()
    for country in countries
}

REGIONS = {
    "NORTHERN AFRICA": ["ALGERIA", "EGYPT", "LIBYA", "MOROCCO", "SUDAN", "TUNISIA"],
    "WESTERN AFRICA": [
        "BENIN", "BURKINA FASO", "CABO VERDE", "COTE D'IVOIRE", "GAMBIA, THE",
        "GHANA", "GUINEA", "GUINEA-BISSAU", "LIBERIA", "MALI", "MAURITANIA",
        "NIGER", "NIGERIA", "SENEGAL", "SIERRA LEONE", "TOGO"
    ],
    "MIDDLE AFRICA": [
        "ANGOLA", "CAMEROON", "CENTRAL AFRICAN REPUBLIC", "CHAD",
        "CONGO, DEMOCRATIC REPUBLIC OF THE", "CONGO, REPUBLIC OF THE",
        "EQUATORIAL GUINEA", "GABON", "SAO TOME AND PRINCIPE"
    ],
    "EASTERN AFRICA": [
        "BURUNDI", "COMOROS", "DJIBOUTI", "ERITREA", "ETHIOPIA", "KENYA", "MADAGASCAR",
        "MALAWI", "MAURITIUS", "MOZAMBIQUE", "RWANDA", "SEYCHELLES", "SOMALIA",
        "SOUTH SUDAN", "TANZANIA", "UGANDA", "ZAMBIA", "ZIMBABWE"
    ],
    "SOUTHERN AFRICA": ["BOTSWANA", "ESWATINI", "LESOTHO", "NAMIBIA", "SOUTH AFRICA"],
    "NORTHERN AMERICA": ["CANADA", "UNITED STATES"],
    "CENTRAL AMERICA": ["BELIZE", "COSTA RICA", "EL SALVADOR", "GUATEMALA", "HONDURAS", "MEXICO", "NICARAGUA", "PANAMA"],
    "CARIBBEAN": [
        "ANTIGUA AND BARBUDA", "BAHAMAS, THE", "BARBADOS", "CUBA", "DOMINICA",
        "DOMINICAN REPUBLIC", "GRENADA", "HAITI", "JAMAICA", "SAINT KITTS AND NEVIS",
        "SAINT LUCIA", "SAINT VINCENT AND THE GRENADINES", "TRINIDAD AND TOBAGO"
    ],
    "SOUTH AMERICA": ["ARGENTINA", "BOLIVIA", "BRAZIL", "CHILE", "COLOMBIA", "ECUADOR", "GUYANA", "PARAGUAY", "PERU", "SURINAME", "URUGUAY", "VENEZUELA"],
    "CENTRAL ASIA": ["KAZAKHSTAN", "KYRGYZSTAN", "TAJIKISTAN", "TURKMENISTAN", "UZBEKISTAN"],
    "EASTERN ASIA": ["CHINA", "JAPAN", "KOREA, NORTH", "KOREA, SOUTH", "MONGOLIA"],
    "SOUTH-EASTERN ASIA": ["BRUNEI", "CAMBODIA", "INDONESIA", "LAOS", "MALAYSIA", "BURMA", "PHILIPPINES", "SINGAPORE", "THAILAND", "TIMOR-LESTE", "VIETNAM"],
    "SOUTHERN ASIA": ["AFGHANISTAN", "BANGLADESH", "BHUTAN", "INDIA", "IRAN", "MALDIVES", "NEPAL", "PAKISTAN", "SRI LANKA"],
    "WESTERN ASIA": [
        "ARMENIA", "AZERBAIJAN", "BAHRAIN", "CYPRUS", "GEORGIA", "IRAQ", "ISRAEL",
        "JORDAN", "KUWAIT", "LEBANON", "OMAN", "QATAR", "SAUDI ARABIA", "SYRIA",
        "TURKEY (TURKIYE)", "UNITED ARAB EMIRATES", "YEMEN"
    ],
    "EASTERN EUROPE": ["BELARUS", "BULGARIA", "CZECHIA", "HUNGARY", "MOLDOVA", "POLAND", "ROMANIA", "RUSSIA", "SLOVAKIA", "UKRAINE"],
    "NORTHERN EUROPE": ["DENMARK", "ESTONIA", "FINLAND", "ICELAND", "IRELAND", "LATVIA", "LITHUANIA", "NORWAY", "SWEDEN", "UNITED KINGDOM"],
    "SOUTHERN EUROPE": ["ALBANIA", "ANDORRA", "BOSNIA AND HERZEGOVINA", "CROATIA", "GREECE", "ITALY", "MALTA", "MONTENEGRO", "NORTH MACEDONIA", "PORTUGAL", "SAN MARINO", "SERBIA", "SLOVENIA", "SPAIN"],
    "WESTERN EUROPE": ["AUSTRIA", "BELGIUM", "FRANCE", "GERMANY", "LIECHTENSTEIN", "LUXEMBOURG", "MONACO", "NETHERLANDS", "SWITZERLAND"],
    "AUSTRALIA AND NEW ZEALAND": ["AUSTRALIA", "NEW ZEALAND"],
    "MELANESIA": ["FIJI", "PAPUA NEW GUINEA", "SOLOMON ISLANDS", "VANUATU"],
    "MICRONESIA": ["KIRIBATI", "MARSHALL ISLANDS", "MICRONESIA, FEDERATED STATES OF", "NAURU", "PALAU"],
    "POLYNESIA": ["SAMOA", "TONGA", "TUVALU"],
}

COUNTRY_TO_REGION = {
    country: region
    for region, countries in REGIONS.items()
    for country in countries
}

# ============================================================
# Helpers
# ============================================================
def prettify_attribute(name: str) -> str:
    parts = name.split("_")
    pretty = []
    for i, p in enumerate(parts):
        if p.isupper():
            pretty.append(p)
        else:
            pretty.append(p.capitalize() if i == 0 else p.lower())
    return " ".join(pretty)


def normalize_country_key(name: object) -> str:
    if not isinstance(name, str):
        return ""
    return name.strip().upper()


def normalize_country_display(name: object) -> str:
    if not isinstance(name, str):
        return ""
    return name.strip()

# ============================================================
# MUN dataset (single-table source)
# ============================================================
_MUN_CANDIDATES = [
    BASE_DIR / "mun_dataset.csv",
    BASE_DIR.parent / "mun_dataset.csv",
]
_MUN_PATH = next((p for p in _MUN_CANDIDATES if p.exists()), None)

if _MUN_PATH is not None:
    DATA_INFO = pd.read_csv(_MUN_PATH)
else:
    DATA_INFO = pd.DataFrame()

if not DATA_INFO.empty and "Country" in DATA_INFO.columns:
    DATA_INFO["Country"] = DATA_INFO["Country"].apply(normalize_country_display)
    DATA_INFO["_CountryKey"] = DATA_INFO["Country"].apply(normalize_country_key)

    DATA_INFO = DATA_INFO[DATA_INFO["_CountryKey"].isin(UN_COUNTRIES)].copy()

    DATA_INFO["Continent"] = DATA_INFO["_CountryKey"].map(COUNTRY_TO_CONTINENT).fillna("Unknown")
    DATA_INFO["Region"] = DATA_INFO["_CountryKey"].map(COUNTRY_TO_REGION).fillna("Unknown")
else:
    if DATA_INFO.empty:
        DATA_INFO = pd.DataFrame(columns=["Country", "Continent", "Region"])

if not DATA_INFO.empty and "Country" in DATA_INFO.columns:
    ALL_COUNTRIES = sorted([c for c in DATA_INFO["Country"].dropna().unique().tolist() if str(c).strip() != ""])
else:
    ALL_COUNTRIES = []

# ============================================================
# Optional: load multi-csv datasets (safe)
# ============================================================
def load_datasets():
    datasets: dict[str, pd.DataFrame] = {}
    category_attributes: dict[str, list[tuple[str, str]]] = {}

    if not os.path.isdir(DATA_DIR):
        return datasets, category_attributes

    for file in os.listdir(DATA_DIR):
        if not file.endswith(".csv"):
            continue

        if file.lower() == "mun_dataset.csv":
            continue

        full_path = os.path.join(DATA_DIR, file)
        category_name = os.path.splitext(file)[0].replace("_", " ").title()

        try:
            df = pd.read_csv(full_path)
        except Exception:
            continue

        if "Country" in df.columns:
            df["Country"] = df["Country"].apply(normalize_country_key)
            df = df[df["Country"].isin(UN_COUNTRIES)].copy()
            df["Continent"] = df["Country"].map(COUNTRY_TO_CONTINENT).fillna("Unknown")
            df["Region"] = df["Country"].map(COUNTRY_TO_REGION).fillna("Unknown")

        datasets[category_name] = df

        numeric_cols = [
            col for col in df.columns
            if col.lower() not in ("country", "region", "continent") and pd.api.types.is_numeric_dtype(df[col])
        ]
        category_attributes[category_name] = [(col, prettify_attribute(col)) for col in numeric_cols]

    return datasets, category_attributes


DATASETS, CATEGORY_ATTRIBUTES = load_datasets()
