from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_support_page_is_the_faq_destination_without_a_second_umpire_callout():
    html = (ROOT / "public" / "support.html").read_text(encoding="utf-8")

    assert 'data-call-umpire' not in html
    assert "Frequently Asked Questions" in html


def test_report_issue_modal_links_to_support_and_is_mobile_friendly():
    script = (ROOT / "public" / "js" / "report-issue.js").read_text(encoding="utf-8")

    assert 'href=\"/support\"' in script
    assert "Visit Support / FAQ" in script
    assert "openModal" in script
    assert "issue-message').focus" not in script
    assert "100dvh" in script
    assert "overflow-y: auto" in script
