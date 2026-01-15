# jbi100_app/data/category_mapping.py

from __future__ import annotations

# Keep ONLY numeric, comparable indicators for multivariate analysis.
# Remove non-numeric fields (e.g., government_type) from PCP/distribution defaults.

UI_CATEGORIES = {
    "economy": [
        "unemployment_pct",
        "gdp_nominal_bil_usd",
        "gdp_per_capita_usd",
        "trade_openness_ratio",
        "gdp_growth_rate_pct",
        "government_debt_pct_gdp_pct",
    ],
    "energy_environment": [
        "co2_total_Mt",
        "co2_intensity_tonnes_per_usd",
        "co2_per_capita_tonnes",
    ],
    "geography_politics": [
        "land_area_km2",
    ],
    "population_society": [
        "birth_rate_per_1000",
        "literacy_rate_pct",
        "pop_density_per_km2",
        "infant_mortality_per_1000",
        "median_age_years",
        "total_fertility_rate",
    ],
    "communication_infrastructure": [
        "internet_users_total",
        "digital_access_index",
    ],
}

UI_CATEGORY_LABELS = [
    ("economy", "Economy"),
    ("environment", "Energy & environment"),
    ("population", "Population & society"),
    ("geography", "Geography & politics"),
    ("infrastructure", "Communication & infrastructure"),
]

# Final version does NOT use multi-dataset loading as core logic.
# Keep for compatibility with any leftover imports, but it is not required by the simplified tool.
UI_TO_DATASET_KEYS = {
    "economy": ["Economy"],
    "energy_env": ["Energy", "Environment", "Energy And Environment"],
    "population_society": ["Population", "Demographics", "Population And Society"],
    "geography_politics": ["Geography", "Government", "Geography And Politics"],
    "comm_infra": ["Communication", "Infrastructure", "Transportation"],
}
