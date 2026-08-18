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
    orders = fixed_budget_orders(
        candidates,
        candidate_weights,
        maximum_budget=args.budget,
        seed=args.seed,
        longitude_degrees=longitude_degrees,
        latitude_degrees=latitude_degrees,
    )

    x_candidates = build_features(candidates)
    x_evaluation = build_features(evaluation)
    y_candidates = candidates["spco2"].to_numpy()
    y_evaluation = evaluation["spco2"].to_numpy()
    evaluation_predictions: dict[str, np.ndarray] = {}
    sampling_frames: list[pd.DataFrame] = []

    for strategy, order in orders.items():
        selected = order[: args.budget]
        model = make_model(args.seed + 10_000)
        model.fit(x_candidates.iloc[selected], y_candidates[selected])
        evaluation_predictions[strategy] = model.predict(x_evaluation)
        sampling_frames.append(
            spatial_block_summary(
                candidates.iloc[selected],
                strategy=strategy,
                longitude_degrees=longitude_degrees,
                latitude_degrees=latitude_degrees,
            )
        )

    published = pd.read_csv("results/public/osse_cross_year_metrics.csv")
    expected = published.query(
        "year == @args.year and evaluation_domain == 'all' "
        "and budget == @args.budget and seed == @args.seed"
    ).set_index("strategy")["rmse"]
    for strategy, prediction in evaluation_predictions.items():
        observed_rmse = float(np.sqrt(np.mean((prediction - y_evaluation) ** 2)))
        if not np.isclose(observed_rmse, expected.loc[strategy], rtol=0, atol=1e-10):
            raise RuntimeError(f"{strategy} RMSE does not match the published run")

    truth = (
        frame.groupby(["latitude", "longitude"], as_index=False)
        .agg(truth_spco2=("spco2", "mean"))
        .sort_values(["latitude", "longitude"])
    )
    errors = evaluation.loc[:, ["latitude", "longitude"]].copy()
    for strategy, prediction in evaluation_predictions.items():
        errors[f"absolute_error_{strategy}"] = np.abs(prediction - y_evaluation)
    errors["absolute_error_difference_coverage_minus_random"] = (
        errors["absolute_error_spatial_coverage"]
        - errors["absolute_error_random"]
    )
    error_fields = errors.groupby(
        ["latitude", "longitude"], as_index=False
    ).mean(numeric_only=True)
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
                "budget": args.budget,
                "complete_month_cells": len(frame),
                "candidate_month_cells": len(candidates),
                "evaluation_month_cells": len(evaluation),
                "map_grid_cells": len(fields),
                "sampling_longitude_degrees": longitude_degrees,
                "sampling_latitude_degrees": latitude_degrees,
                "map_role": "representative spatial pattern; not inferential replicate",
            }
        ]
    ).to_csv(metadata_output, index=False)

    print(f"wrote {len(fields):,} map cells to {field_output}")
    print(f"wrote {sum(map(len, sampling_frames)):,} sampling blocks to {sampling_output}")


if __name__ == "__main__":
    main()
