"""Summarize intrinsic pCO2 scales in the locked OSSE truth fields."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-directory",
        type=Path,
        default=Path("data/processed/osse_pilot"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/public/osse_truth_scale.csv"),
    )
    return parser.parse_args()


def summarize_field(path: Path) -> dict[str, float | int | str]:
    """Calculate scale references without altering or subsampling the field."""
    with xr.open_dataset(path, engine="h5netcdf") as dataset:
        truth = dataset["spco2"].load()
        values = truth.values.astype(float)
        annual_mean = truth.mean("time", skipna=True).values.astype(float)
        seasonal_amplitude = (
            truth.max("time", skipna=True) - truth.min("time", skipna=True)
        ).values.astype(float)
        year = int(str(dataset["time"].values[0])[:4])
    return {
        "scope": str(year),
        "n_finite_month_cells": int(np.isfinite(values).sum()),
        "month_cell_standard_deviation_uatm": float(np.nanstd(values)),
        "annual_mean_spatial_standard_deviation_uatm": float(
            np.nanstd(annual_mean)
        ),
        "median_local_seasonal_amplitude_uatm": float(
            np.nanmedian(seasonal_amplitude)
        ),
        "mean_local_seasonal_amplitude_uatm": float(
            np.nanmean(seasonal_amplitude)
        ),
        "month_cell_p05_uatm": float(np.nanquantile(values, 0.05)),
        "month_cell_p95_uatm": float(np.nanquantile(values, 0.95)),
    }


def main() -> None:
    args = parse_args()
    paths = sorted(args.input_directory.glob("IPSL-CM6A-LR_historical_*_1deg.nc"))
    if not paths:
        raise FileNotFoundError(f"No locked truth fields found in {args.input_directory}")

    rows = [summarize_field(path) for path in paths]
    pooled_values: list[np.ndarray] = []
    pooled_annual_means: list[np.ndarray] = []
    pooled_amplitudes: list[np.ndarray] = []
    for path in paths:
        with xr.open_dataset(path, engine="h5netcdf") as dataset:
            truth = dataset["spco2"].load()
        pooled_values.append(truth.values.astype(float).ravel())
        pooled_annual_means.append(
            truth.mean("time", skipna=True).values.astype(float).ravel()
        )
        pooled_amplitudes.append(
            (
                truth.max("time", skipna=True) - truth.min("time", skipna=True)
            ).values.astype(float).ravel()
        )

    values = np.concatenate(pooled_values)
    annual_means = np.concatenate(pooled_annual_means)
    amplitudes = np.concatenate(pooled_amplitudes)
    rows.append(
        {
            "scope": "pooled_prespecified_years",
            "n_finite_month_cells": int(np.isfinite(values).sum()),
            "month_cell_standard_deviation_uatm": float(np.nanstd(values)),
            "annual_mean_spatial_standard_deviation_uatm": float(
                np.nanstd(annual_means)
            ),
            "median_local_seasonal_amplitude_uatm": float(
                np.nanmedian(amplitudes)
            ),
            "mean_local_seasonal_amplitude_uatm": float(
                np.nanmean(amplitudes)
            ),
            "month_cell_p05_uatm": float(np.nanquantile(values, 0.05)),
            "month_cell_p95_uatm": float(np.nanquantile(values, 0.95)),
        }
    )
    output = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    print(output.to_string(index=False))
    print(f"\nwrote {len(output):,} rows to {args.output}")


if __name__ == "__main__":
    main()
