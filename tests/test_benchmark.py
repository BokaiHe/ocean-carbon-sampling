import numpy as np
import pandas as pd

from ocean_carbon_sampling.benchmark import (
    bootstrap_mean_interval,
    build_paired_effects,
    summarize_across_folds,
    summarize_paired_effects,
)


def test_bootstrap_interval_is_reproducible() -> None:
    values = np.array([1.0, 2.0, 3.0, 4.0])
    first = bootstrap_mean_interval(
        values, n_resamples=1000, confidence_level=0.95, seed=7
    )
    second = bootstrap_mean_interval(
        values, n_resamples=1000, confidence_level=0.95, seed=7
    )

    assert first == second
    assert first[0] < values.mean() < first[1]


def test_paired_effects_keep_seed_as_independent_replication() -> None:
    metrics = pd.DataFrame(
        {
            "regime": ["spatial"] * 4,
            "budget_fraction": [0.2] * 4,
            "seed": [0, 0, 1, 1],
            "strategy": ["random", "coverage", "random", "coverage"],
            "rmse": [10.0, 8.0, 9.0, 8.5],
        }
    )
    selections = metrics.drop(columns="rmse").assign(
        coverage_cell_count_cv=[1.5, 0.8, 1.4, 0.7]
    )
    paired = build_paired_effects(metrics, selections)
    summary = summarize_paired_effects(
        paired,
        n_resamples=1000,
        confidence_level=0.95,
        bootstrap_seed=3,
    )

    assert paired["rmse_gain"].tolist() == [2.0, 0.5]
    assert paired["cell_cv_reduction"].tolist() == [0.7, 0.7]
    assert set(summary["n_seeds"]) == {2}
    assert set(summary["fraction_positive"]) == {1.0}


def test_across_fold_summary_uses_fold_means_as_units() -> None:
    fold_summary = pd.DataFrame(
        {
            "spatial_test_fold": [0, 1, 2],
            "metric": ["rmse_gain"] * 3,
            "mean": [0.2, 0.5, -0.1],
            "ci_lower": [0.1, 0.2, -0.3],
        }
    )
    result = summarize_across_folds(fold_summary).iloc[0]

    assert result["n_folds"] == 3
    assert np.isclose(result["mean_of_fold_means"], 0.2)
    assert result["folds_mean_positive"] == 2
    assert result["folds_interval_above_zero"] == 2
