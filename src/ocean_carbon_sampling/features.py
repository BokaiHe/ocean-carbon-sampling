"""Leakage-safe feature construction for the minimum experiment."""

from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "sst",
    "salinity",
    "latitude",
    "longitude_sin",
    "longitude_cos",
    "year",
    "month_sin",
    "month_cos",
]


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return model features without using fCO2 or validation-set statistics."""
    longitude_radians = np.deg2rad(frame["longitude"].to_numpy())
    month_radians = 2.0 * np.pi * (frame["date"].dt.month.to_numpy() - 1) / 12.0

    features = pd.DataFrame(
        {
            "sst": frame["sst"].to_numpy(),
            "salinity": frame["salinity"].to_numpy(),
            "latitude": frame["latitude"].to_numpy(),
            "longitude_sin": np.sin(longitude_radians),
            "longitude_cos": np.cos(longitude_radians),
            "year": frame["date"].dt.year.to_numpy(),
            "month_sin": np.sin(month_radians),
            "month_cos": np.cos(month_radians),
        }
    )
    return features.loc[:, FEATURE_COLUMNS]
