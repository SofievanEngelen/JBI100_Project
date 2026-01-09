# jbi100_app/state/filters.py
from __future__ import annotations

import re
from typing import Any

import pandas as pd


_CONSTRAINT_KEY_RE = re.compile(r"^dimensions\[(\d+)\]\.constraintrange$")


def parse_parcoords_constraintrange_patch(restyle_data: Any) -> tuple[dict[str, list[list[float]]], bool]:
    """
    Parse Plotly Parcoords restyleData into an incremental constraintrange PATCH.

    Returns:
      (patch, saw_constraint_key)

    patch schema (JSON friendly):
      { "<dim_idx>": [[lo, hi], [lo2, hi2], ...] }
    If a constraint was cleared for a dimension, patch will contain:
      { "<dim_idx>": [] }

    saw_constraint_key is False if the restyle event did NOT include any
    dimensions[i].constraintrange keys (so you can ignore it).
    """
    if not restyle_data:
        return {}, False

    # restyleData is typically: [update_dict, trace_indexes]
    update = None
    if isinstance(restyle_data, (list, tuple)) and len(restyle_data) >= 1 and isinstance(restyle_data[0], dict):
        update = restyle_data[0]
    elif isinstance(restyle_data, dict):
        update = restyle_data
    else:
        return {}, False

    patch: dict[str, list[list[float]]] = {}
    saw = False

    for k, v in update.items():
        m = _CONSTRAINT_KEY_RE.match(str(k))
        if not m:
            continue

        saw = True
        dim_idx = str(int(m.group(1)))

        # Cleared
        if v is None or v == []:
            patch[dim_idx] = []
            continue

        ranges = v

        # Common extra nesting: [[[lo, hi]]] -> [[lo, hi]]
        if (
            isinstance(ranges, list)
            and len(ranges) == 1
            and isinstance(ranges[0], list)
            and len(ranges[0]) == 1
            and isinstance(ranges[0][0], (list, tuple))
            and len(ranges[0][0]) == 2
        ):
            ranges = ranges[0]

        parsed: list[list[float]] = []
        if isinstance(ranges, (list, tuple)):
            for r in ranges:
                if isinstance(r, (list, tuple)) and len(r) == 2:
                    lo, hi = r
                    try:
                        lo_f = float(lo)
                        hi_f = float(hi)
                    except Exception:
                        continue
                    if hi_f < lo_f:
                        lo_f, hi_f = hi_f, lo_f
                    parsed.append([lo_f, hi_f])

        # If parsing failed, treat it as no-op for that dim (do not clear)
        # But since this was a constraintrange key, we still record it as empty only
        # if it's truly empty in the payload. Otherwise keep parsed (may be empty).
        patch[dim_idx] = parsed

    return patch, saw


def countries_from_parcoords_constraints(
    work_df: pd.DataFrame,
    dims: list[str],
    constraints: dict[str, list[list[float]]],
) -> list[str]:
    """
    Apply accumulated parcoords constraints across ALL constrained dimensions.

    - work_df must contain "Country" and the dimension columns in the PCP's order.
    - values should be normalized to 0..1 (because constraintrange is in displayed scale).
    - constraints keys are dimension indices as strings (JSON friendly).
    """
    if work_df is None or work_df.empty or "Country" not in work_df.columns:
        return []

    if not dims:
        dims = [c for c in work_df.columns if c != "Country"]

    if not constraints:
        return []

    mask = pd.Series(True, index=work_df.index)
    any_active = False

    for dim_idx_str, ranges in constraints.items():
        if not ranges:
            continue

        try:
            dim_idx = int(dim_idx_str)
        except Exception:
            continue

        if dim_idx < 0 or dim_idx >= len(dims):
            continue

        any_active = True
        col = dims[dim_idx]
        col_vals = work_df[col]

        # OR within dimension across disjoint ranges
        dim_ok = pd.Series(False, index=work_df.index)
        for lo, hi in ranges:
            dim_ok = dim_ok | ((col_vals >= lo) & (col_vals <= hi))

        # AND across dimensions
        mask = mask & dim_ok

    if not any_active:
        return []

    return work_df.loc[mask, "Country"].astype(str).tolist()


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
