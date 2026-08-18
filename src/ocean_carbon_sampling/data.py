"""Load and standardize SOCAT gridded text products."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SOCAT_COLUMN_MAP = {
    "DATE": "date",
    "LAT": "latitude",
    "LON": "longitude",
    "COUNT_NCRUISE_YEAR": "cruise_count",
    "FCO2_COUNT_NOBS_YEAR": "fco2_count",
    "FCO2_AVE_WEIGHTED_YEAR": "fco2",
    "SST_AVE_WEIGHTED_YEAR": "sst",
    "SALINITY_AVE_WEIGHTED_YEAR": "salinity",
}


def find_csv_header(path: str | Path) -> int:
    """Return the zero-based line index of the embedded CSV header."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream):
            if line.lstrip().startswith("DATE,"):
                return line_number
    raise ValueError(f"Could not find a DATE CSV header in {path}")


def read_socat_monthly(path: str | Path) -> pd.DataFrame:
    """Read the SOCAT monthly gridded CSV and return canonical columns.

    SOCAT's downloadable text file contains a CDL-style metadata preamble before
    the comma-separated table. Fill values such as -1e34 are converted to NA.
    """
    path = Path(path)
    header_line = find_csv_header(path)
    frame = pd.read_csv(
        path,
        skiprows=header_line,
        skipinitialspace=True,
        usecols=list(SOCAT_COLUMN_MAP),
    ).rename(columns=SOCAT_COLUMN_MAP)

    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    measured = ["fco2", "sst", "salinity"]
    frame[measured] = frame[measured].mask(frame[measured] <= -1e20)
    return frame


def select_southern_ocean(
    frame: pd.DataFrame,
    *,
    latitude_max: float = -35.0,
    year_start: int = 1990,
    year_end: int = 2024,
) -> pd.DataFrame:
    """Select the initial Southern Ocean study domain and year range."""
    years = frame["date"].dt.year
    selected = frame.loc[
        (frame["latitude"] < latitude_max)
        & years.between(year_start, year_end)
    ].copy()
    return selected.sort_values(["date", "latitude", "longitude"]).reset_index(
        drop=True
    )

