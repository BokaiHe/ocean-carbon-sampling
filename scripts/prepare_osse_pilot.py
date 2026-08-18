"""Create one or more annual 1-degree CMIP6 cubes for the OSSE."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ocean_carbon_sampling.cmip6 import load_manifest
from ocean_carbon_sampling.osse import (
    aggregate_curvilinear_to_regular,
    pa_to_microatmosphere,
    regular_grid_centers,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/osse_pilot.yaml")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        help="years to prepare; defaults to processing.pilot_year",
    )
    return parser.parse_args()


def _year_path(processing: dict[str, object], key: str, year: int) -> Path:
    template_key = f"{key}_template"
    if template_key in processing:
        return Path(str(processing[template_key]).format(year=year))
    return Path(str(processing[key]))


def prepare_year(
    *,
    year: int,
    cmip: dict[str, object],
    processing: dict[str, object],
    manifest: pd.DataFrame,
) -> tuple[Path, pd.DataFrame]:
    """Prepare a single annual cube and return its audit table."""
    source_dir = Path(str(cmip["raw_directory"]))
    resolution = float(processing["target_grid_degrees"])
    latitudes, longitudes = regular_grid_centers(resolution)
    arrays: dict[str, tuple[tuple[str, ...], np.ndarray, dict[str, str]]] = {}
    reference_time: np.ndarray | None = None
    reference_latitude: np.ndarray | None = None
    reference_longitude: np.ndarray | None = None
    reference_counts: np.ndarray | None = None
    audit_rows: list[dict[str, object]] = []

    for entry in manifest.itertuples(index=False):
        path = source_dir / entry.filename
        with xr.open_dataset(path, engine="h5netcdf", decode_times=True) as source:
            selected = source[entry.variable].sel(
                time=slice(f"{year}-01", f"{year}-12")
            )
            expected_months = int(processing["expected_months"])
            if selected.sizes.get("time") != expected_months:
                raise ValueError(
                    f"{entry.variable} does not contain {expected_months} months "
                    f"for {year}"
                )
            time = selected["time"].values
            latitude = source["nav_lat"].values
            longitude = source["nav_lon"].values
            if reference_time is None:
                reference_time = time
                reference_latitude = latitude
                reference_longitude = longitude
            else:
                if not np.array_equal(reference_time, time):
                    raise ValueError("CMIP6 variables have different annual time axes")
                if not np.allclose(reference_latitude, latitude, equal_nan=True):
                    raise ValueError("CMIP6 variables have different latitude grids")
                if not np.allclose(reference_longitude, longitude, equal_nan=True):
                    raise ValueError("CMIP6 variables have different longitude grids")

            native = selected.values
            regular, counts = aggregate_curvilinear_to_regular(
                native,
                latitude,
                longitude,
                resolution_degrees=resolution,
            )
            if entry.variable == "spco2":
                regular = pa_to_microatmosphere(regular)
                units = "microatmosphere"
                reference_counts = counts
            else:
                units = str(selected.attrs.get("units", ""))
            arrays[entry.variable] = (
                ("time", "latitude", "longitude"),
                regular.astype(np.float32),
                {"units": units, "source_variable": entry.variable},
            )
            finite_by_month = np.isfinite(regular).sum(axis=(1, 2))
            quantiles = np.nanquantile(regular, [0.001, 0.01, 0.5, 0.99, 0.999])
            maximum_index = np.unravel_index(np.nanargmax(regular), regular.shape)
            audit_rows.append(
                {
                    "year": year,
                    "variable": entry.variable,
                    "native_finite_cells_per_month": int(
                        np.isfinite(native[0]).sum()
                    ),
                    "regular_finite_bins_min": int(finite_by_month.min()),
                    "regular_finite_bins_max": int(finite_by_month.max()),
                    "minimum": float(np.nanmin(regular)),
                    "q001": float(quantiles[0]),
                    "q01": float(quantiles[1]),
                    "median": float(quantiles[2]),
                    "q99": float(quantiles[3]),
                    "q999": float(quantiles[4]),
                    "maximum": float(np.nanmax(regular)),
                    "maximum_time": str(time[maximum_index[0]])[:10],
                    "maximum_latitude": float(latitudes[maximum_index[1]]),
                    "maximum_longitude": float(longitudes[maximum_index[2]]),
                    "values_above_1000": (
                        int((regular > 1000).sum())
                        if entry.variable == "spco2"
                        else ""
                    ),
                    "units": units,
                }
            )

    if reference_time is None or reference_counts is None:
        raise RuntimeError("No required CMIP6 variables were processed")
    ocean_bins = int((reference_counts > 0).sum(axis=(1, 2)).min())
    if ocean_bins < int(processing["minimum_ocean_bins"]):
        raise ValueError(f"Only {ocean_bins} occupied ocean bins; gate not met")

    arrays["source_cell_count"] = (
        ("time", "latitude", "longitude"),
        reference_counts,
        {"long_name": "native cells contributing to each regular-grid value"},
    )
    dataset = xr.Dataset(
        data_vars=arrays,
        coords={
            "time": reference_time,
            "latitude": latitudes,
            "longitude": longitudes,
        },
        attrs={
            "title": f"IPSL-CM6A-LR {year} global OSSE cube",
            "source_id": cmip["source_id"],
            "experiment_id": cmip["experiment_id"],
            "member_id": cmip["member_id"],
            "source_grid": cmip["grid_label"],
            "source_version": cmip["version"],
            "regrid_method": processing["regrid_method"],
            "analysis_status": "prespecified cross-year robustness analysis",
        },
    )
    output = _year_path(processing, "processed_file", year)
    output.parent.mkdir(parents=True, exist_ok=True)
    encoding = {
        name: {"compression": "gzip", "compression_opts": 4}
        for name in dataset.data_vars
    }
    dataset.to_netcdf(output, engine="h5netcdf", encoding=encoding)

    audit = pd.DataFrame(audit_rows)
    audit_path = _year_path(processing, "audit_file", year)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(audit_path, index=False)
    return output, audit


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    cmip = config["cmip6"]
    processing = config["processing"]
    manifest = load_manifest(cmip["manifest"])
    years = args.years or [int(processing["pilot_year"])]
    for year in years:
        output, audit = prepare_year(
            year=year,
            cmip=cmip,
            processing=processing,
            manifest=manifest,
        )
        print(audit.to_string(index=False))
        print(f"\nSaved {output} ({output.stat().st_size / 1_000_000:.1f} MB)\n")


if __name__ == "__main__":
    main()
