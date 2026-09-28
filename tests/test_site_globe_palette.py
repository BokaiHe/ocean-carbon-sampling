"""Palette changes are display-only; zero error must not become missing data."""
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"


def test_both_globes_use_neutral_ocean_and_white_land():
    for name in ("globe.js", "observations.js"):
        js = (SITE / name).read_text(encoding="utf-8")
        assert "const noDataColour='#9ca3af'" in js
        assert "ctx.fillStyle=noDataColour" in js
        assert "ctx.fillStyle='#ffffff'" in js
        assert "ctx.strokeStyle='#000000'" in js
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert "Grey background is not a fine-grid coverage mask" in html


def test_experimental_globe_restores_three_views_without_losing_missing_values():
    js = (SITE / "globe.js").read_text(encoding="utf-8")
    assert "colourStops[model.layer].join(',')" in js
    assert "Object.keys(colourStops)" in js
    assert "Grey background is not a fine-grid coverage mask" in js
    assert "data.fields" in js
    assert "model.layer" in js
    assert "v===null?noDataColour" in js
    html = (SITE / "index.html").read_text(encoding="utf-8")
    for layer in ("sampling", "mae", "delta"):
        assert f'value="{layer}"' in html
    assert "count===0?noDataColour" in js
