"""Leakage-aware validation splits for gridded ocean observations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def add_spatial_folds(
    frame: pd.DataFrame,
    *,
    lon_block_degrees: float = 20.0,
    lat_block_degrees: float = 10.0,
    n_folds: int = 5,
) -> pd.DataFrame:
    """Assign deterministic checkerboard folds to spatial blocks."""
    result = frame.copy()
    lon_block = np.floor((result["longitude"] + 180.0) / lon_block_degrees).astype(
        int
    )
    lat_block = np.floor((result["latitude"] + 90.0) / lat_block_degrees).astype(
        int
    )
    result["spatial_block"] = lon_block.astype(str) + "_" + lat_block.astype(str)
    result["spatial_fold"] = (lon_block + 2 * lat_block) % n_folds
    return result


def add_validation_regimes(
    frame: pd.DataFrame,
    *,
    temporal_test_start: int = 2020,
    spatial_test_fold: int = 0,
) -> pd.DataFrame:
    """Label independent temporal and spatial evaluation regimes.

    Spatial evaluation is restricted to pre-test years so it does not conflate
    spatial extrapolation with forecasting into the future.
    """
    result = frame.copy()
    years = result["date"].dt.year
    result["temporal_split"] = np.where(
        years >= temporal_test_start, "test", "development"
    )
    result["spatial_split"] = "not_used"
    pretest = years < temporal_test_start
    result.loc[pretest, "spatial_split"] = np.where(
        result.loc[pretest, "spatial_fold"] == spatial_test_fold,
        "test",
        "development",
    )
    return result

