import os
import pandas as pd

# Folder where all CSV datasets live
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

UN_COUNTRIES = {'AFGHANISTAN', 'ALBANIA', 'ALGERIA', 'ANDORRA', 'ANGOLA', 'ANTIGUA AND BARBUDA', 'ARGENTINA', 'ARMENIA',
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
                'VENEZUELA', 'VIETNAM', 'YEMEN', 'ZAMBIA', 'ZIMBABWE'}

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

    "NORTH AMERICA": [
        "CANADA", "UNITED STATES", "MEXICO"
    ],

    "CENTRAL AMERICA": [
        "BELIZE", "COSTA RICA", "EL SALVADOR", "GUATEMALA",
        "HONDURAS", "NICARAGUA", "PANAMA"
    ],

    "CARIBBEAN": [
        "ANTIGUA AND BARBUDA", "BAHAMAS, THE", "BARBADOS", "CUBA", "DOMINICA",
        "DOMINICAN REPUBLIC", "GRENADA", "HAITI", "JAMAICA",
        "SAINT KITTS AND NEVIS", "SAINT LUCIA",
        "SAINT VINCENT AND THE GRENADINES", "TRINIDAD AND TOBAGO"
    ],

    "SOUTH AMERICA": [
        "ARGENTINA", "BOLIVIA", "BRAZIL", "CHILE", "COLOMBIA", "ECUADOR",
        "GUYANA", "PARAGUAY", "PERU", "SURINAME", "URUGUAY", "VENEZUELA"
    ],

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

    # ------------------------------------------------------------
    # AFRICA
    # ------------------------------------------------------------

    "NORTHERN AFRICA": [
        "ALGERIA",
        "EGYPT",
        "LIBYA",
        "MOROCCO",
        "SUDAN",
        "TUNISIA"
    ],

    "WESTERN AFRICA": [
        "BENIN",
        "BURKINA FASO",
        "CABO VERDE",
        "COTE D'IVOIRE",
        "GAMBIA, THE",
        "GHANA",
        "GUINEA",
        "GUINEA-BISSAU",
        "LIBERIA",
        "MALI",
        "MAURITANIA",
        "NIGER",
        "NIGERIA",
        "SENEGAL",
        "SIERRA LEONE",
        "TOGO"
    ],

    "MIDDLE AFRICA": [
        "ANGOLA",
        "CAMEROON",
        "CENTRAL AFRICAN REPUBLIC",
        "CHAD",
        "CONGO, DEMOCRATIC REPUBLIC OF THE",
        "CONGO, REPUBLIC OF THE",
        "EQUATORIAL GUINEA",
        "GABON",
        "SAO TOME AND PRINCIPE"
    ],

    "EASTERN AFRICA": [
        "BURUNDI",
        "COMOROS",
        "DJIBOUTI",
        "ERITREA",
        "ETHIOPIA",
        "KENYA",
        "MADAGASCAR",
        "MALAWI",
        "MAURITIUS",
        "MOZAMBIQUE",
        "RWANDA",
        "SEYCHELLES",
        "SOMALIA",
        "SOUTH SUDAN",
        "TANZANIA",
        "UGANDA",
        "ZAMBIA",
        "ZIMBABWE"
    ],

    "SOUTHERN AFRICA": [
        "BOTSWANA",
        "ESWATINI",
        "LESOTHO",
        "NAMIBIA",
        "SOUTH AFRICA"
    ],

    # ------------------------------------------------------------
    # AMERICAS
    # ------------------------------------------------------------

    "NORTHERN AMERICA": [
        "CANADA",
        "UNITED STATES"
    ],

    "CENTRAL AMERICA": [
        "BELIZE",
        "COSTA RICA",
        "EL SALVADOR",
        "GUATEMALA",
        "HONDURAS",
        "MEXICO",
        "NICARAGUA",
        "PANAMA"
    ],

    "CARIBBEAN": [
        "ANTIGUA AND BARBUDA",
        "BAHAMAS, THE",
        "BARBADOS",
        "CUBA",
        "DOMINICA",
        "DOMINICAN REPUBLIC",
        "GRENADA",
        "HAITI",
        "JAMAICA",
        "SAINT KITTS AND NEVIS",
        "SAINT LUCIA",
        "SAINT VINCENT AND THE GRENADINES",
        "TRINIDAD AND TOBAGO"
    ],

    "SOUTH AMERICA": [
        "ARGENTINA",
        "BOLIVIA",
        "BRAZIL",
        "CHILE",
        "COLOMBIA",
        "ECUADOR",
        "GUYANA",
        "PARAGUAY",
        "PERU",
        "SURINAME",
        "URUGUAY",
        "VENEZUELA"
    ],

    # ------------------------------------------------------------
    # ASIA
    # ------------------------------------------------------------

    "CENTRAL ASIA": [
        "KAZAKHSTAN",
        "KYRGYZSTAN",
        "TAJIKISTAN",
        "TURKMENISTAN",
        "UZBEKISTAN"
    ],

    "EASTERN ASIA": [
        "CHINA",
        "JAPAN",
        "KOREA, NORTH",
        "KOREA, SOUTH",
        "MONGOLIA"
    ],

    "SOUTH-EASTERN ASIA": [
        "BRUNEI",
        "CAMBODIA",
        "INDONESIA",
        "LAOS",
        "MALAYSIA",
        "BURMA",          # your CSV uses BURMA → normalize to MYANMAR
        "PHILIPPINES",
        "SINGAPORE",
        "THAILAND",
        "TIMOR-LESTE",
        "VIETNAM"
    ],

    "SOUTHERN ASIA": [
        "AFGHANISTAN",
        "BANGLADESH",
        "BHUTAN",
        "INDIA",
        "IRAN",
        "MALDIVES",
        "NEPAL",
        "PAKISTAN",
        "SRI LANKA"
    ],

    "WESTERN ASIA": [
        "ARMENIA",
        "AZERBAIJAN",
        "BAHRAIN",
        "CYPRUS",
        "GEORGIA",
        "IRAQ",
        "ISRAEL",
        "JORDAN",
        "KUWAIT",
        "LEBANON",
        "OMAN",
        "QATAR",
        "SAUDI ARABIA",
        "SYRIA",
        "TURKEY (TURKIYE)",
        "UNITED ARAB EMIRATES",
        "YEMEN"
    ],

    # ------------------------------------------------------------
    # EUROPE
    # ------------------------------------------------------------

    "EASTERN EUROPE": [
        "BELARUS",
        "BULGARIA",
        "CZECHIA",
        "HUNGARY",
        "MOLDOVA",
        "POLAND",
        "ROMANIA",
        "RUSSIA",
        "SLOVAKIA",
        "UKRAINE"
    ],

    "NORTHERN EUROPE": [
        "DENMARK",
        "ESTONIA",
        "FINLAND",
        "ICELAND",
        "IRELAND",
        "LATVIA",
        "LITHUANIA",
        "NORWAY",
        "SWEDEN",
        "UNITED KINGDOM"
    ],

    "SOUTHERN EUROPE": [
        "ALBANIA",
        "ANDORRA",
        "BOSNIA AND HERZEGOVINA",
        "CROATIA",
        "GREECE",
        "ITALY",
        "MALTA",
        "MONTENEGRO",
        "NORTH MACEDONIA",
        "PORTUGAL",
        "SAN MARINO",
        "SERBIA",
        "SLOVENIA",
        "SPAIN"
    ],

    "WESTERN EUROPE": [
        "AUSTRIA",
        "BELGIUM",
        "FRANCE",
        "GERMANY",
        "LIECHTENSTEIN",
        "LUXEMBOURG",
        "MONACO",
        "NETHERLANDS",
        "SWITZERLAND"
    ],

    # ------------------------------------------------------------
    # OCEANIA
    # ------------------------------------------------------------

    "AUSTRALIA AND NEW ZEALAND": [
        "AUSTRALIA",
        "NEW ZEALAND"
    ],

    "MELANESIA": [
        "FIJI",
        "PAPUA NEW GUINEA",
        "SOLOMON ISLANDS",
        "VANUATU"
    ],

    "MICRONESIA": [
        "KIRIBATI",
        "MARSHALL ISLANDS",
        "MICRONESIA, FEDERATED STATES OF",
        "NAURU",
        "PALAU"
    ],

    "POLYNESIA": [
        "SAMOA",
        "TONGA",
        "TUVALU"
    ],
}

