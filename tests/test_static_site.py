"""Contract checks for the frozen static portfolio site."""

from __future__ import annotations

import csv
import json
import re
import runpy
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def load_site_data() -> dict:
    return json.loads((SITE / "data" / "site-data.json").read_text(encoding="utf-8"))


def test_static_site_entry_points_exist() -> None:
    for path in (SITE / "index.html", SITE / "styles.css", SITE / "app.js"):
        assert path.is_file()
        assert path.stat().st_size > 0


def test_globe_land_overlay_is_last_and_disclosed_as_display_only() -> None:
    js = (SITE / "globe.js").read_text(encoding="utf-8")
    fill = "path(land);ctx.fillStyle='#ffffff';ctx.fill();"
    outline = "ctx.strokeStyle='#000000';ctx.lineWidth=1.35"
    assert js.index(fill) > js.index("if(selected){const hit=visible.find")
    assert js.index(outline) > js.index(fill)
    assert js.count("path(land)") == 1
    assert "d3.geoContains(land,location)" in js
    assert "Covered by the land overlay; retained in source data" in js
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert "White land overlays data symbols for display only" in html
    assert "not a scientific exclusion mask" in html


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


def test_globe_retains_scope_fallback_and_local_dependencies() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    js = (SITE / "globe.js").read_text(encoding="utf-8")
    assert 'aria-label="Research chapters"' in html
    assert 'id="ocean-globe"' in html
    assert 'id="globe-coordinate-form"' in html
    assert "not live vessel tracking" in html
    assert "not the aligned &lt;60°N primary evaluation" in html
    assert "not real ship tracks" in html
    assert "No route or marginal benefit" in html
    assert "prefers-reduced-motion" in js
    assert "pointercancel" in js
    assert "document.hidden" in js
    assert "flat maps and result charts below are still available" in js
    assert (SITE / "vendor/d3-7.9.0.min.js").stat().st_size > 100000
    assert (SITE / "vendor/D3-LICENSE.txt").is_file()
    land = json.loads((SITE / "data/globe-land.json").read_text(encoding="utf-8"))
    assert land["type"] == "MultiPolygon"
    assert len(land["coordinates"]) > 100


def test_image_enlargement_stays_on_page_with_accessible_exit() -> None:
    js = (SITE / "app.js").read_text(encoding="utf-8")
    css = (SITE / "styles.css").read_text(encoding="utf-8")
    assert 'document.createElement("dialog")' in js
    assert 'aria-label="Close enlarged map"' in js
    assert "imageViewer.showModal()" in js
    assert "imageViewer.close()" in js
    assert 'imageViewer.addEventListener("close"' in js
    assert "focus({preventScroll:true})" in js
    assert "top:imageScroll" in js
    assert 'link.hasAttribute("download")' in js
    assert ".image-viewer::backdrop" in css
    assert ".image-viewer-toolbar button:focus-visible" in css


