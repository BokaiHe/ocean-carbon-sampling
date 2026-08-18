from __future__ import annotations

import numpy as np
import pandas as pd

from ocean_carbon_sampling.osse_experiment import (
    fixed_budget_orders,
    historical_density_weights,
    stratified_evaluation_positions,
)


def _candidate_frame(n_per_month: int = 20) -> pd.DataFrame:
    month = np.repeat([1, 2], n_per_month)
    position = np.tile(np.arange(n_per_month), 2)
    return pd.DataFrame(
        {
            "month": month,
            "latitude": -80.0 + position,
            "longitude": -170.0 + 2 * position,
        }
    )


def test_stratified_evaluation_is_reproducible_and_month_balanced():
    frame = _candidate_frame()

    first = stratified_evaluation_positions(frame, fraction=0.2, seed=7)
    second = stratified_evaluation_positions(frame, fraction=0.2, seed=7)

    assert np.array_equal(first, second)
    assert frame.iloc[first].groupby("month").size().to_dict() == {1: 4, 2: 4}


def test_historical_density_uses_only_requested_years():
    candidates = pd.DataFrame(
        {"month": [1, 1], "latitude": [0.5, 1.5], "longitude": [10.5, 11.5]}
    )
    socat = pd.DataFrame(
        {
            "date": pd.to_datetime(["2004-01-16", "2005-01-16"]),
            "latitude": [0.5, 1.5],
            "longitude": [10.5, 11.5],
            "fco2_count": [20, 100],
        }
    )

    weights = historical_density_weights(
        candidates, socat, year_start=1990, year_end=2004
    )

    assert weights.tolist() == [20.0, 0.0]


def test_fixed_budget_orders_are_unique_nested_and_target_blind():
    frame = _candidate_frame(n_per_month=50)
    weights = np.arange(1, len(frame) + 1, dtype=float)

    orders = fixed_budget_orders(frame, weights, maximum_budget=20, seed=3)

    assert set(orders) == {"random", "historical_density", "spatial_coverage"}
    for order in orders.values():
        assert len(order) == 20
        assert len(np.unique(order)) == 20
        assert np.array_equal(order[:10], order[:20][:10])


def test_historical_order_never_selects_zero_weight_candidates():
    frame = _candidate_frame(n_per_month=30)
    weights = np.zeros(len(frame))
    weights[:25] = 1.0

    orders = fixed_budget_orders(frame, weights, maximum_budget=20, seed=2)

    assert np.all(weights[orders["historical_density"]] > 0)
