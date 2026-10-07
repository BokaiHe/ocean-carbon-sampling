"""Presentation changes do not claim to close the scientific domain audit."""
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"


def test_contribution_and_primary_result_precede_context():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert html.index('id="evidence-story"') < html.index('id="background"')
    assert "My contribution:" in html
    assert '<details class="optional-explorer" id="observations-detail">' in html
    assert 'id="observation-month"' in html and 'id="globe-layer"' in html


def test_domain_status_is_visible_and_cannot_be_mistaken_for_a_completed_audit():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert html.index('id="result-domain-status"') < html.index('id="paired-evidence"')
    assert "effect on error magnitudes and rankings has not been quantified" in html
    assert "No corrected-mask rerun" in html
    assert "Twelve positive variants do not test this missing control" in html
    for panel in ("error-map", "sampling"):
        body = html.split(f'id="{panel}"', 1)[1].split('</section>', 1)[0]
        assert 'href="#ocean-domain-audit"' in body


def test_chart_legibility_and_tab_scroll_are_explicit():
    js = (SITE / "app.js").read_text(encoding="utf-8")
    story = (SITE / "src/ResultsStory.jsx").read_text(encoding="utf-8")
    assert 'Training + testing <60°N' in js
    assert 'Testing only <60°N' in js
    assert '"sweep-chart",300' in js
    assert 'scrollRequested' in story and "scrollIntoView({behavior:'instant',block:'start'})" in story
    assert 'focus({preventScroll:true})' in story
