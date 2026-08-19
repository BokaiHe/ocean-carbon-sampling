"""Relate local historical signed error to SOCAT spatial density."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml
from scipy.stats import spearmanr

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.osse_experiment import historical_spatial_weights


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/osse_pilot.yaml"))
    parser.add_argument("--year", type=int, default=2005)
    parser.add_argument(
        "--map-input",
        type=Path,
        default=Path("results/public/osse_historical_bias_map_2005.parquet"),
    )
    parser.add_argument(
        "--cell-output",
        type=Path,
        default=Path("results/public/osse_historical_bias_density_cells_2005.parquet"),
    )
    parser.add_argument(
        "--bin-output",
        type=Path,
        default=Path("results/public/osse_historical_bias_density_bins_2005.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("results/public/osse_historical_bias_density_summary_2005.csv"),
    )
    return parser.parse_args()


def load_frame(path: Path) -> pd.DataFrame:
    with xr.open_dataset(path, engine="h5netcdf", decode_times=True) as dataset:
        frame = (
            dataset[["spco2", "tos", "sos"]]
            .to_dataframe()
            .dropna()
            .reset_index()
            .rename(columns={"time": "date", "tos": "sst", "sos": "salinity"})
        )
    frame["month"] = frame["date"].dt.month
    return frame


def summarize_bins(cells: pd.DataFrame) -> pd.DataFrame:
    positive = cells.loc[cells["historical_spatial_density"] > 0].copy()
    positive["density_bin"] = pd.qcut(
        positive["historical_spatial_density"],
        q=10,
        labels=False,
        duplicates="drop",
    ) + 1
    zero = cells.loc[cells["historical_spatial_density"] == 0].copy()
    zero["density_bin"] = 0
    grouped = pd.concat([zero, positive], ignore_index=True)
    rows: list[dict[str, float | int]] = []
    columns = (
        "signed_error_historical_density",
        "signed_error_historical_spatial_month_balanced",
    )
    for density_bin, group in grouped.groupby("density_bin", sort=True):
        row: dict[str, float | int] = {
            "density_bin": int(density_bin),
            "n_cells": len(group),
            "density_min": float(group["historical_spatial_density"].min()),
            "density_median": float(group["historical_spatial_density"].median()),
            "density_max": float(group["historical_spatial_density"].max()),
        }
        for column in columns:
            row[f"{column}_mean"] = float(group[column].mean())
            row[f"{column}_median"] = float(group[column].median())
            row[f"{column}_q25"] = float(group[column].quantile(0.25))
            row[f"{column}_q75"] = float(group[column].quantile(0.75))
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    processed = Path(
        str(config["processing"]["processed_file_template"]).format(year=args.year)
    )
    frame = load_frame(processed)
    density_config = config["experiment"]["historical_density"]
    socat = read_socat_monthly(density_config["socat_path"])
    weights = historical_spatial_weights(
        frame,
        socat,
        year_start=int(density_config["year_start"]),
        year_end=int(density_config["year_end"]),
        weight_column=str(density_config["weight_column"]),
    )
    density = frame[["latitude", "longitude"]].copy()
    density["historical_spatial_density"] = weights
    density = density.groupby(["latitude", "longitude"], as_index=False).first()
    maps = pd.read_parquet(args.map_input)
    cells = maps.merge(
        density,
        on=["latitude", "longitude"],
        how="left",
        validate="one_to_one",
    )
    if cells["historical_spatial_density"].isna().any():
        raise RuntimeError("historical spatial density is missing for map cells")
    cells["log10_one_plus_density"] = np.log10(
        1.0 + cells["historical_spatial_density"]
    )

    summary_rows: list[dict[str, float | int | str]] = []
    for scope, subset in (
        ("all_cells", cells),
        ("positive_density_cells", cells.loc[cells["historical_spatial_density"] > 0]),
    ):
        for column in (
            "signed_error_historical_density",
            "signed_error_historical_spatial_month_balanced",
        ):
            rho, pvalue = spearmanr(
                subset["historical_spatial_density"], subset[column]
            )
            summary_rows.append(
                {
                    "scope": scope,
                    "response": column,
                    "n_cells": len(subset),
                    "spearman_rho": float(rho),
                    "nominal_p_value_not_for_inference": float(pvalue),
                    "note": "grid cells are spatially dependent; p is descriptive only",
                }
            )
    bins = summarize_bins(cells)
    summary = pd.DataFrame(summary_rows)
    for path in (args.cell_output, args.bin_output, args.summary_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    float_columns = cells.select_dtypes(include=["number"]).columns
    cells[float_columns] = cells[float_columns].astype("float32")
    cells.to_parquet(args.cell_output, index=False)
    bins.to_csv(args.bin_output, index=False)
    summary.to_csv(args.summary_output, index=False)
    print(summary.to_string(index=False))
    print("\nBinned relationship:\n")
    print(bins.to_string(index=False))


if __name__ == "__main__":
    main()
