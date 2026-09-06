# Join Page Venmo Payment Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe, prefilled Venmo payment links to the join page for the `$35` Player and `$45` Social Butterfly memberships.

**Architecture:** Keep the existing static HTML and vanilla JavaScript join page. Use canonical page-local HTTPS Venmo profile URLs for the two amounts, add static anchors to the relevant copy, and update the existing success state after form submission based on the selected tier. No payment API or server change is required.

**Tech Stack:** Static HTML, CSS, vanilla JavaScript, pytest, Vercel.

## Global Constraints

- Use `https://venmo.com/u/ncoffen` as the recipient profile; the validated display name is Natalie Coffen, `@ncoffen`.
- Use `txn=pay`, `amount=35.00` or `amount=45.00`, and URL-encoded membership notes.
- Never submit, authorize, or verify a payment from the website.
- Keep the join form, membership values, availability rules, `/api/join` request, and admin payment verification unchanged.
- Put the `$35` link in the main instruction and the `$45` link only in the lower Social Butterfly option.
- Open external links with `target="_blank"` and `rel="noopener noreferrer"`.
- Write the failing test and observe the expected failure before changing production markup or script.

---

### Task 1: Define the join-page payment-link contract

**Files:**
- Create: `tests/test_join_payment_links.py`
- Read: `public/join.html`

**Interfaces:**
- Produces static tests for the exact payment URLs and visible join-page payment affordances.
- Consumes the page source directly; it makes no network calls and never submits a form.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_join_payment_links.py` with:

```python
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
```

- [ ] **Step 2: Run the focused tests and verify the correct failure**

Run:

```bash
pytest -q tests/test_join_payment_links.py
```

Expected: the new tests fail because the current join page has no Venmo payment URLs, payment labels, or tier-aware success link.

- [ ] **Step 3: Commit the red test contract**

```bash
git add tests/test_join_payment_links.py
git commit -m "test: define join page Venmo payment links"
```

### Task 2: Add the validated payment links to the join page

**Files:**
- Modify: `public/join.html:449-452, 486-499, 574-576, 593-706`

**Interfaces:**
- Static markup consumes the two canonical Venmo URL constants and exposes safe external anchors.
- The existing submit handler produces a tier-aware success-state link after the existing successful `/api/join` response.

- [ ] **Step 1: Add static Player and Social Butterfly payment anchors**

Replace the main instruction with:

```html
<p style="font-size: 0.9rem; color: var(--text-muted); margin-top: 1rem; line-height: 1.6;">
    <a href="https://venmo.com/u/ncoffen?txn=pay&amp;amount=35.00&amp;note=Net%20Worth%20Tennis%20Player%20membership" target="_blank" rel="noopener noreferrer" style="color: var(--text-white); font-weight: 600;">Pay $35 Player membership via Venmo @NCOFFEN (Natalie)</a>, then create your player profile here. If you join after the month has started, you'll be matched in the next month.
</p>
```

Extend only the Social Butterfly description with:

```html
<div class="tier-description">
    All the social events and community, with no matches assigned. <a href="https://venmo.com/u/ncoffen?txn=pay&amp;amount=45.00&amp;note=Net%20Worth%20Tennis%20Social%20Butterfly%20membership" target="_blank" rel="noopener noreferrer" style="color: var(--text-white); font-weight: 600;">Pay $45 Social Butterfly fee via Venmo</a>.
</div>
```

- [ ] **Step 2: Add canonical URLs and the success-state anchor**

Change the success copy to:

```html
<div class="venmo-info">
    <p>Please send your membership fee via <a id="success-venmo-link" href="https://venmo.com/u/ncoffen?txn=pay&amp;amount=35.00&amp;note=Net%20Worth%20Tennis%20Player%20membership" target="_blank" rel="noopener noreferrer" style="color: var(--text-white); font-weight: 600;">Venmo @NCOFFEN (Natalie)</a>.</p>
    <p style="margin-top: 1rem;"><strong>You can sign in now!</strong></p>
</div>
```

At the top of the existing script, before the form listener, add:

```js
const venmoPlayerUrl = 'https://venmo.com/u/ncoffen?txn=pay&amount=35.00&note=Net%20Worth%20Tennis%20Player%20membership';
const venmoSocialUrl = 'https://venmo.com/u/ncoffen?txn=pay&amount=45.00&note=Net%20Worth%20Tennis%20Social%20Butterfly%20membership';
const successVenmoLink = document.getElementById('success-venmo-link');
```

Inside the existing `if (data.success)` block, immediately before hiding `formSection`, add:

```js
const isSocialButterfly = membershipTier === 'social_butterfly';
successVenmoLink.href = isSocialButterfly ? venmoSocialUrl : venmoPlayerUrl;
successVenmoLink.textContent = isSocialButterfly
    ? 'Venmo @NCOFFEN (Natalie) for $45'
    : 'Venmo @NCOFFEN (Natalie) for $35';
```

- [ ] **Step 3: Run the focused tests and inspect the diff**

Run:

```bash
pytest -q tests/test_join_payment_links.py
git diff --check
```

Expected: all focused tests pass; `git diff --check` exits 0.

- [ ] **Step 4: Commit the implementation**

```bash
git add public/join.html
git commit -m "feat: add prefilled Venmo links to join page"
```

### Task 3: Verify the complete change

**Files:**
- Review: `public/join.html`
- Test: `tests/test_join_payment_links.py`, existing `tests/`

**Interfaces:**
- The static page remains compatible with the existing Vercel route and `/api/join` contract.
- External Venmo links are verified by opening them without completing a payment.

- [ ] **Step 1: Run focused and regression tests**

Run:

```bash
pytest -q tests/test_join_payment_links.py tests/test_public_navigation.py tests/test_api.py
git diff --check
```

Expected: all selected tests pass and the diff check is clean.

- [ ] **Step 2: Verify the source URLs are exact**

Run:

```bash
rg -n "venmo.com/u/ncoffen|amount=35.00|amount=45.00|success-venmo-link|Only build" public/join.html
```

Expected: both exact URLs appear, the success link exists, and no Venmo SDK or payment API is present.

- [ ] **Step 3: Perform browser verification without submitting payment**

Open `/join` at desktop and phone-sized widths. Confirm:

1. The top link reads as the `$35` Player payment action.
2. The lower Social Butterfly option contains the `$45` payment link.
3. Both links resolve to Venmo’s `@ncoffen` profile and preserve their respective amount and note query parameters.
4. The join form remains available after opening Venmo in a new tab.
5. No payment is submitted.

- [ ] **Step 4: Deployment gate**

Do not send mail, submit payment, or change the `/api/join` contract. Production deployment is a separate explicit action after source and browser verification.
