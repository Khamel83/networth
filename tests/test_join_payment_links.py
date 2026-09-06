from pathlib import Path


ROOT = Path(__file__).parents[1]
JOIN_PAGE = ROOT / "public" / "join.html"

PLAYER_URL = (
    "https://venmo.com/u/ncoffen?txn=pay&amount=35.00&"
    "note=Net%20Worth%20Tennis%20Player%20membership"
)
SOCIAL_URL = (
    "https://venmo.com/u/ncoffen?txn=pay&amount=45.00&"
    "note=Net%20Worth%20Tennis%20Social%20Butterfly%20membership"
)


def join_page() -> str:
    return JOIN_PAGE.read_text(encoding="utf-8")


def test_join_page_links_player_fee_to_prefilled_venmo_payment():
    html = join_page()

    assert PLAYER_URL in html
    assert "Pay $35" in html
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html


def test_join_page_links_social_butterfly_fee_to_prefilled_venmo_payment():
    html = join_page()

    assert SOCIAL_URL in html
    assert "Pay $45" in html


def test_join_success_state_has_a_tier_aware_venmo_link():
    html = join_page()

    assert 'id="success-venmo-link"' in html
    assert "venmoPlayerUrl" in html
    assert "venmoSocialUrl" in html
    assert "membershipTier === 'social_butterfly'" in html
