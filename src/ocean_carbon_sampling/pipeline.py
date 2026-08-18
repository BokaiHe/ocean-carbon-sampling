"""Shared preparation pipeline for regional SOCAT experiments."""

from __future__ import annotations

import pandas as pd

from ocean_carbon_sampling.data import read_socat_monthly, select_southern_ocean
from ocean_carbon_sampling.splits import add_spatial_folds


def load_complete_study(config: dict) -> pd.DataFrame:
    """Load, filter, and spatially block the complete-case study frame."""
    full = read_socat_monthly(config["data"]["raw_path"])
    study = select_southern_ocean(
        full,
        latitude_max=float(config["data"]["latitude_max"]),
        year_start=int(config["data"]["year_start"]),
        year_end=int(config["data"]["year_end"]),
    )
    complete = study.dropna(subset=["fco2", "sst", "salinity"]).copy()
    complete = complete.reset_index(drop=True)
    complete["observation_id"] = range(len(complete))
    n_before = len(study)
    n_after = len(complete)
    complete = add_spatial_folds(
        complete,
        lon_block_degrees=float(
            config["validation"]["spatial_block_lon_degrees"]
        ),
        lat_block_degrees=float(
            config["validation"]["spatial_block_lat_degrees"]
        ),
        n_folds=int(config["validation"].get("n_spatial_folds", 5)),
    )
    complete.attrs["n_before"] = n_before
    complete.attrs["n_after"] = n_after
    return complete
