# jbi100_app/data/attributes.py
from __future__ import annotations

import pandas as pd

from jbi100_app.data.data_loader import ATTRIBUTE_METADATA


# =============================================================================
# Attribute helpers
# =============================================================================

def attribute_display_label(
    attr: str,
    *,
    include_category: bool = True,
    include_unit: bool = True,
) -> str:
    """
    Return a human-readable display label for an attribute.

    Format:
        Category - Display name (Unit)

    Components can be selectively excluded via keyword arguments.
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
    """
    Return the category for an attribute, if available.
    """
    if attr in ATTRIBUTE_METADATA.index:
        return str(ATTRIBUTE_METADATA.loc[attr, "Category"])
    return None


def all_numeric_attributes(df: pd.DataFrame) -> list[str]:
    """
    Return all dataframe columns that correspond to numeric attributes
    defined in ATTRIBUTE_METADATA.
    """
    if df is None or df.empty:
        return []

    return [
        c for c in df.columns
        if c in ATTRIBUTE_METADATA.index
    ]


def is_diverging_attribute(attr: str) -> bool:
    """
    Return True if the attribute should use a diverging colour scale.
    """
    if attr not in ATTRIBUTE_METADATA.index:
        return False

    val = ATTRIBUTE_METADATA.loc[attr, "Diverging"]
    return bool(val)


def attribute_scale(attr: str) -> str:
    """
    Return the scale type for an attribute ("linear", "log", etc.).
    """
    if attr not in ATTRIBUTE_METADATA.index:
        return "linear"

    return str(ATTRIBUTE_METADATA.loc[attr, "Scale"]).lower()
