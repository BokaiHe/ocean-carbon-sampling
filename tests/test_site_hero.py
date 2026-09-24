"""The cinematic entrance is presentation-only and progressively enhanced."""
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"


def test_hero_keeps_local_assets_and_discloses_animated_photo():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert 'href="hero.css?' in html
    assert 'src="hero.js?' in html
    assert 'id="hero-motion"' in html
    assert "Animated satellite photograph. Context imagery, not model output." in html
    assert "assets/context/nasa-celtic-sea-phytoplankton.jpg" in (SITE / "hero.css").read_text()


def test_hero_has_reduced_motion_pause_and_no_data_dependency():
    js = (SITE / "hero.js").read_text()
    css = (SITE / "hero.css").read_text()
    assert "prefers-reduced-motion: reduce" in js
    assert "document.hidden" in js
    assert "IntersectionObserver" in js
    assert "aria-pressed" in js
    assert "animation-play-state:paused" in css
    assert "prefers-reduced-motion:reduce" in css
    assert "backdrop-filter:blur" in css
    assert "fetch(" not in js
