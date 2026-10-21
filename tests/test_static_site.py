"""Contract checks for the frozen static portfolio site."""

from __future__ import annotations

import json
import runpy
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def test_static_site_entry_points_exist() -> None:
    for path in (SITE / "index.html", SITE / "ocean.css", SITE / "story.js", SITE / "globes.js", SITE / "i18n.js"):
        assert path.is_file()
        assert path.stat().st_size > 0


def test_globe_values_are_frozen_source_exports_not_new_predictions() -> None:
    data = json.loads((SITE / "data/globe-data.json").read_text(encoding="utf-8"))
    assert data["metadata"]["no_new_fits"] is True
    assert data["metadata"]["sampling_seed"] == 0
    assert data["metadata"]["error_seeds"] == 20
    samples = pd.read_parquet(ROOT / "results/public/osse_visual_demo_sampling.parquet")
    for key, strategy in (
        ("random", "random"),
        ("historical", "historical_density"),
        ("coverage", "spatial_coverage"),
    ):
        expected = samples.loc[
            samples.strategy == strategy, ["longitude", "latitude", "observations"]
        ].to_numpy()
        np.testing.assert_array_equal(data["sampling"][key], expected)
        assert sum(row[2] for row in data["sampling"][key]) == 5000
    fields = pd.read_parquet(ROOT / "results/public/osse_visual_demo_fields.parquet")
    expected = fields[
        [
            "longitude",
            "latitude",
            "absolute_error_random",
            "absolute_error_historical_density",
            "absolute_error_spatial_coverage",
        ]
    ].to_numpy()
    actual = np.asarray(data["fields"], dtype=float)
    np.testing.assert_allclose(actual, expected, atol=0.000051, rtol=0, equal_nan=True)
    assert len(actual) == 40624
    np.testing.assert_array_equal(np.isnan(actual), np.isnan(expected))
    assert "not vessel locations" in data["metadata"]["coordinates"]


def test_chart_export_matches_sources_without_new_model_fits() -> None:
    exporter = ROOT / "scripts/export_site_chart_data.py"
    build = runpy.run_path(str(exporter))["build_chart_data"]
    frozen = json.loads((SITE / "data/chart-data.json").read_text(encoding="utf-8"))
    assert build(ROOT / "results/public") == frozen
    assert frozen["provenance"]["no_new_fits"] is True
    assert ".fit(" not in exporter.read_text(encoding="utf-8")
    audit = {
        (r["mask"], r["protocol"], r["comparison"]): r
        for r in frozen["mask_audit"]["rows"]
    }
    assert len(audit) == 12
    latitude_cap = pd.read_csv(ROOT / "results/public/osse_latitude_cap_overall.csv")
    latitude_cap = latitude_cap.loc[
        (latitude_cap.budget == 5000)
        & (latitude_cap.domain == "south_of_60n")
        & (latitude_cap.weighting == "spherical_cell_area")
    ]
    assert frozen["mask_audit"]["locations_below_60n"] == {
        "m0": 36215,
        "m1": 36108,
        "m2": 33089,
    }
    for scheme, n in (("hidden", 3), ("block", 15)):
        rows = frozen["pairs"][scheme]
        assert len(rows) == n
        assert all(r["historical"] > r["random"] for r in rows)
        primary = audit[("m1", scheme, "historical_density")]
        for field, metric in (("random", "random_mae"), ("historical", "comparator_mae")):
            mean = sum(r[field] for r in rows) / n
            assert round(mean, 3) == primary[metric]
        # The pre-mask reference row comes straight from the latitude-cap audit.
        source = latitude_cap.loc[
            (latitude_cap.validation_scheme == f"{'hidden_cells' if scheme == 'hidden' else 'whole_blocks'}_latitude_cap")
            & (latitude_cap.comparison == "historical_density_minus_random")
        ].iloc[0]
        reference = audit[("m0", scheme, "historical_density")]
        assert reference["random_mae"] == round(float(source.mean_random_mae), 3)
        assert reference["comparator_mae"] == round(float(source.mean_comparator_mae), 3)
    for mask in ("m0", "m1", "m2"):
        assert audit[(mask, "hidden", "historical_density")]["units_mae_worse"] == 3
        assert audit[(mask, "block", "historical_density")]["units_mae_worse"] == 15
