"""Export compact, source-grounded map data for the visual-story notebook."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.experiment import make_model
from ocean_carbon_sampling.features import build_features
from ocean_carbon_sampling.osse_experiment import (
    fixed_budget_orders,
    historical_density_weights,
    stratified_evaluation_positions,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/osse_pilot.yaml")
    parser.add_argument("--year", type=int, default=2005)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--error-seeds",
        type=int,
        nargs="+",
        default=list(range(20)),
        help="Paired seeds averaged in the error maps.",
    )
    parser.add_argument("--budget", type=int, default=5000)
    parser.add_argument(
        "--field-output",
        default="results/public/osse_visual_demo_fields.parquet",
    )
    parser.add_argument(
        "--sampling-output",
        default="results/public/osse_visual_demo_sampling.parquet",
    )
    parser.add_argument(
        "--metadata-output",
        default="results/public/osse_visual_demo_metadata.csv",
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


def spatial_block_summary(
    selected: pd.DataFrame,
    *,
    strategy: str,
    longitude_degrees: float,
    latitude_degrees: float,
) -> pd.DataFrame:
    summary = selected.loc[:, ["month", "latitude", "longitude"]].copy()
    lon_index = np.floor((summary["longitude"] + 180.0) / longitude_degrees)
    lat_index = np.floor((summary["latitude"] + 90.0) / latitude_degrees)
    summary["longitude"] = -180.0 + (lon_index + 0.5) * longitude_degrees
    summary["latitude"] = -90.0 + (lat_index + 0.5) * latitude_degrees
    result = (
        summary.groupby(["latitude", "longitude"], as_index=False)
        .agg(
            observations=("month", "size"),
            months_covered=("month", "nunique"),
        )
        .sort_values(["latitude", "longitude"])
    )
    result.insert(0, "strategy", strategy)
    return result


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    processing = config["processing"]
    experiment = config["experiment"]
    processed_path = Path(
        str(processing["processed_file_template"]).format(year=args.year)
    )
    frame = load_frame(processed_path)

    density = experiment["historical_density"]
    socat = read_socat_monthly(density["socat_path"])
    historical_weights = historical_density_weights(
        frame,
        socat,
        year_start=int(density["year_start"]),
        year_end=int(density["year_end"]),
        weight_column=str(density["weight_column"]),
    )

    evaluation_config = experiment["evaluation"]
    evaluation_positions = stratified_evaluation_positions(
        frame,
        fraction=float(evaluation_config["fraction"]),
        seed=int(evaluation_config["seed"]),
    )
    evaluation_mask = np.zeros(len(frame), dtype=bool)
    evaluation_mask[evaluation_positions] = True
    candidates = frame.loc[~evaluation_mask].reset_index(drop=True)
    evaluation = frame.loc[evaluation_mask].reset_index(drop=True)
    candidate_weights = historical_weights[~evaluation_mask]

    coverage = experiment["coverage_blocks"]
    longitude_degrees = float(coverage["longitude_degrees"])
    latitude_degrees = float(coverage["latitude_degrees"])
    x_candidates = build_features(candidates)
    x_evaluation = build_features(evaluation)
    y_candidates = candidates["spco2"].to_numpy()
    y_evaluation = evaluation["spco2"].to_numpy()
    strategies = ("random", "historical_density", "spatial_coverage")
    error_seeds = tuple(dict.fromkeys(int(seed) for seed in args.error_seeds))
    if not error_seeds:
        raise ValueError("error-seeds must contain at least one seed")
    absolute_error_sums = {
        strategy: np.zeros(len(evaluation), dtype=float) for strategy in strategies
    }
    location_index = pd.MultiIndex.from_frame(
        evaluation[["latitude", "longitude"]]
    )
    location_codes, unique_locations = pd.factorize(location_index, sort=True)
    location_counts = np.bincount(location_codes)
    positive_seed_counts = np.zeros(len(unique_locations), dtype=int)
    negative_seed_counts = np.zeros(len(unique_locations), dtype=int)
    sampling_frames: list[pd.DataFrame] = []
    sampling_orders = fixed_budget_orders(
        candidates,
        candidate_weights,
        maximum_budget=args.budget,
        seed=args.seed,
        longitude_degrees=longitude_degrees,
        latitude_degrees=latitude_degrees,
    )
    for strategy, order in sampling_orders.items():
        sampling_frames.append(
            spatial_block_summary(
                candidates.iloc[order[: args.budget]],
                strategy=strategy,
                longitude_degrees=longitude_degrees,
                latitude_degrees=latitude_degrees,
            )
        )

    published = pd.read_csv("results/public/osse_cross_year_metrics.csv")
    for seed in error_seeds:
        orders = fixed_budget_orders(
            candidates,
            candidate_weights,
            maximum_budget=args.budget,
            seed=seed,
            longitude_degrees=longitude_degrees,
            latitude_degrees=latitude_degrees,
        )
        seed_errors: dict[str, np.ndarray] = {}
        expected = published.query(
            "year == @args.year and evaluation_domain == 'all' "
            "and budget == @args.budget and seed == @seed"
        ).set_index("strategy")["rmse"]
        for strategy, order in orders.items():
            selected = order[: args.budget]
            model = make_model(seed + 10_000)
            model.fit(x_candidates.iloc[selected], y_candidates[selected])
            prediction = model.predict(x_evaluation)
            absolute_error = np.abs(prediction - y_evaluation)
            seed_errors[strategy] = absolute_error
            absolute_error_sums[strategy] += absolute_error
            observed_rmse = float(np.sqrt(np.mean((prediction - y_evaluation) ** 2)))
            if not np.isclose(
                observed_rmse,
                expected.loc[strategy],
                rtol=0,
                atol=1e-10,
            ):
                raise RuntimeError(
                    f"{strategy} seed {seed} RMSE does not match the published run"
                )
        difference = (
            seed_errors["spatial_coverage"] - seed_errors["random"]
        )
        cell_difference = (
            np.bincount(location_codes, weights=difference) / location_counts
        )
        positive_seed_counts += cell_difference > 0
        negative_seed_counts += cell_difference < 0
        print(f"completed error-map seed {seed}", flush=True)

    truth = (
        frame.groupby(["latitude", "longitude"], as_index=False)
        .agg(truth_spco2=("spco2", "mean"))
        .sort_values(["latitude", "longitude"])
    )
    errors = evaluation.loc[:, ["latitude", "longitude"]].copy()
    for strategy in strategies:
        errors[f"absolute_error_{strategy}"] = (
            absolute_error_sums[strategy] / len(error_seeds)
        )
    errors["absolute_error_difference_coverage_minus_random"] = (
        errors["absolute_error_spatial_coverage"]
        - errors["absolute_error_random"]
    )
    error_fields = errors.groupby(
        ["latitude", "longitude"], as_index=False
    ).mean(numeric_only=True)
    consistency = unique_locations.to_frame(index=False)
    consistency.columns = ["latitude", "longitude"]
    consistency["coverage_better_seed_fraction"] = (
        negative_seed_counts / len(error_seeds)
    )
    consistency["random_better_seed_fraction"] = (
        positive_seed_counts / len(error_seeds)
    )
    consistency["sign_consistent_80pct"] = (
        np.maximum(negative_seed_counts, positive_seed_counts)
        >= np.ceil(0.8 * len(error_seeds))
    )
    error_fields = error_fields.merge(
        consistency,
        on=["latitude", "longitude"],
        how="left",
        validate="one_to_one",
    )
    fields = truth.merge(
        error_fields,
        on=["latitude", "longitude"],
        how="left",
        validate="one_to_one",
    )

    field_output = Path(args.field_output)
    sampling_output = Path(args.sampling_output)
    metadata_output = Path(args.metadata_output)
    for path in (field_output, sampling_output, metadata_output):
        path.parent.mkdir(parents=True, exist_ok=True)
    fields.to_parquet(field_output, index=False)
    pd.concat(sampling_frames, ignore_index=True).to_parquet(
        sampling_output,
        index=False,
    )
    pd.DataFrame(
        [
            {
                "year": args.year,
                "seed": args.seed,
                "error_map_seeds": ";".join(str(seed) for seed in error_seeds),
                "n_error_map_seeds": len(error_seeds),
                "budget": args.budget,
                "complete_month_cells": len(frame),
                "candidate_month_cells": len(candidates),
                "evaluation_month_cells": len(evaluation),
                "map_grid_cells": len(fields),
                "sampling_longitude_degrees": longitude_degrees,
                "sampling_latitude_degrees": latitude_degrees,
                "map_role": (
                    "error fields are paired-seed means; sampling geometry uses "
                    "the representative seed"
                ),
            }
        ]
    ).to_csv(metadata_output, index=False)

    print(f"wrote {len(fields):,} map cells to {field_output}")
    print(f"wrote {sum(map(len, sampling_frames)):,} sampling blocks to {sampling_output}")


if __name__ == "__main__":
    main()
