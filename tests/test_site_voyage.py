"""The real-voyage context stays source-faithful and separate from model scores."""

import csv
import hashlib
import io
import json
import re
import runpy
from datetime import datetime
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def test_story_introduces_problem_and_method_before_results():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    sections = re.findall(r'<section\b[^>]*id="([^"]+)"', html)
    expected = [
        "background",
        "voyage",
        "workflow",
        "sampling",
        "paired-evidence",
        "results",
        "error-map",
        "sample-count",
        "technical",
    ]
    assert [sections.index(name) for name in expected] == sorted(
        sections.index(name) for name in expected
    )
    assert sections.count("workflow") == 1
    assert "not exact ship positions" in html
    assert "not used as the OSSE truth" in html
    assert "not the historical-density sampling mask" in html
    assert "SOCAT data-use statement" in html
    assert re.search(r"[\u3400-\u9fff]", html) is None
    ids = re.findall(r'\bid="([^"]+)"', html)
    assert len(ids) == len(set(ids))


def test_voyage_positions_match_every_original_record():
    raw = (SITE / "data/PS103-track.tab").read_bytes()
    assert (
        hashlib.sha256(raw).hexdigest()
        == "eac294ca192832a1cc7f5092759e9fa21661e11585e63efc1415eab2db3e9049"
    )
    records = list(
        csv.DictReader(
            io.StringIO(raw.decode("utf-8").split("*/", 1)[1].strip()), delimiter="\t"
        )
    )
    data = json.loads((SITE / "data/voyage-track.json").read_text(encoding="utf-8"))
    assert data["points"] == [
        [r["Date/Time"], float(r["Longitude"]), float(r["Latitude"])] for r in records
    ]
    assert len(data["points"]) == data["metadata"]["count"] == 6997
    times = [datetime.fromisoformat(p[0]) for p in data["points"]]
    assert all(b > a for a, b in pairwise(times))
    assert data["break_before"] == [
        i
        for i in range(1, len(times))
        if (times[i] - times[i - 1]).total_seconds() > 1800
    ]
    assert data["metadata"]["license"] == "CC-BY-3.0"


def test_voyage_export_is_reproducible(tmp_path):
    module = runpy.run_path(str(ROOT / "scripts/export_site_voyage.py"))
    output = tmp_path / "voyage.json"
    module["export"](SITE / "data/PS103-track.tab", output)
    assert output.read_bytes() == (SITE / "data/voyage-track.json").read_bytes()


def test_voyage_is_independent_and_accessible():
    js = (SITE / "voyage.js").read_text(encoding="utf-8")
    assert "data/globe-data.json" not in js
    assert "data/site-data.json" not in js
    assert "prefers-reduced-motion" in js
    assert "visibilitychange" in js
    assert "IntersectionObserver" in js
    assert "pointerdown" not in js
    assert "LOOP_MS = 32000" in js
    assert "original navigation table and source link below remain available" in js
    assert "setInterval" not in js


def test_real_ship_introduction_is_live_and_distinct_from_observations():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    for name in ("real-voyage", "voyage-explorer", "voyage-globe"):
        assert f'id="{name}"' in html
    assert 'src="voyage.js' in html
    intro = html.split('id="background"', 1)[1].split('</section>', 1)[0]
    assert 'id="real-voyage"' in intro
    assert 'id="voyage-time"' not in html
    assert 'id="voyage-locate"' not in html
    assert '32 seconds' in intro
    assert 'noaa-ctd-launch.jpg' in html
    assert 'This photo is not from the voyage below' in html
    assert 'a position is not necessarily a CO₂ sample' in html
    assert "'voyage.js'" in (ROOT / "vite.config.js").read_text(encoding="utf-8")
