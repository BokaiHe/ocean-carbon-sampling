"""Contract checks for the frozen static portfolio site."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def load_site_data() -> dict:
    return json.loads((SITE / "data" / "site-data.json").read_text(encoding="utf-8"))


def test_static_site_entry_points_exist() -> None:
    for path in (SITE / "index.html", SITE / "styles.css", SITE / "app.js"):
        assert path.is_file()
        assert path.stat().st_size > 0


def test_estimand_contract_is_complete_and_defaults_are_locked() -> None:
    data = load_site_data()
    assert len(data["estimands"]) == 12
    assert data["metadata"]["default_estimand"] == "area|both60|block"
    default = data["estimands"]["area|both60|block"]
    assert default["status"] == "default"
    assert default["metrics"]["bias"]["difference"] == -0.473
    assert default["metrics"]["mae"]["random"] == 11.836
    assert default["metrics"]["mae"]["difference"] == 1.855
    assert default["metrics"]["mae"]["relative_pct"] == 15.67
    assert default["metrics"]["mae"]["direction"] == "15/15 worse"


def test_sensitivity_journey_and_sample_sweep_are_complete() -> None:
    data = load_site_data()
    journey = data["estimand_journey"]
    assert journey == [
        "equal|global|block",
        "area|global|block",
        "area|eval60|block",
        "area|both60|block",
    ]
    assert [data["estimands"][key]["metrics"]["bias"]["difference"] for key in journey] == [
        -4.954,
        -1.884,
        -0.631,
        -0.473,
    ]
    assert set(data["sample_sweep"]) == {"500", "1000", "2500", "5000"}
    for record in data["sample_sweep"].values():
        assert set(record["metrics"]) == {
            "median_absolute_error",
            "p99_absolute_error",
            "rmse",
        }


def test_all_pre_rendered_maps_exist() -> None:
    data = load_site_data()
    assert data["maps"]["zero_coverage_cell_pct"] == 53.1
    assert data["maps"]["zero_coverage_area_pct"] == 49.2
    for strategy in ("random", "historical", "coverage"):
        for variant in ("base", "zero"):
            path = SITE / data["maps"]["images"][strategy][variant]
            assert path.is_file()
            assert path.stat().st_size > 10_000
