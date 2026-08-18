"""Run the preregistered repeated-seed regional sampling benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yaml

from ocean_carbon_sampling.benchmark import (
    build_paired_effects,
    summarize_paired_effects,
)
from ocean_carbon_sampling.experiment import ExperimentSettings, run_regime
from ocean_carbon_sampling.pipeline import load_complete_study
from ocean_carbon_sampling.splits import add_validation_regimes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/benchmark.yaml"))
    parser.add_argument("--output", type=Path, default=Path("results/public"))
    parser.add_argument("--work", type=Path, default=Path("results/benchmark_work"))
    return parser.parse_args()


def prepare_frame(config: dict) -> pd.DataFrame:
    complete = load_complete_study(config)
    return add_validation_regimes(
        complete,
        temporal_test_start=int(config["validation"]["temporal_test_start"]),
        spatial_test_fold=int(config["validation"]["spatial_test_fold"]),
    )


def run_seed(
    frame: pd.DataFrame, config: dict, seed: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    coverage = config["sampling"]["coverage_cells"]
    settings = ExperimentSettings(
        seed=seed,
        initial_fraction=float(config["sampling"]["initial_fraction"]),
        budgets=(float(config["sampling"]["budget"]),),
        coverage_lon_degrees=float(coverage["longitude_degrees"]),
        coverage_lat_degrees=float(coverage["latitude_degrees"]),
    )
    metric_frames = []
    selection_frames = []
    for regime, split_column in [
        ("temporal", "temporal_split"),
        ("spatial", "spatial_split"),
    ]:
        metrics, selections = run_regime(
            frame,
            regime=regime,
            split_column=split_column,
            settings=settings,
        )
        metric_frames.append(metrics)
        selection_frames.append(selections)
    return (
        pd.concat(metric_frames, ignore_index=True),
        pd.concat(selection_frames, ignore_index=True),
    )


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    frame = prepare_frame(config)
    args.work.mkdir(parents=True, exist_ok=True)

    metric_frames = []
    selection_frames = []
    for seed in config["experiment"]["seeds"]:
        metric_path = args.work / f"metrics_seed_{seed:03d}.csv"
        selection_path = args.work / f"selection_seed_{seed:03d}.csv"
        if not (metric_path.exists() and selection_path.exists()):
            metrics, selections = run_seed(frame, config, int(seed))
            metrics.to_csv(metric_path, index=False)
            selections.to_csv(selection_path, index=False)
        # Treat serialized checkpoints as the canonical representation so a
        # clean run and a resumed run produce byte-identical public outputs.
        metrics = pd.read_csv(metric_path)
        selections = pd.read_csv(selection_path)
        metric_frames.append(metrics)
        selection_frames.append(selections)
        print(f"completed seed {seed}", flush=True)

    metrics = pd.concat(metric_frames, ignore_index=True).sort_values(
        ["regime", "seed", "strategy"]
    )
    selections = pd.concat(selection_frames, ignore_index=True).sort_values(
        ["regime", "seed", "strategy"]
    )
    paired = build_paired_effects(metrics, selections)
    statistics = config["statistics"]
    summary = summarize_paired_effects(
        paired,
        n_resamples=int(statistics["bootstrap_resamples"]),
        confidence_level=float(statistics["confidence_level"]),
        bootstrap_seed=int(statistics["bootstrap_seed"]),
    )

    args.output.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.output / "benchmark_seed_metrics.csv", index=False)
    selections.to_csv(args.output / "benchmark_seed_selection.csv", index=False)
    paired.to_csv(args.output / "benchmark_paired_effects.csv", index=False)
    summary.to_csv(args.output / "benchmark_summary.csv", index=False)


if __name__ == "__main__":
    main()
