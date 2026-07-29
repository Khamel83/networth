from pathlib import Path


PROFILES_PAGE = Path(__file__).parents[1] / "public" / "profiles.html"


def test_players_page_has_an_explicit_preview_mode_without_changing_members_only_default():
    html = PROFILES_PAGE.read_text()

    assert 'preview=1' in html
    assert 'data-preview-mode' in html
    assert 'data-preview-sample' in html
    assert "isPreviewMode" in html
    assert "if (!isPreviewMode && !isLoggedIn())" in html
    assert 'data-members-only="true"' in html


def test_players_preview_is_clearly_labeled_as_sample_data():
    html = PROFILES_PAGE.read_text()

    assert "Sample preview data" in html
    assert "Not the live league roster" in html
