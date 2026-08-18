"""Preprocessing utilities for the global observing-system simulation experiment."""

from __future__ import annotations

import numpy as np

PASCAL_TO_MICROATMOSPHERE = 1_000_000.0 / 101_325.0


def pa_to_microatmosphere(values: np.ndarray) -> np.ndarray:
    """Convert pressure from Pa to micro-atmospheres."""
    return np.asarray(values) * PASCAL_TO_MICROATMOSPHERE


def regular_grid_centers(
    resolution_degrees: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Return latitude and longitude centres for a global regular grid."""
    _validate_resolution(resolution_degrees)
    latitudes = np.arange(-90.0, 90.0, resolution_degrees) + resolution_degrees / 2
    longitudes = np.arange(-180.0, 180.0, resolution_degrees) + resolution_degrees / 2
    return latitudes, longitudes


def aggregate_curvilinear_to_regular(
    values: np.ndarray,
    latitude: np.ndarray,
    longitude: np.ndarray,
    *,
    resolution_degrees: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Average native cell-centre values within occupied regular-grid bins.

    ``values`` must have shape ``(time, y, x)`` and the coordinate arrays must
    have shape ``(y, x)``. Unoccupied output bins remain NaN.
    """
    _validate_resolution(resolution_degrees)
    data = np.asarray(values, dtype=np.float64)
    lat = np.asarray(latitude, dtype=np.float64)
    lon = np.asarray(longitude, dtype=np.float64)
    if data.ndim != 3:
        raise ValueError("values must have shape (time, y, x)")
    if lat.shape != lon.shape or data.shape[1:] != lat.shape:
        raise ValueError("coordinate shapes must match the spatial data dimensions")

    latitudes, longitudes = regular_grid_centers(resolution_degrees)
    n_lat = latitudes.size
    n_lon = longitudes.size
    n_bins = n_lat * n_lon

    finite_coordinates = np.isfinite(lat) & np.isfinite(lon)
    safe_latitude = np.where(finite_coordinates, lat, -90.0)
    safe_longitude = np.where(finite_coordinates, lon, -180.0)
    normalized_lon = ((safe_longitude + 180.0) % 360.0) - 180.0
    lat_index = np.floor((safe_latitude + 90.0) / resolution_degrees).astype(
        np.int64
    )
    lon_index = np.floor((normalized_lon + 180.0) / resolution_degrees).astype(
        np.int64
    )
    coordinate_valid = (
        finite_coordinates
        & (lat_index >= 0)
        & (lat_index < n_lat)
        & (lon_index >= 0)
        & (lon_index < n_lon)
    )
    bin_id = lat_index * n_lon + lon_index

    output = np.full((data.shape[0], n_bins), np.nan, dtype=np.float64)
    counts = np.zeros((data.shape[0], n_bins), dtype=np.int32)
    flat_bins = bin_id.ravel()
    flat_coordinates = coordinate_valid.ravel()
    for time_index, field in enumerate(data):
        flat_values = field.ravel()
        valid = flat_coordinates & np.isfinite(flat_values)
        time_counts = np.bincount(flat_bins[valid], minlength=n_bins)
        time_sums = np.bincount(
            flat_bins[valid], weights=flat_values[valid], minlength=n_bins
        )
        occupied = time_counts > 0
        output[time_index, occupied] = time_sums[occupied] / time_counts[occupied]
        counts[time_index] = time_counts.astype(np.int32)

    shape = (data.shape[0], n_lat, n_lon)
    return output.reshape(shape), counts.reshape(shape)


def _validate_resolution(resolution_degrees: float) -> None:
    if resolution_degrees <= 0:
        raise ValueError("resolution_degrees must be positive")
    divisions = 180 / resolution_degrees
    if not np.isclose(divisions, round(divisions)):
        raise ValueError("resolution_degrees must divide 180 exactly")
