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
    assert "Grey water means no displayed observation—not zero CO₂" in html


def test_error_palette_distinguishes_null_from_zero_and_uses_shared_legend_stops():
    js = (SITE / "globe.js").read_text(encoding="utf-8")
    assert "v===null?noDataColour:palettes" in js
    assert "colourStops[model.layer].join(',')" in js
    assert "Object.keys(colourStops)" in js
    assert "not zero error" in js
    assert "Grey background is not a fine-grid coverage mask" in js
