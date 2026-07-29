from pathlib import Path


PUBLIC_PAGES = (
    "index.html",
    "rules.html",
    "profiles.html",
    "profile.html",
    "privacy.html",
    "support.html",
)

ROOT = Path(__file__).parents[1]


def page(name: str) -> str:
    return (ROOT / "public" / name).read_text(encoding="utf-8")


def test_public_pages_load_shared_navigation_assets():
    for name in PUBLIC_PAGES:
        html = page(name)
        assert "/css/site-nav.css" in html, name
        assert "/js/site-nav.js" in html, name
        assert "data-site-nav" in html, name


def test_public_pages_use_canonical_public_destinations():
    required = (
        'href="/#how-it-works"',
        'href="/#courts"',
        'href="/rules"',
    )
    for name in PUBLIC_PAGES:
        html = page(name)
        for destination in required:
            assert destination in html, f"{name}: {destination}"


def test_rules_page_marks_game_play_as_current():
    html = page("rules.html")
    assert 'data-page="rules"' in html
    assert "Game Play &amp; Scoring" in html or "Game Play & Scoring" in html


def test_gated_navigation_is_marked_for_shared_auth_behavior():
    for name in PUBLIC_PAGES:
        html = page(name)
        assert 'data-members-only="true"' in html, name
        assert "data-auth-action" in html, name
