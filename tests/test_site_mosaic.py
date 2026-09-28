"""Paid presentation layer must stay separate from public research data."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def test_mosaic_is_private_lazy_and_motion_safe():
    ignored = (ROOT / ".gitignore").read_text()
    wrapper = (SITE / "src/MosaicBackdrop.jsx").read_text(encoding="utf-8")
    config = (ROOT / "vite.config.js").read_text()
    assert "site/licensed/" in ignored
    assert "lazy(()=>import('@licensed/mosaic-waves'))" in wrapper
    for guard in ("IntersectionObserver", "prefers-reduced-motion", "document.hidden", "saveData", "paused={paused}"):
        assert guard in wrapper
    assert "OMIT_LICENSED_MOSAIC" in config and "StaticMosaic.jsx" in config
    assert "fetch(" not in wrapper


def test_primary_and_stress_results_remain_distinct():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    js = (SITE / "app.js").read_text(encoding="utf-8")
    assert 'data-paired-protocol="hidden" aria-pressed="true"' in html
    assert 'data-paired-protocol="block" aria-pressed="false"' in html
    assert 'pairedProtocol:"hidden"' in js
    assert 'state.data.estimands["area|both60|hidden"].metrics.mae.relative_pct' in js
    assert "Each panel has its own vertical scale" in html
    assert "not independent ESM replicates" in html


def test_only_application_build_is_published():
    publisher = (ROOT / "scripts/publish_site.mjs").read_text()
    workflow = (ROOT / ".github/workflows/deploy-pages.yml").read_text()
    assert "licensed" in publisher and "Source files must not enter" in publisher
    assert "commit-tree" in publisher and "--force" not in publisher
    assert "ref: site-build" in workflow
    assert "npm run build" not in workflow
