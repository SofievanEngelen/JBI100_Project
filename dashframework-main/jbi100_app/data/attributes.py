# jbi100_app/data/attributes.py
from __future__ import annotations

import pandas as pd
from jbi100_app.data.data_loader import ATTRIBUTE_METADATA


def attribute_display_label(
    attr: str,
    *,
    include_category: bool = True,
    include_unit: bool = True,
) -> str:
    """
    Format:
      Category - Display_name (Unit)
    """
    if not isinstance(attr, str) or attr not in ATTRIBUTE_METADATA.index:
        return attr.replace("_", " ")

    row = ATTRIBUTE_METADATA.loc[attr]

    label = row["Display_name"]

    if include_category and pd.notna(row["Category"]):
        label = f"{row['Category']} - {label}"

    if include_unit and pd.notna(row["Unit"]):
        label = f"{label} ({row['Unit']})"

    return label


def attribute_category(attr: str) -> str | None:
    if attr in ATTRIBUTE_METADATA.index:
        return ATTRIBUTE_METADATA.loc[attr]["Category"]
    return None


def all_numeric_attributes(df):
    return [c for c in df.columns if c in ATTRIBUTE_METADATA.index]

def is_diverging_attribute(attr: str) -> bool:
    if attr not in ATTRIBUTE_METADATA.index:
        return False
    val = ATTRIBUTE_METADATA.loc[attr, "Diverging"]
    return bool(val)

def attribute_scale(attr: str) -> str:
    if attr not in ATTRIBUTE_METADATA.index:
        return "linear"
    return str(ATTRIBUTE_METADATA.loc[attr, "Scale"]).lower()

