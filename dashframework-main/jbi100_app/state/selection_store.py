# jbi100_app/state/selection_store.py
from __future__ import annotations

import random
from typing import TypedDict

from jbi100_app.data.constants import MAX_SELECTED_COUNTRIES, SELECTION_COLOR_POOL


class SelectedCountry(TypedDict):
    country_name: str
    colour_rgb: str


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
    """
    Ensures selection store is a list[{country_name, colour_rgb}] with:
    - no duplicate names
    - no duplicate colours
    - max length limit
    """
    if not isinstance(sel_store, list):
        return []

    seen_names = set()
    seen_colours = set()
    out: list[SelectedCountry] = []

    for item in sel_store:
        if not isinstance(item, dict):
            continue
        n = item.get("country_name")
        c = item.get("colour_rgb")
        if not n or not c:
            continue

        n = str(n)
        c = str(c)

        if n in seen_names:
            continue
        if c in seen_colours:
            continue

        seen_names.add(n)
        seen_colours.add(c)
        out.append({"country_name": n, "colour_rgb": c})

        if len(out) >= MAX_SELECTED_COUNTRIES:
            break

    return out


def names_from_store(sel_store) -> list[str]:
    if not isinstance(sel_store, list):
        return []
    return clamp_selection(
        [str(x.get("country_name")) for x in sel_store if isinstance(x, dict) and x.get("country_name")],
        limit=MAX_SELECTED_COUNTRIES,
    )


def merge_selection_store(prev_store, desired_names: list[str]) -> tuple[list[SelectedCountry], bool]:
    """
    Keeps stable colours for countries already selected.
    Assigns new colours to new countries (from pool).
    Returns (new_store, ok) where ok=False means "ran out of colours".
    """
    prev_store = normalize_selection_store(prev_store)
    desired_names = clamp_selection(desired_names, limit=MAX_SELECTED_COUNTRIES)

    prev_map = {d["country_name"]: d["colour_rgb"] for d in prev_store}

    new_store: list[SelectedCountry] = []
    used_colours: set[str] = set()

    # keep existing colours
    for name in desired_names:
        if name in prev_map:
            col = prev_map[name]
            if col in used_colours:
                continue
            new_store.append({"country_name": name, "colour_rgb": col})
            used_colours.add(col)

    # assign new colours
    for name in desired_names:
        if name in prev_map:
            continue
        free = [c for c in SELECTION_COLOR_POOL if c not in used_colours]
        if not free:
            return prev_store, False
        col = random.choice(free)
        new_store.append({"country_name": name, "colour_rgb": col})
        used_colours.add(col)

    return new_store, True
