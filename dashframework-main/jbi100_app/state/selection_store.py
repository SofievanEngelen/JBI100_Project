from __future__ import annotations

import random
from typing import TypedDict

from jbi100_app.data.constants import MAX_SELECTED_COUNTRIES


# ------------------------------------------------------------------
# Colour palettes
# ------------------------------------------------------------------
SELECTION_COLOR_POOL = [
    "rgb(213, 94, 0)",     # burnt orange
    "rgb(174, 0, 255)",    # purple
    "rgb(204, 121, 167)",  # rose
    "rgb(0, 158, 115)",    # teal-green
    "rgb(240, 228, 66)",   # yellow
    "rgb(180, 35, 24)",    # deep red
]

SELECTION_COLOR_POOL_LIGHT = [
    "rgb(241, 193, 163)",  # light burnt orange
    "rgb(220, 179, 255)",  # light purple
    "rgb(235, 203, 219)",  # light rose
    "rgb(184, 226, 214)",  # light teal-green
    "rgb(250, 244, 181)",  # light yellow
    "rgb(232, 190, 186)",  # light red
]


class SelectedCountry(TypedDict):
    country_name: str
    colour_rgb: str
    colour_rgb_light: str


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def clamp_selection(sel: list[str], limit: int = MAX_SELECTED_COUNTRIES) -> list[str]:
    out: list[str] = []
    for c in sel:
        c = str(c)
        if c and c not in out:
            out.append(c)
        if len(out) >= limit:
            break
    return out


def normalize_selection_store(sel_store) -> list[SelectedCountry]:
    if not isinstance(sel_store, list):
        return []

    seen = set()
    out: list[SelectedCountry] = []

    for item in sel_store:
        if not isinstance(item, dict):
            continue

        n = item.get("country_name")
        if not n or n in seen:
            continue

        c = item.get("colour_rgb")
        cl = item.get("colour_rgb_light")
        if not c or not cl:
            continue

        seen.add(n)
        out.append(
            {
                "country_name": n,
                "colour_rgb": c,
                "colour_rgb_light": cl,
            }
        )

        if len(out) >= MAX_SELECTED_COUNTRIES:
            break

    return out


def names_from_store(sel_store) -> list[str]:
    if not isinstance(sel_store, list):
        return []
    return clamp_selection(
        [x["country_name"] for x in sel_store if isinstance(x, dict) and x.get("country_name")],
        limit=MAX_SELECTED_COUNTRIES,
    )


def merge_selection_store(prev_store, desired_names: list[str]) -> tuple[list[SelectedCountry], bool]:
    prev_store = normalize_selection_store(prev_store)
    desired_names = clamp_selection(desired_names, limit=MAX_SELECTED_COUNTRIES)

    prev_map = {d["country_name"]: d for d in prev_store}

    used_idx: set[int] = set()
    new_store: list[SelectedCountry] = []

    # keep existing colours
    for name in desired_names:
        if name in prev_map:
            item = prev_map[name]
            idx = SELECTION_COLOR_POOL.index(item["colour_rgb"])
            used_idx.add(idx)
            new_store.append(item)

    # assign new colours
    for name in desired_names:
        if name in prev_map:
            continue

        free = [i for i in range(len(SELECTION_COLOR_POOL)) if i not in used_idx]
        if not free:
            return prev_store, False

        i = random.choice(free)
        used_idx.add(i)

        new_store.append(
            {
                "country_name": name,
                "colour_rgb": SELECTION_COLOR_POOL[i],
                "colour_rgb_light": SELECTION_COLOR_POOL_LIGHT[i],
            }
        )

    return new_store, True
