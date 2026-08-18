"""Run all spatial holdout folds across prespecified sampling seeds."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ocean_carbon_sampling.benchmark import (
    build_paired_effects,
    summarize_across_folds,
    summarize_paired_effects,
)
from ocean_carbon_sampling.experiment import ExperimentSettings, run_regime
from ocean_carbon_sampling.pipeline import load_complete_study
from ocean_carbon_sampling.splits import add_validation_regimes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=Path("configs/spatial_sensitivity.yaml")
    )
    parser.add_argument("--output", type=Path, default=Path("results/public"))
    parser.add_argument(
        "--work", type=Path, default=Path("results/spatial_sensitivity_work")
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


def build_block_map(frame: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Create a lightweight source table for occupied pre-2020 spatial blocks."""
    validation = config["validation"]
    lon_width = float(validation["spatial_block_lon_degrees"])
    lat_width = float(validation["spatial_block_lat_degrees"])
    pretest = frame.loc[
        frame["date"].dt.year < int(validation["temporal_test_start"])
    ].copy()
    pretest["lon_block"] = np.floor(
        (pretest["longitude"] + 180.0) / lon_width
    ).astype(int)
    pretest["lat_block"] = np.floor(
        (pretest["latitude"] + 90.0) / lat_width
    ).astype(int)
    blocks = (
        pretest.groupby(["lon_block", "lat_block", "spatial_fold"], as_index=False)
        .size()
        .rename(columns={"size": "rows"})
    )
    blocks["longitude_center"] = -180.0 + (blocks["lon_block"] + 0.5) * lon_width
    blocks["latitude_center"] = -90.0 + (blocks["lat_block"] + 0.5) * lat_width
    blocks["longitude_width"] = lon_width
    blocks["latitude_width"] = lat_width
    return blocks


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    base = load_complete_study(config)
    args.work.mkdir(parents=True, exist_ok=True)

    metric_frames = []
    selection_frames = []
    design_rows = []
    for fold in config["experiment"]["spatial_test_folds"]:
        frame = add_validation_regimes(
            base,
            temporal_test_start=int(config["validation"]["temporal_test_start"]),
            spatial_test_fold=int(fold),
        )
        test_mask = frame["spatial_split"] == "test"
        development_mask = frame["spatial_split"] == "development"
        design_rows.append(
            {
                "spatial_test_fold": int(fold),
                "n_development": int(development_mask.sum()),
                "n_test": int(test_mask.sum()),
                "n_test_blocks": int(
                    frame.loc[test_mask, "spatial_block"].nunique()
                ),
            }
        )
        for seed in config["experiment"]["seeds"]:
            metric_path = args.work / f"metrics_fold_{fold}_seed_{seed:03d}.csv"
            selection_path = (
                args.work / f"selection_fold_{fold}_seed_{seed:03d}.csv"
            )
            if not (metric_path.exists() and selection_path.exists()):
                metrics, selections = run_regime(
                    frame,
                    regime=f"spatial_fold_{fold}",
                    split_column="spatial_split",
                    settings=make_settings(config, int(seed)),
                )
                metrics.to_csv(metric_path, index=False)
                selections.to_csv(selection_path, index=False)
            metrics = pd.read_csv(metric_path)
            selections = pd.read_csv(selection_path)
            metric_frames.append(metrics)
            selection_frames.append(selections)
            print(f"completed fold {fold}, seed {seed}", flush=True)

    metrics = pd.concat(metric_frames, ignore_index=True).sort_values(
        ["regime", "seed", "strategy"]
    )
    selections = pd.concat(selection_frames, ignore_index=True).sort_values(
        ["regime", "seed", "strategy"]
    )
    paired = build_paired_effects(metrics, selections)
    paired["spatial_test_fold"] = paired["regime"].str.extract(r"(\d+)$").astype(int)
    statistics = config["statistics"]
    fold_summary = summarize_paired_effects(
        paired,
        n_resamples=int(statistics["bootstrap_resamples"]),
        confidence_level=float(statistics["confidence_level"]),
        bootstrap_seed=int(statistics["bootstrap_seed"]),
    )
    fold_summary["spatial_test_fold"] = (
        fold_summary["regime"].str.extract(r"(\d+)$").astype(int)
    )
    overall = summarize_across_folds(fold_summary)

    args.output.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.output / "spatial_sensitivity_seed_metrics.csv", index=False)
    selections.to_csv(
        args.output / "spatial_sensitivity_seed_selection.csv", index=False
    )
    paired.to_csv(args.output / "spatial_sensitivity_paired_effects.csv", index=False)
    fold_summary.to_csv(
        args.output / "spatial_sensitivity_fold_summary.csv", index=False
    )
    overall.to_csv(
        args.output / "spatial_sensitivity_overall_summary.csv", index=False
    )
    pd.DataFrame(design_rows).to_csv(
        args.output / "spatial_sensitivity_design.csv", index=False
    )
    build_block_map(base, config).to_csv(
        args.output / "spatial_fold_blocks.csv", index=False
    )


if __name__ == "__main__":
    main()
