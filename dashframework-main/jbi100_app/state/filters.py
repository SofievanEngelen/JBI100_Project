# jbi100_app/state/filters.py
from __future__ import annotations

import pandas as pd


def extract_parcoords_brush_countries(parcoords_selected, work_df: pd.DataFrame) -> list[str]:
    """
    Your existing PCP selectionData -> list of country names.
    """
    if not isinstance(parcoords_selected, dict):
        return []
    pts = parcoords_selected.get("points", [])
    if not pts:
        return []

    idxs: list[int] = []
    for p in pts:
        pn = p.get("pointNumber")
        if isinstance(pn, int):
            idxs.append(pn)

    if not idxs:
        return []

    idxs = [i for i in idxs if 0 <= i < len(work_df)]
    return [str(work_df.iloc[i]["Country"]) for i in idxs]


def apply_temp_region_filter(df: pd.DataFrame, temp_region_countries: list[str] | None) -> pd.DataFrame:
    """
    If temp_region_countries is provided, filter df to those countries.
    Otherwise return df unchanged.
    """
    if df is None or df.empty:
        return df
    if not temp_region_countries:
        return df
    s = set(str(x) for x in temp_region_countries if x)
    return df[df["Country"].astype(str).isin(s)].copy()