def test_ocean_editorial_layout_keeps_context_separate_from_evidence() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    css = (SITE / "styles.css").read_text(encoding="utf-8")
    header = html.split("</header>", 1)[0]
    assert 'id="paired-chart"' not in header
    assert 'class="story-rail shell"' in header
    assert 'id="paired-evidence"' in html
    assert "ArtHouse Studio / Pexels" in html
    assert "NOAA Ocean Exploration" in html
    assert "Context imagery, not model output." in html
    assert "not the specific surface pCO₂ system" in html
    assert "nasa-celtic-sea-phytoplankton.jpg" in css
    assert "prefers-reduced-motion" in css
    for name in ("nasa-celtic-sea-phytoplankton.jpg", "noaa-ctd-launch.jpg"):
        assert (SITE / "assets" / "context" / name).is_file()


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
    assert [
        data["estimands"][key]["metrics"]["bias"]["difference"] for key in journey
    ] == [
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
    flow = html.split('class="workflow-flow"', 1)[1].split("</ol>", 1)[0]
    assert flow.count("<li>") == 5
    assert flow.count("<svg ") == 5


def test_headline_evaluations_match_frozen_source_tables() -> None:
    data = load_site_data()
    with (ROOT / "results/public/osse_latitude_cap_overall.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        rows = list(csv.DictReader(source))
    for scheme, source_scheme in (
        ("hidden", "hidden_cells"),
        ("block", "whole_blocks"),
    ):
        selected = [
            r
            for r in rows
            if (
                r["validation_scheme"] == f"{source_scheme}_latitude_cap"
                and r["domain"] == "south_of_60n"
                and r["weighting"] == "spherical_cell_area"
                and r["comparison"] == "historical_density_minus_random"
                and r["budget"] == "5000"
            )
        ]
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
    assert 'id="paired-chart"' in html
    assert '"data/chart-data.json"' in js
    assert "3 year means" in html and "15 year–fold means" in html
    assert "approximately 20%" in readme and "about 20%" in html
    assert "<span>Historical</span>" not in html
    assert ">Historical-density</button>" in html
    for text in (html, readme):
        assert "Galen A. McKinley" in text
        assert "10.1029/2020GB006788" in text
        assert "10.5194/bg-21-2159-2024" in text
        assert "https://github.com/spariser/ReconstructOceanCarbonP3G1" in text
    assert "mailto:bh2954@columbia.edu" in html
    assert "../docs/" not in js
    assert (
        "https://github.com/BokaiHe/ocean-carbon-sampling/blob/main/docs/osse_regrid_audit_results.md"
        in js
    )
    assert "before training" in html
    assert "because they are" not in html


def test_story_order_and_archived_map_scope() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    sections = re.findall(r'<section[^>]+id="([^"]+)"', html)
    assert sections.index("results") < sections.index("sample-count")
    assert sections.index("sample-count") < sections.index("estimand")
    assert sections.index("estimand") < sections.index("technical")
    technical = html.split('id="technical"', 1)[1].split("</section>", 1)[0]
    assert '<details id="archived-bias-map">' in technical
    assert technical.count('id="priority-map"') == 1
    assert html.count('id="priority-map"') == 1
    assert "Not a sampling-priority map." in technical
    assert "locations north of 60°N" in technical
    assert "Where should a follow-up sampling experiment test first?" not in html
    assert "Why this different scope?" in html
    assert "reversal threshold cannot be transferred" in html
    assert '<details class="mobile-navigation" id="mobile-navigation">' in html
    assert "Escape" in (SITE / "app.js").read_text(encoding="utf-8")


def test_chart_export_matches_sources_without_new_model_fits() -> None:
    exporter = ROOT / "scripts/export_site_chart_data.py"
    build = runpy.run_path(str(exporter))["build_chart_data"]
    frozen = json.loads((SITE / "data/chart-data.json").read_text(encoding="utf-8"))
    assert build(ROOT / "results/public") == frozen
    assert frozen["provenance"]["no_new_fits"] is True
    assert ".fit(" not in exporter.read_text(encoding="utf-8")
    for scheme, n in (("hidden", 3), ("block", 15)):
        rows = frozen["pairs"][scheme]
        assert len(rows) == n
        assert all(r["historical"] > r["random"] for r in rows)
        for field, metric in (("random", "random"), ("historical", "comparator")):
            mean = sum(r[field] for r in rows) / n
            expected = load_site_data()["estimands"][f"area|both60|{scheme}"][
                "metrics"
            ]["mae"][metric]
            assert round(mean, 3) == expected
    assert [r["blocks"] for r in frozen["sampling"]["blocks"]] == [955, 622, 1026]
    assert all(r["sample_count"] == 5000 for r in frozen["sampling"]["blocks"])
    assert frozen["error_map_availability"]["primary_domain_map_available"] is False


def test_visual_brief_charts_retain_scopes_and_accessible_values() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    js = (SITE / "app.js").read_text(encoding="utf-8")
    for name in ("paired", "block", "robustness", "sweep", "bias"):
        assert f'id="{name}-chart"' in html
        assert f'id="{name}-table"' in html
    assert "correlated evaluation variants" in html
    assert "not confidence intervals" in html
    assert "not an estimated continuous learning curve" in html
    assert "not a time series" in html
    assert "not per-cell predictions" in html
    assert 'id="budget-slider"' not in html
    assert '"aria-labelledby"' in js
    assert '"mouseenter","focus","click"' in js


def test_supporting_error_map_preserves_every_source_location_and_difference() -> None:
    source = pd.read_parquet(ROOT / "results/public/osse_visual_demo_fields.parquet")
    exported = pd.read_csv(SITE / "data/supporting-error-map.csv")
    audit = json.loads(
        (SITE / "data/supporting-error-map.json").read_text(encoding="utf-8")
    )
    pd.testing.assert_frame_equal(
        exported[["latitude", "longitude"]], source[["latitude", "longitude"]]
    )
    expected = source.absolute_error_historical_density - source.absolute_error_random
    np.testing.assert_allclose(exported.delta_mae_uatm, expected, equal_nan=True)
    assert len(exported) == audit["source_locations"] == 40624
    assert expected.notna().sum() == audit["finite_locations"] == 37920
    assert expected.isna().sum() == audit["missing_locations"] == 2704
    assert (expected < -30).sum() == audit["below_colour_scale"] == 115
    assert (expected > 30).sum() == audit["above_colour_scale"] == 2169
    assert expected.min() == audit["minimum_uatm"]
    assert expected.max() == audit["maximum_uatm"]
    assert audit["no_new_fits_or_predictions"] is True
    assert (audit["year"], audit["seeds"], audit["sample_count"]) == (2005, 20, 5000)
    for extension in ("png", "svg", "pdf"):
        assert (
            SITE / f"assets/maps/supporting_mae_difference_2005.{extension}"
        ).stat().st_size > 10000
    svg = (SITE / "assets/maps/supporting_mae_difference_2005.svg").read_text(
        encoding="utf-8"
    )
    assert "<text" in svg


def test_refined_charts_and_supporting_map_keep_interpretation_explicit() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert "axis is zoomed, not zero-based" in html
    assert "equally spaced categories, not a linear axis" in html
    supporting = html.split('id="error-map"', 1)[1].split("</section>", 1)[0]
    for phrase in (
        "not the primary scope",
        "2005",
        "20 paired seeds",
        "no mapped error",
        "not global area-weighted contributions",
        "not a crop",
        "±30",
        "No models were retrained",
    ):
        assert phrase in supporting
    assert 'href="data/supporting-error-map.csv"' in supporting
