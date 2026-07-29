from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_support_page_exposes_call_umpire_action_above_the_faq():
    html = (ROOT / "public" / "support.html").read_text(encoding="utf-8")

    assert 'data-call-umpire' in html
    assert 'type="button"' in html
    assert "Call the umpire" in html
    assert html.index("data-call-umpire") < html.index("Frequently Asked Questions")


def test_report_issue_script_wires_inline_call_umpire_triggers_to_existing_modal():
    script = (ROOT / "public" / "js" / "report-issue.js").read_text(encoding="utf-8")

    assert "data-call-umpire" in script
    assert "openModal" in script
