"""Build per-observation paired error effects for XGBoost diagnostics."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from ocean_carbon_sampling.experiment import (
    ExperimentSettings,
    run_regime_detailed,
)
from ocean_carbon_sampling.pipeline import load_complete_study
from ocean_carbon_sampling.splits import add_validation_regimes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/diagnostic.yaml"))
    parser.add_argument(
        "--work", type=Path, default=Path("results/diagnostic_work")
    )
    return parser.parse_args()


def make_settings(config: dict, seed: int) -> ExperimentSettings:
    coverage = config["sampling"]["coverage_cells"]
    return ExperimentSettings(
        seed=seed,
        initial_fraction=float(config["sampling"]["initial_fraction"]),
        budgets=(float(config["sampling"]["budget"]),),
        coverage_lon_degrees=float(coverage["longitude_degrees"]),
        coverage_lat_degrees=float(coverage["latitude_degrees"]),
    )


def paired_errors(predictions: pd.DataFrame, fold: int, seed: int) -> pd.DataFrame:
    index = ["observation_id"]
    squared = predictions.pivot(index=index, columns="strategy", values="squared_error")
    absolute = predictions.pivot(
        index=index, columns="strategy", values="absolute_error"
    )
    paired = pd.DataFrame(
        {
            "random_squared_error": squared["random"],
            "coverage_squared_error": squared["coverage"],
            "squared_error_gain": squared["random"] - squared["coverage"],
            "random_absolute_error": absolute["random"],
            "coverage_absolute_error": absolute["coverage"],
            "absolute_error_gain": absolute["random"] - absolute["coverage"],
        }
    ).reset_index()
    paired["spatial_test_fold"] = fold
    paired["seed"] = seed
    return paired


def aggregate_effects(seed_effects: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    aggregated = (
        seed_effects.groupby(["observation_id", "spatial_test_fold"], as_index=False)
        .agg(
            mean_squared_error_gain=("squared_error_gain", "mean"),
            median_squared_error_gain=("squared_error_gain", "median"),
            sd_squared_error_gain=("squared_error_gain", "std"),
            mean_absolute_error_gain=("absolute_error_gain", "mean"),
            fraction_squared_error_gain_positive=(
                "squared_error_gain",
                lambda values: float((values > 0).mean()),
            ),
            n_seeds=("seed", "nunique"),
        )
    )
    metadata = base[
        [
            "observation_id",
            "date",
            "latitude",
            "longitude",
            "sst",
            "salinity",
            "fco2",
            "spatial_block",
        ]
    ]
    return aggregated.merge(metadata, on="observation_id", validate="one_to_one")


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    base = load_complete_study(config)
    args.work.mkdir(parents=True, exist_ok=True)
    effect_frames = []

    for fold in config["experiment"]["spatial_test_folds"]:
        frame = add_validation_regimes(
            base,
            temporal_test_start=int(config["validation"]["temporal_test_start"]),
            spatial_test_fold=int(fold),
        )
        for seed in config["experiment"]["seeds"]:
            effect_path = args.work / f"effects_fold_{fold}_seed_{seed:03d}.parquet"
            if not effect_path.exists():
                _, _, predictions = run_regime_detailed(
                    frame,
                    regime=f"spatial_fold_{fold}",
                    split_column="spatial_split",
                    settings=make_settings(config, int(seed)),
                )
                paired_errors(predictions, int(fold), int(seed)).to_parquet(
                    effect_path, index=False
                )
            effects = pd.read_parquet(effect_path)
            effect_frames.append(effects)
            print(f"completed fold {fold}, seed {seed}", flush=True)

    seed_effects = pd.concat(effect_frames, ignore_index=True)
    observation_effects = aggregate_effects(seed_effects, base)
    seed_effects.to_parquet(args.work / "seed_effects.parquet", index=False)
    observation_effects.to_parquet(
        args.work / "observation_effects.parquet", index=False
    )


if __name__ == "__main__":
    main()
