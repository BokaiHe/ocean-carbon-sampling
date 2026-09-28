"""The final type layer covers titles, native controls and chart labels alike."""
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "site"


def test_single_sans_serif_family_is_the_final_stylesheet():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    css = (SITE / "typography.css").read_text(encoding="utf-8")
    assert html.index('href="typography.css"') > html.index('href="story.css"')
    assert "--site-font: Arial, sans-serif" in css
    assert "body *" in css
    assert "font-family: var(--site-font) !important" in css
    assert "font-style: normal !important" in css
