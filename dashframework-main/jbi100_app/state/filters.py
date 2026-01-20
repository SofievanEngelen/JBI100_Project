from __future__ import annotations

import re
from typing import Any

import pandas as pd


# Matches Plotly parcoords constraintrange keys such as:
#   dimensions[0].constraintrange
_CONSTRAINT_KEY_RE = re.compile(r"^dimensions\[(\d+)\]\.constraintrange$")


def parse_parcoords_constraintrange_patch(
    restyle_data: Any,
) -> tuple[dict[str, list[list[float]]], bool]:
    """
    Parse Plotly Parcoords restyleData into an incremental constraintrange patch.

    Returns:
        (patch, saw_constraint_key)

    Patch schema (JSON-friendly), keyed by dimension INDEX as a string:
        { "<dim_idx>": [[lo, hi], [lo2, hi2], ...] }

    If a constraint was cleared for a dimension, the patch will contain:
        { "<dim_idx>": [] }

    saw_constraint_key is False if the restyle event did NOT include any
    dimensions[i].constraintrange keys (so it can be safely ignored).
    """
    if not restyle_data:
        return {}, False

    # restyleData is typically: [update_dict, trace_indices]
    update: dict[str, Any] | None = None

    if (
        isinstance(restyle_data, (list, tuple))
        and len(restyle_data) >= 1
        and isinstance(restyle_data[0], dict)
    ):
        update = restyle_data[0]
    elif isinstance(restyle_data, dict):
        update = restyle_data
    else:
        return {}, False

    patch: dict[str, list[list[float]]] = {}
    saw_constraint_key = False

    for key, value in update.items():
        match = _CONSTRAINT_KEY_RE.match(str(key))
        if not match:
            continue

        saw_constraint_key = True
        dim_idx = str(int(match.group(1)))

        # Constraint cleared
        if value is None or value == []:
            patch[dim_idx] = []
            continue

        ranges = value

        # Common extra nesting: [[[lo, hi]]] → [[lo, hi]]
        if (
            isinstance(ranges, list)
            and len(ranges) == 1
            and isinstance(ranges[0], list)
            and len(ranges[0]) == 1
            and isinstance(ranges[0][0], (list, tuple))
            and len(ranges[0][0]) == 2
        ):
            ranges = ranges[0]

        parsed_ranges: list[list[float]] = []

        if isinstance(ranges, (list, tuple)):
            for r in ranges:
                if not (isinstance(r, (list, tuple)) and len(r) == 2):
                    continue

                lo, hi = r
                try:
                    lo_f = float(lo)
                    hi_f = float(hi)
                except Exception:
                    continue

                # Ensure lo <= hi
                if hi_f < lo_f:
                    lo_f, hi_f = hi_f, lo_f

                parsed_ranges.append([lo_f, hi_f])

        patch[dim_idx] = parsed_ranges

    return patch, saw_constraint_key


def countries_from_parcoords_constraints(
    work_df: pd.DataFrame,
    dims: list[str],
    constraints: dict[str, list[list[float]]],
) -> list[str]:
    """
    Apply accumulated Parallel Coordinates constraints across all dimensions.

    Notes:
    - Constraints are keyed by DIMENSION NAME (column name), not index:
        { "gdp_per_capita_usd": [[0.2, 0.4]] }

    - work_df must contain a "Country" column and the constrained dimensions.
    - Values are expected to be normalised to 0..1, as constraintrange
      operates on the displayed (scaled) values.
    """
    if work_df is None or work_df.empty or "Country" not in work_df.columns:
        return []

    if not dims:
        dims = [c for c in work_df.columns if c != "Country"]

    if not constraints:
        return []

    mask = pd.Series(True, index=work_df.index)
    any_constraint_active = False

    for col, ranges in constraints.items():
        if not ranges:
            continue

        col = str(col)
        if col not in work_df.columns:
            continue

        any_constraint_active = True
        col_values = work_df[col]

        # OR within a dimension across disjoint ranges
        dim_mask = pd.Series(False, index=work_df.index)
        for lo, hi in ranges:
            dim_mask = dim_mask | ((col_values >= lo) & (col_values <= hi))

        # AND across dimensions
        mask = mask & dim_mask

    if not any_constraint_active:
        return []

    return work_df.loc[mask, "Country"].astype(str).tolist()


def apply_temp_region_filter(
    df: pd.DataFrame,
    temp_region_countries: list[str] | None,
) -> pd.DataFrame:
    """
    Apply a temporary region filter to the DataFrame.

    If temp_region_countries is provided, only those countries are retained.
    Otherwise, the DataFrame is returned unchanged.
    """
    if df is None or df.empty:
        return df

    if not temp_region_countries:
        return df

    allowed = {str(x) for x in temp_region_countries if x}
    return df[df["Country"].astype(str).isin(allowed)].copy()
