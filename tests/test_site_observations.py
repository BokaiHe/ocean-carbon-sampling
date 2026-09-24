"""Observed fCO2 is distinct from the frozen model experiment."""

import json
import runpy
from pathlib import Path

import numpy as np
import pytest

from ocean_carbon_sampling.data import read_socat_monthly

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def test_observation_export_keeps_quantity_scope_and_extremes():
    data = json.loads((SITE / "data/observed-co2.json").read_text(encoding="utf-8"))
    assert data["metadata"]["units"] == "µatm"
    assert data["metadata"]["field"] == "FCO2_AVE_WEIGHTED_YEAR"
    assert data["metadata"]["default_year"] == 2014
    assert data["metadata"]["colour_domain"] == [200, 600]
    assert "not a complete annual mean" in data["metadata"]["all_months"]
    for year, count in [(2005, 11961), (2010, 14664), (2014, 16348)]:
        rows = np.asarray(data["years"][str(year)])
        assert len(rows) == count
        assert set(rows[:, 0]) == set(range(1, 13))
        assert np.isfinite(rows).all()
        assert ((rows[:, 1] >= -180) & (rows[:, 1] <= 180)).all()
        assert ((rows[:, 2] >= -90) & (rows[:, 2] <= 90)).all()
        assert (rows[:, 4] > 0).all()
        assert rows[:, 3].min() < 200 and rows[:, 3].max() > 600
    assert max(r[3] for r in data["years"]["2010"]) == 4310.25
    assert len({(r[1], r[2]) for r in data["years"]["2014"]}) == 7784


def test_observation_values_match_local_socat_when_available():
    source = ROOT / "data/raw/socat/SOCATv2025_tracks_gridded_monthly.csv"
    if not source.exists():
        pytest.skip("Raw SOCAT CSV stays local; export contract is tested separately")
    data = json.loads((SITE / "data/observed-co2.json").read_text(encoding="utf-8"))
    frame = read_socat_monthly(source)
    for year, rows in data["years"].items():
        part = frame.loc[frame.date.dt.year == int(year)].sort_values(
            ["date", "latitude", "longitude"]
        )
        part = part.loc[np.isfinite(part.fco2) & (part.fco2_count > 0)]
        expected = np.column_stack(
            [
                part.date.dt.month,
                part.longitude,
                part.latitude,
                part.fco2,
                part.fco2_count,
                part.cruise_count,
            ]
        )
        np.testing.assert_array_equal(np.asarray(rows), expected)


def test_observation_export_filters_missing_not_high_values(tmp_path):
    source = tmp_path / "socat.csv"
    source.write_text(
        "metadata\nDATE, LAT, LON, COUNT_NCRUISE_YEAR, FCO2_COUNT_NOBS_YEAR, FCO2_AVE_WEIGHTED_YEAR, SST_AVE_WEIGHTED_YEAR, SALINITY_AVE_WEIGHTED_YEAR\n"
        "2014-01-16,10.5,20.5,1,2,4310.25,20,35\n"
        "2014-02-16,10.5,20.5,1,2,-1e34,20,35\n"
        "2014-03-16,10.5,20.5,1,0,350,20,35\n",
        encoding="utf-8",
    )
    module = runpy.run_path(str(ROOT / "scripts/export_site_observations.py"))
    data = module["export"](source, tmp_path / "observed.json")
    assert data["years"]["2014"] == [[1, 20.5, 10.5, 4310.25, 2, 1]]
    assert data["metadata"]["excluded_missing_or_unobserved_rows"] == 2


def test_observation_date_controls_are_above_globe_with_visible_month_buttons():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    js = (SITE / "observations.js").read_text(encoding="utf-8")
    view = html.split('class="observation-view"', 1)[1].split("</section>", 1)[0]
    assert view.index('id="observation-year"') < view.index('id="observation-globe"')
    assert view.index('id="observation-month"') < view.index('id="observation-globe"')
    assert '<select id="observation-month"' not in html
    assert 'class="observation-month-buttons" role="group"' in html
    assert "button.dataset.observationMonth" in js
    assert "aria-pressed" in js
    assert "months.slice(1)" in js
    assert "button.textContent=String(i)" in js
    assert 'id="observation-all-months"' in html


def test_observation_globe_has_no_routes_or_model_data_dependency():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    js = (SITE / "observations.js").read_text(encoding="utf-8")
    assert 'src="voyage.js' not in html
    assert "Follow a real ship" not in html
    assert "not a complete annual mean" in html
    assert "not dissolved-carbon concentration" in html
    assert "per-cruise-weighted" in html
    assert "globe-data.json" not in js and "site-data.json" not in js
    assert "MultiLineString" not in js and "LineString" not in js
    assert "pointercancel" in js and "ArrowLeft" in js
    assert js.index("path(land);ctx.fillStyle='#ffffff'") > js.index(
        "for(let i=0;i<cells.length;i++)"
    )