COUNTRY_TO_REGION = {
    country: region
    for region, countries in REGIONS.items()
    for country in countries
}


def prettify_attribute(name: str) -> str:
    """Convert snake_case attribute into readable label preserving ALL CAPS parts."""
    parts = name.split("_")

    pretty = []
    for i, p in enumerate(parts):
        # Keep original all-caps segments as is
        if p.isupper():
            pretty.append(p)
        else:
            # First word uppercase, rest lowercase
            pretty.append(p.capitalize() if i == 0 else p.lower())

    return " ".join(pretty)


def normalize_country(name):
    """Normalize country strings to improve matching."""
    if not isinstance(name, str):
        return None
    return name.strip().upper()


def load_datasets():
    datasets = {}
    category_attributes = {}

    for file in os.listdir(DATA_DIR):
        if not file.endswith(".csv"):
            continue

        full_path = os.path.join(DATA_DIR, file)
        category_name = os.path.splitext(file)[0].replace("_", " ").title()

        df = pd.read_csv(full_path)

        # Normalize country column for filtering
        if "Country" in df.columns:
            df["Country"] = df["Country"].apply(normalize_country)

            # Filter to UN countries
            df = df[df["Country"].isin(UN_COUNTRIES)]

            # Add geographic metadata
            df["Continent"] = df["Country"].map(COUNTRY_TO_CONTINENT).fillna("Unknown")
            df["Region"] = df["Country"].map(COUNTRY_TO_REGION).fillna("Unknown")

        # Store cleaned dataset
        datasets[category_name] = df

        # Attributes = all columns except Country/Region/Continent
        numeric_cols = [
            col for col in df.columns
            if col.lower() not in ("country", "region", "continent") and pd.api.types.is_numeric_dtype(df[col])
        ]

        category_attributes[category_name] = [
            (col, prettify_attribute(col)) for col in numeric_cols
        ]

    return datasets, category_attributes


# Load dynamically
DATASETS, CATEGORY_ATTRIBUTES = load_datasets()

# Global list of all UN countries present in any dataset
ALL_COUNTRIES = sorted(
    {
        country
        for df in DATASETS.values()
        if "Country" in df.columns
        for country in df["Country"].dropna().unique()
    }
)

DATA_INFO = pd.read_csv("/Users/sofie/dev/Python/Uni/JBI100/dashframework-main/jbi100_app/country_info_final.csv")
