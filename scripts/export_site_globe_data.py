"""Export frozen map locations to the globe; no fitting or new predictions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from cartopy.io import shapereader
from shapely.geometry import mapping
from shapely.geometry.polygon import orient


def build_globe_data(results_dir: Path) -> dict:
    sampling = pd.read_parquet(results_dir / "osse_visual_demo_sampling.parquet")
    fields = pd.read_parquet(results_dir / "osse_visual_demo_fields.parquet")
    keys = {
        "random": "random",
        "historical": "historical_density",
        "coverage": "spatial_coverage",
    }
    samples = {}
    for key, strategy in keys.items():
        rows = sampling.loc[sampling.strategy == strategy]
        assert rows.observations.sum() == 5000
        samples[key] = rows[["longitude", "latitude", "observations"]].values.tolist()
    columns = [
        "longitude",
        "latitude",
        "absolute_error_random",
        "absolute_error_historical_density",
        "absolute_error_spatial_coverage",
    ]
    values = fields[columns].to_numpy(dtype=float)
    packed = [
        [None if not np.isfinite(v) else round(float(v), 4) for v in row]
        for row in values
    ]
    return {
        "metadata": {
            "year": 2005,
            "sample_count": 5000,
            "sampling_seed": 0,
            "error_seeds": 20,
            "no_new_fits": True,
            "sampling_source": "results/public/osse_visual_demo_sampling.parquet",
            "error_source": "results/public/osse_visual_demo_fields.parquet",
            "scope": "Original full-domain hidden-cell runs, NOT aligned-domain primary results",
            "sampling_unit": "Observations per 5-degree latitude by 10-degree longitude block",
            "error_unit": "Local mean absolute error (microatmospheres), over paired seeds and available hidden months",
            "field_columns": [
                "longitude",
                "latitude",
                "random_mae",
                "historical_mae",
                "coverage_mae",
            ],
            "missing": "null means no saved error, never zero",
            "coordinates": "Sampling points are block centres, not vessel locations or tracks",
        },
        "sampling": samples,
        "fields": packed,
    }


def build_land() -> dict:
    source = shapereader.natural_earth(
        resolution="110m", category="physical", name="land"
    )
    polygons = []
    for geometry in shapereader.Reader(source).geometries():
        parts = (
            list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
        )
        # D3's spherical polygon convention requires clockwise small polygons.
        polygons.extend(mapping(orient(part, sign=-1))["coordinates"] for part in parts)
    return {"type": "MultiPolygon", "coordinates": polygons}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=Path("results/public"))
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    args = parser.parse_args()
    target = args.site_dir / "data"
    target.mkdir(parents=True, exist_ok=True)
    for name, data in (
        ("globe-data.json", build_globe_data(args.results_dir)),
        ("globe-land.json", build_land()),
    ):
        (target / name).write_text(
            json.dumps(data, separators=(",", ":"), allow_nan=False), encoding="utf-8"
        )
        print(name, (target / name).stat().st_size)
