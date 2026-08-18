"""Fixed-budget sampling strategies that never inspect test labels."""

from __future__ import annotations

import heapq
from collections import Counter, defaultdict

import numpy as np
import pandas as pd


def initial_sample(n_rows: int, fraction: float, seed: int) -> np.ndarray:
    """Select the shared initial sample by positional index."""
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    size = max(1, int(np.ceil(n_rows * fraction)))
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n_rows, size=size, replace=False))


def random_acquisition_order(
    n_rows: int, initial_positions: np.ndarray, seed: int
) -> np.ndarray:
    """Return a reproducible random order for all remaining candidates."""
    remaining = np.setdiff1d(
        np.arange(n_rows, dtype=int), initial_positions, assume_unique=False
    )
    return np.random.default_rng(seed).permutation(remaining)


def coverage_cells(
    frame: pd.DataFrame,
    *,
    lon_degrees: float = 10.0,
    lat_degrees: float = 5.0,
) -> np.ndarray:
    """Assign fixed geographic coverage cells without learning from outcomes."""
    lon_cell = np.floor((frame["longitude"].to_numpy() + 180.0) / lon_degrees).astype(
        int
    )
    lat_cell = np.floor((frame["latitude"].to_numpy() + 90.0) / lat_degrees).astype(
        int
    )
    return np.column_stack([lon_cell, lat_cell])


def coverage_acquisition_order(
    frame: pd.DataFrame,
    initial_positions: np.ndarray,
    seed: int,
    *,
    lon_degrees: float = 10.0,
    lat_degrees: float = 5.0,
) -> np.ndarray:
    """Prioritize cells with the fewest already selected observations.

    Rows within each cell and ties between equally represented cells are
    randomized reproducibly. The full order is computed from the development
    pool only, so budget prefixes are nested and test labels cannot leak in.
    """
    cells = coverage_cells(
        frame, lon_degrees=lon_degrees, lat_degrees=lat_degrees
    )
    cell_keys = [tuple(row) for row in cells]
    initial_set = set(np.asarray(initial_positions, dtype=int).tolist())
    selected_counts = Counter(cell_keys[position] for position in initial_set)

    candidates: dict[tuple[int, int], list[int]] = defaultdict(list)
    for position, key in enumerate(cell_keys):
        if position not in initial_set:
            candidates[key].append(position)

    rng = np.random.default_rng(seed)
    heap: list[tuple[int, float, tuple[int, int], int]] = []
    for key, positions in candidates.items():
        shuffled = rng.permutation(positions).tolist()
        candidates[key] = shuffled
        heapq.heappush(heap, (selected_counts[key], float(rng.random()), key, 0))

    order: list[int] = []
    while heap:
        count, _, key, offset = heapq.heappop(heap)
        positions = candidates[key]
        order.append(positions[offset])
        next_offset = offset + 1
        if next_offset < len(positions):
            heapq.heappush(
                heap,
                (count + 1, float(rng.random()), key, next_offset),
            )
    return np.asarray(order, dtype=int)
