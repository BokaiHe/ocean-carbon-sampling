"""Print a reproducible audit of the local SOCAT monthly gridded file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ocean_carbon_sampling.data import read_socat_monthly, select_southern_ocean


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--latitude-max", type=float, default=-35.0)
    parser.add_argument("--year-start", type=int, default=1990)
    parser.add_argument("--year-end", type=int, default=2024)
    parser.add_argument("--temporal-test-start", type=int, default=2020)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    full = read_socat_monthly(args.path)
    study = select_southern_ocean(
        full,
        latitude_max=args.latitude_max,
        year_start=args.year_start,
        year_end=args.year_end,
    )
    complete = study.dropna(subset=["fco2", "sst", "salinity"])
    test_mask = complete["date"].dt.year >= args.temporal_test_start

    summary = {
        "source_path": str(args.path.resolve()),
        "global_rows": len(full),
        "global_date_min": full["date"].min().date().isoformat(),
        "global_date_max": full["date"].max().date().isoformat(),
        "study_rows_before_fill_filter": len(study),
        "study_complete_rows": len(complete),
        "study_rows_with_missing_salinity": int(study["salinity"].isna().sum()),
        "study_unique_grid_cells": int(
            complete[["latitude", "longitude"]].drop_duplicates().shape[0]
        ),
        "temporal_train_rows": int((~test_mask).sum()),
        "temporal_test_rows": int(test_mask.sum()),
        "duplicate_date_grid_rows": int(
            complete.duplicated(["date", "latitude", "longitude"]).sum()
        ),
        "latitude_range": [
            float(complete["latitude"].min()),
            float(complete["latitude"].max()),
        ],
        "longitude_range": [
            float(complete["longitude"].min()),
            float(complete["longitude"].max()),
        ],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

