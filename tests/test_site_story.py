"""The chapter presentation must preserve scientific scope and source access."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def test_story_preserves_four_static_panels_and_progressive_enhancement():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    story = (SITE / "src/ResultsStory.jsx").read_text(encoding="utf-8")
    for name in ("paired-evidence", "results", "error-map", "sample-count"):
        assert f'class="evidence-panel" id="{name}"' in html
        assert f"id:'{name}'" in story
    assert 'id="results-navigation"' in html
    assert 'role="tablist"' in story and 'role="tab"' in story
    assert "aria-controls={chapter.id}" in story
    assert "ArrowDown" in story and "Home:0" in story and "End:3" in story
    assert "hashchange" in story and "popstate" in story
    assert "setInterval" not in story
    assert "research:panelchange" in story
    assert "panel.hidden=false" in story
    assert "not 12 independent tests" in html
    assert "not the primary scope" in html
    assert "reversal threshold cannot be transferred" in html
    assert 'id="paired-table"' in html and 'id="sweep-table"' in html
    assert not re.search(r'class="evidence-panel"[^>]*\bhidden\b', html)


def test_hidden_charts_redraw_on_selection_and_primary_and_stress_labels_match():
    js = (SITE / "app.js").read_text(encoding="utf-8")
    css = (SITE / "story.css").read_text(encoding="utf-8")
    assert 'window.addEventListener("research:panelchange"' in js
    assert 'getClientRects().length' in js
    assert 'primary?primaryPercent:state.data.estimands["area|both60|block"]' in js
    assert 'primary?"primary test":"stress test"' in js
    assert 'prefers-reduced-motion:reduce' in css
    assert '.evidence-panel[hidden]' in css


def test_footer_retains_research_boundary_and_contact():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    footer = html.split('<footer class="research-footer"', 1)[1]
    assert 'mailto:bh2954@columbia.edu' in footer
    assert 'Columbia EEE' in footer
    assert 'does not identify optimal routes or marginal gains' in footer
    assert 'data/site-data.json' in footer and 'data/chart-data.json' in footer
    assert 'https://github.com/BokaiHe/ocean-carbon-sampling' in footer
    assert 'class="next-question"' not in html
