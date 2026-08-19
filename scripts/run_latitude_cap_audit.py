"""Align training candidates and evaluation cells below a latitude cap."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from run_historical_area_domain_audit import (
    evaluate_unit,
    load_frame,
    unit_summary,
    validate_cache,
)

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.osse_experiment import (
    historical_density_weights,
    stratified_evaluation_positions,
)
from ocean_carbon_sampling.splits import add_spatial_folds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--osse-config", type=Path, default=Path("configs/osse_pilot.yaml")
    )
    parser.add_argument(
        "--block-config",
        type=Path,
        default=Path("configs/osse_spatial_block_confirmatory.yaml"),
    )
    parser.add_argument("--budget", type=int, default=5000)
    parser.add_argument("--latitude-max", type=float, default=60.0)
    parser.add_argument(
        "--work-directory",
        type=Path,
        default=Path("results/osse_latitude_cap_work"),
    )
    parser.add_argument(
        "--metrics-output",
        type=Path,
        default=Path("results/public/osse_latitude_cap_metrics.csv"),
    )
    parser.add_argument(
        "--unit-output",
        type=Path,
        default=Path("results/public/osse_latitude_cap_unit_summary.csv"),
    )
    parser.add_argument(
        "--paired-output",
        type=Path,
        default=Path("results/public/osse_latitude_cap_paired.csv"),
    )
    parser.add_argument(
        "--overall-output",
        type=Path,
        default=Path("results/public/osse_latitude_cap_overall.csv"),
    )
    return parser.parse_args()


def paired_units(units: pd.DataFrame) -> pd.DataFrame:
    keys = [
        "validation_scheme",
        "year",
        "spatial_fold",
        "budget",
        "domain",
        "weighting",
    ]
    rows: list[dict[str, float | int | str]] = []
    for group_keys, group in units.groupby(keys, sort=True):
        strategies = group.set_index("strategy")
        for comparator in ("historical_density", "spatial_coverage"):
            row: dict[str, float | int | str] = dict(zip(keys, group_keys, strict=True))
            row["comparison"] = f"{comparator}_minus_random"
            for metric in ("bias", "mae", "rmse"):
                random_value = float(strategies.loc["random", f"mean_{metric}"])
                comparator_value = float(strategies.loc[comparator, f"mean_{metric}"])
                row[f"random_{metric}"] = random_value
                row[f"comparator_{metric}"] = comparator_value
                row[f"difference_{metric}"] = comparator_value - random_value
            rows.append(row)
    return pd.DataFrame(rows)


def paired_overall(paired: pd.DataFrame) -> pd.DataFrame:
    keys = [
        "validation_scheme",
        "budget",
        "domain",
        "weighting",
        "comparison",
    ]
    rows: list[dict[str, float | int | str]] = []
    for group_keys, group in paired.groupby(keys, sort=True):
        row: dict[str, float | int | str] = dict(zip(keys, group_keys, strict=True))
        row["n_units"] = len(group)
        for metric in ("bias", "mae", "rmse"):
            difference = group[f"difference_{metric}"]
            row[f"mean_random_{metric}"] = float(group[f"random_{metric}"].mean())
            row[f"mean_comparator_{metric}"] = float(
                group[f"comparator_{metric}"].mean()
            )
            row[f"mean_difference_{metric}"] = float(difference.mean())
            row[f"median_difference_{metric}"] = float(difference.median())
            row[f"units_difference_{metric}_below_zero"] = int((difference < 0).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    if not np.isclose(args.latitude_max, 60.0):
        raise ValueError("the published audit locks latitude-max at 60°N")
    osse = yaml.safe_load(args.osse_config.read_text(encoding="utf-8"))
    block = yaml.safe_load(args.block_config.read_text(encoding="utf-8"))
    years = tuple(int(value) for value in block["source"]["years"])
    seeds = tuple(int(value) for value in block["execution"]["seeds"])
    strategies = ("random", "historical_density", "spatial_coverage")
    processing = osse["processing"]
    experiment = osse["experiment"]
    density = experiment["historical_density"]
    socat = read_socat_monthly(density["socat_path"])
    coverage = experiment["coverage_blocks"]
    block_validation = block["validation"]
    args.work_directory.mkdir(parents=True, exist_ok=True)
    metric_frames: list[pd.DataFrame] = []

    for year in years:
        path = Path(str(processing["processed_file_template"]).format(year=year))
        frame = load_frame(path)
        frame = frame.loc[frame["latitude"] < args.latitude_max].reset_index(drop=True)
        weights = historical_density_weights(
            frame,
            socat,
            year_start=int(density["year_start"]),
            year_end=int(density["year_end"]),
            weight_column=str(density["weight_column"]),
        )
        hidden_positions = stratified_evaluation_positions(
            frame,
            fraction=float(experiment["evaluation"]["fraction"]),
            seed=int(experiment["evaluation"]["seed"]),
        )
        units = [("hidden_cells_latitude_cap", -1, hidden_positions)]
        block_frame = add_spatial_folds(
            frame,
            lon_block_degrees=float(block_validation["longitude_degrees"]),
            lat_block_degrees=float(block_validation["latitude_degrees"]),
            n_folds=int(block_validation["n_folds"]),
        )
        for fold in (int(value) for value in block_validation["folds"]):
            positions = np.flatnonzero(
                block_frame["spatial_fold"].to_numpy(dtype=int) == fold
            )
            units.append(("whole_blocks_latitude_cap", fold, positions))

        for validation_scheme, fold, positions in units:
            cache = (
                args.work_directory / f"metrics_{year}_{validation_scheme}_{fold}.csv"
            )
            if cache.exists():
                metrics = pd.read_csv(cache)
                if "latitude_cutoff_degrees_north" not in metrics:
                    metrics["latitude_cutoff_degrees_north"] = args.latitude_max
                    metrics.to_csv(cache, index=False)
                validate_cache(
                    metrics,
                    year=year,
                    validation_scheme=validation_scheme,
                    spatial_fold=fold,
                    budget=args.budget,
                    seeds=seeds,
                    strategies=strategies,
                    latitude_cutoff=args.latitude_max,
                )
            else:
                selected_frame = (
                    block_frame
                    if validation_scheme == "whole_blocks_latitude_cap"
                    else frame
                )
                metrics = evaluate_unit(
                    selected_frame,
                    weights,
                    positions,
                    year=year,
                    validation_scheme=validation_scheme,
                    spatial_fold=fold,
                    budget=args.budget,
                    seeds=seeds,
                    longitude_degrees=float(coverage["longitude_degrees"]),
                    latitude_degrees=float(coverage["latitude_degrees"]),
                    latitude_cutoff=args.latitude_max,
                    strategies=strategies,
                )
                metrics.to_csv(cache, index=False)
            metric_frames.append(metrics)
            print(f"complete: {year} {validation_scheme} fold={fold}", flush=True)

    metrics = pd.concat(metric_frames, ignore_index=True)
    units = unit_summary(metrics)
    paired = paired_units(units)
    overall = paired_overall(paired)
    for path in (
        args.metrics_output,
        args.unit_output,
        args.paired_output,
        args.overall_output,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.metrics_output, index=False)
    units.to_csv(args.unit_output, index=False)
    paired.to_csv(args.paired_output, index=False)
    overall.to_csv(args.overall_output, index=False)
    print("\nLatitude-cap paired audit:\n")
    print(overall.to_string(index=False))


if __name__ == "__main__":
    main()
