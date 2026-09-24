"""The cinematic entrance is presentation-only and progressively enhanced."""
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"


def test_hero_keeps_local_video_and_discloses_context_footage():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert 'href="hero.css?' in html
    assert 'src="/src/main.jsx"' in html
    assert 'id="hero-motion"' in html
    assert "Context imagery, not model output." in html
    assert 'preload="none"' in html
    assert 'loop=""' in html
    assert 'data-src="assets/context/ocean-waves.mp4"' in html
    assert (SITE / "assets/context/ocean-waves.mp4").stat().st_size < 5_000_000
    assert (SITE / "assets/context/ocean-waves-poster.jpg").is_file()
    assert (SITE / "assets/context/ocean-waves-source.md").is_file()


def test_hero_has_reduced_motion_pause_and_no_data_dependency():
    js = (SITE / "src/useHeroVideo.js").read_text()
    component = (SITE / "src/Hero.jsx").read_text(encoding="utf-8")
    css = (SITE / "hero.css").read_text()
    assert "prefers-reduced-motion: reduce" in js
    assert "document.hidden" in js
    assert "IntersectionObserver" in js
    assert "aria-pressed" in component
    assert "video.play()" in js
    assert "video.pause()" in js
    assert "saveData" in js
    assert "ocean-drift" not in css
    assert "prefers-reduced-motion:reduce" in css
    assert "backdrop-filter:blur" in css
    assert "fetch(" not in js


def test_react_hero_build_keeps_research_assets_and_pages_subpath():
    root = SITE.parent
    import json
    package = json.loads((root / "package.json").read_text())
    config = (root / "vite.config.js").read_text()
    renderer = (root / "scripts/render_hero.jsx").read_text()
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert "react" in package["dependencies"]
    assert "vite" in package["devDependencies"]
    assert "render:hero" in package["scripts"]["build"]
    assert "hydrateRoot" in (SITE / "src/main.jsx").read_text()
    assert "renderToString" in renderer
    assert "vite-ignore" in renderer  # Preserve the poster URL through hydration.
    assert "base:'./'" in config
    for name in ("assets", "data", "vendor", "app.js", "globe.js", "observations.js"):
        assert f"'{name}'" in config
    assert 'id="hero-root"' in html
    assert 'href="mailto:bh2954@columbia.edu"' in html
    assert "path: dist" in (root / ".github/workflows/deploy-pages.yml").read_text()
