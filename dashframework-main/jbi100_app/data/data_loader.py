# jbi100_app/data/data_loader.py
from __future__ import annotations

from pathlib import Path
import pandas as pd

from jbi100_app.data.geo_utils import apply_geography

BASE_DIR = Path(__file__).resolve().parent

# ============================================================
# Load attribute metadata
# ============================================================
_ATTR_META_PATHS = [
    BASE_DIR / "attribute_metadata.csv",
    BASE_DIR.parent / "attribute_metadata.csv",
]

_ATTR_META_PATH = next((p for p in _ATTR_META_PATHS if p.exists()), None)

if _ATTR_META_PATH:
    ATTRIBUTE_METADATA = (
        pd.read_csv(_ATTR_META_PATH)
        .dropna()
        .set_index("Attribute_name")
    )
else:
    ATTRIBUTE_METADATA = pd.DataFrame(
        columns=[
            "Category",
            "Display_name",
            "Unit",
            "Description",
            "Interpretation",
        ]
    )

# ============================================================
# Load MUN dataset
# ============================================================
_DATA_PATHS = [
    BASE_DIR / "mun_dataset.csv",
    BASE_DIR.parent / "mun_dataset.csv",
]

_DATA_PATH = next((p for p in _DATA_PATHS if p.exists()), None)

DATA_INFO = pd.read_csv(_DATA_PATH) if _DATA_PATH else pd.DataFrame()

if not DATA_INFO.empty:
    DATA_INFO = apply_geography(DATA_INFO)

ALL_COUNTRIES = (
    sorted(DATA_INFO["Country"].dropna().unique().tolist())
    if not DATA_INFO.empty and "Country" in DATA_INFO.columns
    else []
)
