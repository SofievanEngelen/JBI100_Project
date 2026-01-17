# jbi100_app/plots/common.py
from __future__ import annotations

import numpy as np
import pandas as pd

from jbi100_app.data.attributes import all_numeric_attributes


def coerce_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def pick_pcp_dims(df: pd.DataFrame, max_dims: int = 8) -> list[str]:
    cols = all_numeric_attributes(df)
    return cols[:max_dims]


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