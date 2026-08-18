from __future__ import annotations

import numpy as np
import pytest

from ocean_carbon_sampling.osse import (
    PASCAL_TO_MICROATMOSPHERE,
    aggregate_curvilinear_to_regular,
    pa_to_microatmosphere,
    regular_grid_centers,
)


def test_pa_to_microatmosphere_converts_one_atmosphere():
    converted = pa_to_microatmosphere(np.array([101_325.0]))

    assert converted[0] == pytest.approx(1_000_000.0)
    assert PASCAL_TO_MICROATMOSPHERE == pytest.approx(9.869232667)


def test_regular_grid_centers_are_cell_centred():
    latitude, longitude = regular_grid_centers(1.0)

    assert latitude.shape == (180,)
    assert longitude.shape == (360,)
    assert (latitude[0], latitude[-1]) == (-89.5, 89.5)
    assert (longitude[0], longitude[-1]) == (-179.5, 179.5)


def test_aggregate_curvilinear_averages_occupied_bins_only():
    values = np.array([[[2.0, 4.0, np.nan]]])
    latitude = np.array([[0.2, 0.3, 10.2]])
    longitude = np.array([[20.2, 20.4, 30.2]])

    aggregated, counts = aggregate_curvilinear_to_regular(
        values, latitude, longitude
    )

    assert aggregated[0, 90, 200] == pytest.approx(3.0)
    assert counts[0, 90, 200] == 2
    assert np.isnan(aggregated[0, 100, 210])
    assert counts[0, 100, 210] == 0


def test_aggregate_curvilinear_rejects_shape_mismatch():
    with pytest.raises(ValueError, match="coordinate shapes"):
        aggregate_curvilinear_to_regular(
            np.ones((1, 2, 2)), np.ones((2, 3)), np.ones((2, 3))
        )


def test_aggregate_curvilinear_ignores_missing_coordinates():
    aggregated, counts = aggregate_curvilinear_to_regular(
        np.array([[[1.0, 2.0]]]),
        np.array([[0.2, np.nan]]),
        np.array([[20.2, np.nan]]),
    )

    assert aggregated[0, 90, 200] == pytest.approx(1.0)
    assert counts.sum() == 1


def test_aggregate_curvilinear_supports_native_cell_area_weights():
    aggregated, counts = aggregate_curvilinear_to_regular(
        np.array([[[2.0, 4.0, 100.0]]]),
        np.array([[0.2, 0.3, 0.4]]),
        np.array([[20.2, 20.4, 20.6]]),
        cell_weights=np.array([[1.0, 3.0, 0.0]]),
    )

    assert aggregated[0, 90, 200] == pytest.approx(3.5)
    assert counts[0, 90, 200] == 2


def test_aggregate_curvilinear_rejects_weight_shape_mismatch():
    with pytest.raises(ValueError, match="cell_weights"):
        aggregate_curvilinear_to_regular(
            np.ones((1, 2, 2)),
            np.ones((2, 2)),
            np.ones((2, 2)),
            cell_weights=np.ones((2, 3)),
        )
