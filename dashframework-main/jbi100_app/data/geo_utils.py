# jbi100_app/data/geo_utils.py
from __future__ import annotations

import pandas as pd


def geo_mask(df: pd.DataFrame, geo_scale: str, focus_country: str | None) -> pd.Series:
    """
    Returns a boolean mask aligned with df.index indicating which rows are "in-scope"
    given a geo_scale and a focus_country.

    geo_scale:
      - "global": everything in scope
      - "continent": rows matching focus country's continent
      - "region": rows matching focus country's region
    """
    if df is None or df.empty:
        return pd.Series([], dtype=bool)

    geo_scale = (geo_scale or "global").lower().strip()
    if geo_scale not in ("continent", "region"):
        return pd.Series([True] * len(df), index=df.index)

    if not focus_country or "Country" not in df.columns:
        return pd.Series([True] * len(df), index=df.index)

    row = df.loc[df["Country"] == focus_country]
    if row.empty:
        return pd.Series([True] * len(df), index=df.index)

    if geo_scale == "continent":
        key = row.iloc[0].get("Continent")
        if key is None:
            return pd.Series([True] * len(df), index=df.index)
        return df["Continent"] == key

    key = row.iloc[0].get("Region")
    if key is None:
        return pd.Series([True] * len(df), index=df.index)
    return df["Region"] == key
