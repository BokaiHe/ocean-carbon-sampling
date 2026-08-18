import numpy as np
import pandas as pd

from ocean_carbon_sampling.sampling import (
    coverage_acquisition_order,
    coverage_cells,
    initial_sample,
    random_acquisition_order,
)


def test_sampling_orders_are_reproducible_and_complete() -> None:
    frame = pd.DataFrame(
        {
            "longitude": np.linspace(-179, 179, 50),
            "latitude": np.linspace(-79, -36, 50),
        }
    )
    initial = initial_sample(len(frame), 0.1, seed=7)
    random_one = random_acquisition_order(len(frame), initial, seed=8)
    random_two = random_acquisition_order(len(frame), initial, seed=8)
    coverage_one = coverage_acquisition_order(frame, initial, seed=9)
    coverage_two = coverage_acquisition_order(frame, initial, seed=9)

    assert np.array_equal(random_one, random_two)
    assert np.array_equal(coverage_one, coverage_two)
    assert set(initial).isdisjoint(random_one)
    assert set(initial).isdisjoint(coverage_one)
    assert len(random_one) == len(frame) - len(initial)
    assert len(coverage_one) == len(frame) - len(initial)


def test_coverage_prefix_reaches_more_cells_in_imbalanced_pool() -> None:
    dense = pd.DataFrame({"longitude": np.zeros(100), "latitude": np.full(100, -50.0)})
    sparse = pd.DataFrame(
        {
            "longitude": [-100.0, 100.0, 150.0],
            "latitude": [-60.0, -65.0, -70.0],
        }
    )
    frame = pd.concat([dense, sparse], ignore_index=True)
    initial = np.array([0, 1, 2, 3, 4])
    order = coverage_acquisition_order(frame, initial, seed=3)
    selected = np.concatenate([initial, order[:3]])
    cells = coverage_cells(frame)

    assert np.unique(cells[selected], axis=0).shape[0] == 4
