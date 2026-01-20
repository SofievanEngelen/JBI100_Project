from __future__ import annotations

import random
from typing import TypedDict

from jbi100_app.data.constants import (
    MAX_SELECTED_COUNTRIES,
    SELECTION_COLOUR_POOL,
    SELECTION_COLOUR_POOL_LIGHT,
)


class SelectedCountry(TypedDict):
    """
    Normalised representation of a selected country.

    Stored in Dash dcc.Store and reused across plots to ensure
    consistent colouring and ordering.
    """
    country_name: str
    colour_rgb: str
    colour_rgb_light: str


# =============================================================================
# Helpers
# =============================================================================

def clamp_selection(
    sel: list[str],
    limit: int = MAX_SELECTED_COUNTRIES,
) -> list[str]:
    """
    Clamp a list of country names to a maximum length while:

    - preserving order
    - removing duplicates
    - coercing values to strings

    Used as a defensive normalisation step throughout the app.
    """
    out: list[str] = []

    for c in sel:
        c = str(c)
        if c and c not in out:
            out.append(c)

        if len(out) >= limit:
            break

    return out


def normalise_selection_store(sel_store) -> list[SelectedCountry]:
    """
    Normalise a raw selection store into a clean list of SelectedCountry entries.

    Guarantees:
    - correct structure
    - unique country names
    - required colour fields present
    - maximum selection cap enforced

    Invalid or malformed entries are silently discarded.
    """
    if not isinstance(sel_store, list):
        return []

    seen: set[str] = set()
    out: list[SelectedCountry] = []

    for item in sel_store:
        if not isinstance(item, dict):
            continue

        name = item.get("country_name")
        if not name or name in seen:
            continue

        colour = item.get("colour_rgb")
        colour_light = item.get("colour_rgb_light")
        if not colour or not colour_light:
            continue

        seen.add(name)
        out.append(
            {
                "country_name": name,
                "colour_rgb": colour,
                "colour_rgb_light": colour_light,
            }
        )

        if len(out) >= MAX_SELECTED_COUNTRIES:
            break

    return out


def names_from_store(sel_store) -> list[str]:
    """
    Extract a clamped list of country names from a selection store.

    Safe to call with:
    - None
    - malformed data
    - partially valid entries
    """
    if not isinstance(sel_store, list):
        return []

    return clamp_selection(
        [
            x["country_name"]
            for x in sel_store
            if isinstance(x, dict) and x.get("country_name")
        ],
        limit=MAX_SELECTED_COUNTRIES,
    )


def merge_selection_store(
    prev_store,
    desired_names: list[str],
) -> tuple[list[SelectedCountry], bool]:
    """
    Merge a desired list of country names into an existing selection store.

    Behaviour:
    - preserves existing colour assignments where possible
    - assigns unused colours to newly added countries
    - enforces MAX_SELECTED_COUNTRIES
    - fails safely if the colour pool is exhausted

    Returns:
        (new_store, success)

    If success is False, the previous store should be retained.
    """
    prev_store = normalise_selection_store(prev_store)
    desired_names = clamp_selection(desired_names, limit=MAX_SELECTED_COUNTRIES)

    # Map existing selections by country name
    prev_map = {d["country_name"]: d for d in prev_store}

    used_idx: set[int] = set()
    new_store: list[SelectedCountry] = []

    # --------------------------------------------------------------
    # Preserve existing colours
    # --------------------------------------------------------------
    for name in desired_names:
        if name in prev_map:
            item = prev_map[name]
            idx = SELECTION_COLOUR_POOL.index(item["colour_rgb"])
            used_idx.add(idx)
            new_store.append(item)

    # --------------------------------------------------------------
    # Assign colours to newly added countries
    # --------------------------------------------------------------
    for name in desired_names:
        if name in prev_map:
            continue

        free = [
            i
            for i in range(len(SELECTION_COLOUR_POOL))
            if i not in used_idx
        ]

        if not free:
            # No colours left → abort and signal failure
            return prev_store, False

        i = random.choice(free)
        used_idx.add(i)

        new_store.append(
            {
                "country_name": name,
                "colour_rgb": SELECTION_COLOUR_POOL[i],
                "colour_rgb_light": SELECTION_COLOUR_POOL_LIGHT[i],
            }
        )

    return new_store, True
