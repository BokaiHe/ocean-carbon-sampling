"""The cinematic entrance is presentation-only and progressively enhanced."""
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"


def test_hero_keeps_local_video_and_discloses_context_footage():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert 'href="hero.css?' in html
    assert 'src="hero.js?' in html
    assert 'id="hero-motion"' in html
    assert "Real ocean footage. Context imagery, not model output." in html
    assert 'muted loop playsinline preload="none"' in html
    assert 'data-src="assets/context/ocean-waves.mp4"' in html
    assert (SITE / "assets/context/ocean-waves.mp4").stat().st_size < 5_000_000
    assert (SITE / "assets/context/ocean-waves-poster.jpg").is_file()
    assert (SITE / "assets/context/ocean-waves-source.md").is_file()


def test_hero_has_reduced_motion_pause_and_no_data_dependency():
    js = (SITE / "hero.js").read_text()
    css = (SITE / "hero.css").read_text()
    assert "prefers-reduced-motion: reduce" in js
    assert "document.hidden" in js
    assert "IntersectionObserver" in js
    assert "aria-pressed" in js
    assert "video.play()" in js
    assert "video.pause()" in js
    assert "saveData" in js
    assert "ocean-drift" not in css
    assert "prefers-reduced-motion:reduce" in css
    assert "backdrop-filter:blur" in css
    assert "fetch(" not in js
