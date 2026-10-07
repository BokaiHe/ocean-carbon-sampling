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


def test_headline_is_explicitly_a_conditional_benchmark():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    js = (SITE / "app.js").read_text(encoding="utf-8")
    headline = html.split('id="paired-evidence"', 1)[1].split('</aside>', 1)[0]
    assert "Current benchmark only" in headline
    assert "no corrected-mask rerun has verified this magnitude or ranking" in headline
    assert "higher MAE than random · current benchmark" in js


def test_desktop_chart_space_and_mobile_photo_alignment():
    css = (SITE / "portfolio.css").read_text(encoding="utf-8")
    assert "@media(min-width:1001px) and (max-width:1399px)" in css
    assert ".finding-tabs { display:grid; grid-template-columns:repeat(4,minmax(0,1fr))" in css
    mobile = css.split("@media(max-width:760px)", 1)[1]
    assert ".field-intro .field-photo { width:100%; max-width:none; }" in mobile


def test_hero_credit_uses_svg_not_a_font_arrow():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    hero = (SITE / "src/Hero.jsx").read_text(encoding="utf-8")
    assert "Course foundation &amp; credits ↗" not in html + hero
    assert "Course foundation &amp; credits <svg" in html
