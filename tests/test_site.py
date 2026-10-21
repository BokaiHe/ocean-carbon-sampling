"""Contracts for the bilingual research page: structure, translations and numbers."""

from __future__ import annotations

import json
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
HTML = (SITE / "index.html").read_text(encoding="utf-8")


def _data(name: str) -> dict:
    return json.loads((SITE / "data" / name).read_text(encoding="utf-8"))


def test_story_runs_intro_background_method_findings_limits():
    order = ["intro", "background", "method", "findings", "f-history", "f-coverage",
             "f-augment", "checks", "conclusion", "limits", "sources"]
    positions = [HTML.index(f'id="{section}"') for section in order]
    assert positions == sorted(positions)
    assert HTML.index('id="hero-root"') < positions[0]
    for removed in ("voyage", "PS103", "unresolved"):
        assert removed not in HTML
    # The intro asks what the findings answer; the second experiment has its own method.
    intro = HTML.split('id="intro"', 1)[1].split("</section>", 1)[0]
    assert "inherit that bias" not in intro and "get worse" in intro
    method = HTML.split('id="method"', 1)[1].split("</section>", 1)[0]
    assert "add to the real network" in method and "Open-ocean interior" in method
    conclusion = HTML.split('id="conclusion"', 1)[1].split("</section>", 1)[0]
    for target in ("#f-history", "#f-coverage", "#f-augment"):
        assert f'href="{target}"' in conclusion


def test_every_translatable_node_has_chinese_text():
    keys = set(re.findall(r'data-i18n="([^"]+)"', HTML))
    source = (SITE / "i18n.js").read_text(encoding="utf-8")
    chinese = set(re.findall(r"'([\w.]+)':'", source))
    assert keys, "page has no translatable text"
    assert keys <= chinese, sorted(keys - chinese)
    hero = (SITE / "src/useLang.jsx").read_text(encoding="utf-8")
    assert "en:{" in hero and "zh:{" in hero
    assert 'data-lang-set="zh"' in HTML


def test_scripts_and_styles_exist_and_are_copied_by_the_build():
    config = (ROOT / "vite.config.js").read_text(encoding="utf-8")
    for name in ("i18n.js", "globes.js", "story.js"):
        assert f'src="{name}?' in HTML
        assert f"'{name}'" in config
        assert (SITE / name).stat().st_size > 0
    assert 'href="ocean.css"' in HTML
    for asset in re.findall(r'src="(assets/[^"]+)"', HTML):
        assert (SITE / asset).is_file(), asset


def test_headline_numbers_match_frozen_results():
    audit = {(r["mask"], r["protocol"], r["comparison"]): r for r in _data("chart-data.json")["mask_audit"]["rows"]}
    primary = audit[("m1", "hidden", "historical_density")]
    assert f"{primary['relative_mae_pct']:.1f}%" == "27.3%"
    assert "+27.3%" in HTML and primary["units_mae_worse"] == 3
    block = audit[("m1", "block", "historical_density")]
    assert f"+{block['relative_mae_pct']:.1f}%" in HTML and block["units_mae_worse"] == 15
    coverage = audit[("m1", "hidden", "spatial_coverage")]
    assert f"−{abs(coverage['difference_rmse']):.1f}" in HTML
    assert f"+{coverage['difference_mae']:.1f}" in HTML


def test_augmentation_numbers_match_the_open_ocean_run():
    built = runpy.run_path(str(ROOT / "scripts/export_site_augmentation.py"))["build"]()
    frozen = _data("augmentation.json")
    assert built == frozen
    assert frozen["metadata"]["no_new_fits"] is True
    assert "M2" in frozen["metadata"]["domain"]
    effects = [p for p in frozen["paired"] if p["domain"] == "global_unobserved" and p["metric"] == "rmse"]
    added = sum(p["improvement"] for p in effects if p["contrast"] == "baseline_minus_random") / 5
    targeted = sum(p["improvement"] for p in effects if p["contrast"] == "random_minus_gap") / 5
    assert f"−{added:.1f}" in HTML
    assert f"−{targeted:.2f}" in HTML
    for arm in ("random_addition", "gap_addition"):
        assert all(len(rows) == 1000 for rows in frozen["map"]["additions"][arm].values())


def test_intro_share_of_observed_month_cells():
    observed = _data("observed-co2.json")["years"]["2014"]
    globe = _data("globe-data.json")["fields"]
    share = 100 * len(observed) / (12 * len(globe))
    assert f"{share:.1f}%" in HTML


def test_photographs_and_sources_are_credited():
    assert "NASA Earth Observatory" in HTML and "NOAA Ocean Exploration" in HTML
    for doi in ("10.25921/648f-fv35", "10.22033/ESGF/CMIP6.5195", "10.1029/2020GB006788", "10.5194/bg-21-2159-2024"):
        assert doi in HTML
    assert "Azam Khan" in HTML and "McKinley" in HTML
