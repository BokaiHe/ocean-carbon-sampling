"""Minimum fixed-budget sampling experiment."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from ocean_carbon_sampling.features import build_features
from ocean_carbon_sampling.sampling import (
    coverage_acquisition_order,
    coverage_cells,
    initial_sample,
    random_acquisition_order,
)


@dataclass(frozen=True)
class ExperimentSettings:
    seed: int = 42
    initial_fraction: float = 0.10
    budgets: tuple[float, ...] = (0.10, 0.20)
    coverage_lon_degrees: float = 10.0
    coverage_lat_degrees: float = 5.0


def regression_metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """Compute preregistered deterministic regression metrics."""
    residual = predicted - observed
    return {
        "rmse": float(np.sqrt(np.mean(np.square(residual)))),
        "mae": float(np.mean(np.abs(residual))),
        "bias": float(np.mean(residual)),
    }


def make_model(seed: int) -> HistGradientBoostingRegressor:
    """Return the single locked lightweight model used by every comparison."""
    return HistGradientBoostingRegressor(
        learning_rate=0.07,
        max_iter=150,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=seed,
    )


def _target_size(n_rows: int, budget: float, initial_size: int) -> int:
    return min(n_rows, max(initial_size, int(np.ceil(n_rows * budget))))


def run_regime_detailed(
    frame: pd.DataFrame,
    *,
    regime: str,
    split_column: str,
    settings: ExperimentSettings,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run both strategies and retain predictions for diagnostic workflows."""
    development = frame.loc[frame[split_column] == "development"].reset_index(drop=True)
    test = frame.loc[frame[split_column] == "test"].reset_index(drop=True)
    if development.empty or test.empty:
        raise ValueError(f"{regime} requires non-empty development and test sets")

    initial = initial_sample(len(development), settings.initial_fraction, settings.seed)
    acquisition_orders = {
        "random": random_acquisition_order(
            len(development), initial, settings.seed + 1
        ),
        "coverage": coverage_acquisition_order(
            development,
            initial,
            settings.seed + 2,
            lon_degrees=settings.coverage_lon_degrees,
            lat_degrees=settings.coverage_lat_degrees,
        ),
    }

    x_development = build_features(development)
    x_test = build_features(test)
    y_development = development["fco2"].to_numpy()
    y_test = test["fco2"].to_numpy()
    cells = coverage_cells(
        development,
        lon_degrees=settings.coverage_lon_degrees,
        lat_degrees=settings.coverage_lat_degrees,
    )
    _, cell_codes = np.unique(cells, axis=0, return_inverse=True)
    n_available_cells = int(cell_codes.max() + 1)

    metric_rows = []
    selection_rows = []
    prediction_frames = []
    for strategy, order in acquisition_orders.items():
        for budget in sorted(settings.budgets):
            target_size = _target_size(len(development), budget, len(initial))
            additions_needed = target_size - len(initial)
            selected = np.concatenate([initial, order[:additions_needed]])

            model = make_model(settings.seed)
            model.fit(x_development.iloc[selected], y_development[selected])
            prediction = model.predict(x_test)
            scores = regression_metrics(y_test, prediction)
            residual = prediction - y_test
            selected_cell_counts = np.bincount(
                cell_codes[selected], minlength=n_available_cells
            )
            metric_rows.append(
                {
                    "regime": regime,
                    "strategy": strategy,
                    "budget_fraction": budget,
                    "n_development": len(development),
                    "n_train": len(selected),
                    "n_test": len(test),
                    **scores,
                    "seed": settings.seed,
                }
            )
            selection_rows.append(
                {
                    "regime": regime,
                    "strategy": strategy,
                    "budget_fraction": budget,
                    "n_train": len(selected),
                    "occupied_coverage_cells": int(
                        np.count_nonzero(selected_cell_counts)
                    ),
                    "available_coverage_cells": n_available_cells,
                    "coverage_cell_count_cv": float(
                        selected_cell_counts.std() / selected_cell_counts.mean()
                    ),
                    "seed": settings.seed,
                }
            )
            prediction_frames.append(
                pd.DataFrame(
                    {
                        "observation_id": test.get(
                            "observation_id", pd.Series(range(len(test)))
                        ).to_numpy(),
                        "regime": regime,
                        "strategy": strategy,
                        "budget_fraction": budget,
                        "seed": settings.seed,
                        "observed_fco2": y_test,
                        "predicted_fco2": prediction,
                        "absolute_error": np.abs(residual),
                        "squared_error": np.square(residual),
                    }
                )
            )

    return (
        pd.DataFrame(metric_rows),
        pd.DataFrame(selection_rows),
        pd.concat(prediction_frames, ignore_index=True),
    )


def run_regime(
    frame: pd.DataFrame,
    *,
    regime: str,
    split_column: str,
    settings: ExperimentSettings,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run both strategies against one locked validation regime."""
    metrics, selections, _ = run_regime_detailed(
        frame,
        regime=regime,
        split_column=split_column,
        settings=settings,
    )
    return metrics, selections
