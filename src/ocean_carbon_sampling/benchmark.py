"""Paired effect estimates for repeated sampling-seed experiments."""

from __future__ import annotations

import numpy as np
import pandas as pd


def bootstrap_mean_interval(
    values: np.ndarray,
    *,
    n_resamples: int,
    confidence_level: float,
    seed: int,
) -> tuple[float, float]:
    """Percentile interval for the mean across sampling-seed replicates."""
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("values must contain at least two one-dimensional entries")
    if n_resamples < 100:
        raise ValueError("n_resamples must be at least 100")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be in (0, 1)")

    rng = np.random.default_rng(seed)
    indices = rng.integers(0, values.size, size=(n_resamples, values.size))
    bootstrap_means = values[indices].mean(axis=1)
    alpha = 1.0 - confidence_level
    lower, upper = np.quantile(
        bootstrap_means, [alpha / 2.0, 1.0 - alpha / 2.0]
    )
    return float(lower), float(upper)


def build_paired_effects(
    metrics: pd.DataFrame, selections: pd.DataFrame
) -> pd.DataFrame:
    """Pair random and coverage outcomes within regime, budget, and seed."""
    index = ["regime", "budget_fraction", "seed"]
    rmse = metrics.pivot(index=index, columns="strategy", values="rmse")
    cell_cv = selections.pivot(
        index=index, columns="strategy", values="coverage_cell_count_cv"
    )
    required = {"random", "coverage"}
    if not required.issubset(rmse.columns) or not required.issubset(cell_cv.columns):
        raise ValueError("every paired comparison requires random and coverage rows")

    paired = pd.DataFrame(
        {
            "random_rmse": rmse["random"],
            "coverage_rmse": rmse["coverage"],
            "rmse_gain": rmse["random"] - rmse["coverage"],
            "random_cell_cv": cell_cv["random"],
            "coverage_cell_cv": cell_cv["coverage"],
            "cell_cv_reduction": cell_cv["random"] - cell_cv["coverage"],
        }
    ).reset_index()
    paired["relative_rmse_gain_pct"] = (
        100.0 * paired["rmse_gain"] / paired["random_rmse"]
    )
    return paired.sort_values(index).reset_index(drop=True)


def summarize_paired_effects(
    paired: pd.DataFrame,
    *,
    n_resamples: int,
    confidence_level: float,
    bootstrap_seed: int,
) -> pd.DataFrame:
    """Summarize seed-level effects without significance testing."""
    rows = []
    metrics = ["rmse_gain", "cell_cv_reduction"]
    for regime_number, (regime, group) in enumerate(
        paired.groupby("regime", sort=True)
    ):
        for metric_number, metric in enumerate(metrics):
            values = group[metric].to_numpy()
            lower, upper = bootstrap_mean_interval(
                values,
                n_resamples=n_resamples,
                confidence_level=confidence_level,
                seed=bootstrap_seed + 10 * regime_number + metric_number,
            )
            rows.append(
                {
                    "regime": regime,
                    "metric": metric,
                    "n_seeds": len(values),
                    "mean": float(values.mean()),
                    "median": float(np.median(values)),
                    "sd": float(values.std(ddof=1)),
                    "ci_level": confidence_level,
                    "ci_lower": lower,
                    "ci_upper": upper,
                    "fraction_positive": float(np.mean(values > 0)),
                    "bootstrap_resamples": n_resamples,
                }
            )
    return pd.DataFrame(rows)


def summarize_across_folds(fold_summary: pd.DataFrame) -> pd.DataFrame:
    """Summarize exhaustive fold means without treating seeds as 100 iid units."""
    required = {"spatial_test_fold", "metric", "mean", "ci_lower"}
    if not required.issubset(fold_summary.columns):
        raise ValueError(f"fold_summary is missing {sorted(required - set(fold_summary))}")

    rows = []
    for metric, group in fold_summary.groupby("metric", sort=True):
        fold_means = group["mean"].to_numpy()
        rows.append(
            {
                "metric": metric,
                "n_folds": len(group),
                "mean_of_fold_means": float(fold_means.mean()),
                "sd_across_fold_means": float(fold_means.std(ddof=1)),
                "min_fold_mean": float(fold_means.min()),
                "max_fold_mean": float(fold_means.max()),
                "folds_mean_positive": int(np.sum(fold_means > 0)),
                "folds_interval_above_zero": int(np.sum(group["ci_lower"] > 0)),
            }
        )
    return pd.DataFrame(rows)
