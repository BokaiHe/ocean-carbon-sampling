"""Run spatially grouped XGBoost validation and descriptive Tree SHAP."""

from __future__ import annotations

import argparse
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ocean_carbon_sampling.diagnostics import (
    grouped_cross_validation,
    interpretability_gate,
    tree_shap_summaries,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/diagnostic.yaml"))
    parser.add_argument(
        "--work", type=Path, default=Path("results/diagnostic_work")
    )
    parser.add_argument("--output", type=Path, default=Path("results/public"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    frame = pd.read_parquet(args.work / "observation_effects.parquet")
    frame["date"] = pd.to_datetime(frame["date"])
    diagnostic = config["diagnostic"]
    seed = int(diagnostic["model_seed"])

    metric_frames = []
    prediction_frames = []
    for target in diagnostic["targets"]:
        for variant in ["environment", "full"]:
            metrics, predictions = grouped_cross_validation(
                frame,
                variant=variant,
                target_column=target,
                group_column=diagnostic["group_column"],
                n_splits=int(diagnostic["group_cv_splits"]),
                seed=seed,
            )
            metrics["target"] = target
            predictions["target"] = target
            metric_frames.append(metrics)
            prediction_frames.append(predictions)

    args.output.mkdir(parents=True, exist_ok=True)
    all_metrics = pd.concat(metric_frames, ignore_index=True)
    all_metrics.to_csv(
        args.output / "diagnostic_group_cv.csv", index=False
    )
    pd.concat(prediction_frames, ignore_index=True).to_csv(
        args.work / "diagnostic_oof_predictions.csv", index=False
    )
    gate = interpretability_gate(
        all_metrics,
        target=diagnostic["primary_target"],
        minimum_r2=float(diagnostic["minimum_oof_r2"]),
        minimum_spearman=float(diagnostic["minimum_oof_spearman"]),
    )
    gate.to_csv(args.output / "diagnostic_interpretability_gate.csv", index=False)
    if bool(gate.loc[0, "shap_interpretation_allowed"]):
        variant = gate.loc[0, "selected_model_variant"]
        importance, fold_shap, shap_values, feature_names = tree_shap_summaries(
            frame,
            variant=variant,
            target_column=diagnostic["primary_target"],
            seed=seed,
        )
        np.savez_compressed(
            args.work / f"shap_values_{variant}.npz",
            values=shap_values,
            feature_names=np.asarray(feature_names),
        )
        importance.to_csv(args.output / "diagnostic_shap_importance.csv", index=False)
        fold_shap.to_csv(args.output / "diagnostic_shap_by_fold.csv", index=False)
    (
        frame.groupby("spatial_test_fold", as_index=False)
        .agg(
            n_observations=("observation_id", "size"),
            mean_squared_error_gain=("mean_squared_error_gain", "mean"),
            median_squared_error_gain=("mean_squared_error_gain", "median"),
            mean_absolute_error_gain=("mean_absolute_error_gain", "mean"),
        )
        .to_csv(args.output / "diagnostic_target_by_fold.csv", index=False)
    )
    pd.DataFrame(
        {
            "package": ["xgboost", "shap"],
            "version": [version("xgboost"), version("shap")],
        }
    ).to_csv(args.output / "diagnostic_versions.csv", index=False)


if __name__ == "__main__":
    main()
