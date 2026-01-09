# jbi100_app/plots/common.py
from __future__ import annotations

import numpy as np
import pandas as pd

from jbi100_app.data.constants import META_COLS
from jbi100_app.data.category_mapping import UI_CATEGORIES


def coerce_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def pretty_metric(name: str) -> str:
    return str(name).replace("_", " ")


def all_numeric_metrics(df: pd.DataFrame) -> list[str]:
    cols: list[str] = []
    for c in df.columns:
        if c in META_COLS:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            cols.append(c)
    return cols


def metric_cols_for_category(df: pd.DataFrame, ui_category: str | None) -> list[str]:
    all_cols = all_numeric_metrics(df)
    if not ui_category:
        return all_cols
    allowed = UI_CATEGORIES.get(ui_category, [])
    return [c for c in allowed if c in all_cols]


def pick_pcp_dims(df: pd.DataFrame, ui_category: str | None, max_dims: int = 8) -> list[str]:
    cols = metric_cols_for_category(df, ui_category)
    if len(cols) < 2:
        cols = all_numeric_metrics(df)
    return [c for c in cols if c in df.columns][:max_dims]


def prepare_hist_bins(x: np.ndarray, bins: int = 30) -> tuple[np.ndarray, float, float, float]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return np.linspace(0.0, 1.0, 50), 0.02, 0.0, 1.0

    lo = float(np.min(x))
    hi = float(np.max(x))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        lo = float(np.median(x))
        hi = lo + 1.0

    pad = 0.02 * (hi - lo)
    lo2 = lo - pad
    hi2 = hi + pad
    edges = np.linspace(lo2, hi2, bins + 1)
    bin_width = float(edges[1] - edges[0])
    grid = np.linspace(lo2, hi2, 240)
    return grid, bin_width, lo2, hi2


def kde_counts(x: np.ndarray, grid: np.ndarray, bin_width: float, bw: float | None = None) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = int(x.size)
    if n < 2:
        return np.zeros_like(grid, dtype=float)

    if bw is None:
        std = float(np.std(x, ddof=1)) if n > 1 else 0.0
        bw = 1.06 * std * (n ** (-1 / 5)) if std > 0 else 1.0

    bw = float(bw)
    if not np.isfinite(bw) or bw <= 0:
        bw = 1.0

    diffs = (grid[:, None] - x[None, :]) / bw
    kern = np.exp(-0.5 * diffs * diffs) / (np.sqrt(2 * np.pi) * bw)
    pdf = np.mean(kern, axis=1)
    return pdf * n * float(bin_width)