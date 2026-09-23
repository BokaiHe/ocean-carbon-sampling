"""Contract checks for the frozen static portfolio site."""

from __future__ import annotations

import csv
import json
import re
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
    assert data["metadata"]["default_estimand"] == "area|both60|hidden"
    default = data["estimands"]["area|both60|hidden"]
    assert default["status"] == "default"
    assert default["metrics"]["bias"]["difference"] == -0.835
    assert default["metrics"]["mae"]["random"] == 9.508
    assert default["metrics"]["mae"]["difference"] == 2.466
    assert default["metrics"]["mae"]["relative_pct"] == 25.94
    assert default["metrics"]["mae"]["direction"] == "3/3 worse"
    stress = data["estimands"]["area|both60|block"]
    assert stress["status"] == "supporting"
    assert stress["metrics"]["mae"]["relative_pct"] == 15.67
    assert stress["metrics"]["mae"]["direction"] == "15/15 worse"
    assert sum(r["status"] == "default" for r in data["estimands"].values()) == 1


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
    priority = SITE / data["maps"]["priority_diagnostic"]
    assert priority.is_file()
    assert priority.stat().st_size > 10_000
    assert "not a causal marginal-gain map" in data["maps"]["priority_definition"]


def test_site_is_english_only_and_workflow_is_complete() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert re.search(r"[\u3400-\u9fff]", html) is None
    assert 'id="workflow"' in html
    assert html.count('class="workflow-card"') == 6
    assert html.count('class="workflow-icon"') == 6


def test_headline_evaluations_match_frozen_source_tables() -> None:
    data = load_site_data()
    with (ROOT / "results/public/osse_latitude_cap_overall.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        rows = list(csv.DictReader(source))
    for scheme, source_scheme in (("hidden", "hidden_cells"), ("block", "whole_blocks")):
        selected = [r for r in rows if (
            r["validation_scheme"] == f"{source_scheme}_latitude_cap"
            and r["domain"] == "south_of_60n"
            and r["weighting"] == "spherical_cell_area"
            and r["comparison"] == "historical_density_minus_random"
            and r["budget"] == "5000"
        )]
        assert len(selected) == 1
        row = selected[0]
        record = data["estimands"][f"area|both60|{scheme}"]
        assert record["n_units"] == int(row["n_units"])
        for metric, payload in record["metrics"].items():
            for key, column in (
                ("random", f"mean_random_{metric}"),
                ("comparator", f"mean_comparator_{metric}"),
                ("difference", f"mean_difference_{metric}"),
            ):
                assert payload[key] == round(float(row[column]), 3)


def test_presentation_scope_credit_and_working_repository_links() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    js = (SITE / "app.js").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert 'id="validation-comparison"' in html
    assert "renderValidationComparison();" in js
    assert "state.data.metadata.default_estimand.split" in js
    assert "+25.94<span>%" in html
    assert "3/3" in html and "15/15" in html
    assert "approximately 20%" in readme and "about 20%" in html
    assert "<span>Historical</span>" not in html
    assert "<span>Historical-density</span>" in html
    for text in (html, readme):
        assert "Galen A. McKinley" in text
        assert "10.1029/2020GB006788" in text
        assert "10.5194/bg-21-2159-2024" in text
        assert "https://github.com/spariser/ReconstructOceanCarbonP3G1" in text
    assert "mailto:bh2954@columbia.edu" in html
    assert "../docs/" not in js
    assert "https://github.com/BokaiHe/ocean-carbon-sampling/blob/main/docs/osse_regrid_audit_results.md" in js
    assert "before training" in html
    assert "because they are" not in html
