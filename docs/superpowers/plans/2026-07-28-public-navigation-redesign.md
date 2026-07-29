# Public Navigation and Game Play & Scoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Net Worth's public navigation consistent and mobile-first, improve the separate `/rules` page, and produce a shareable Vercel branch preview without changing production or league behavior.

**Architecture:** Keep the existing static HTML/Vercel/Python-serverless architecture. Add a small shared navigation module and navigation stylesheet that enhance a semantic navigation shell on each public page; keep page content and existing visual styles local. Preserve relative `/api/*` calls so a Vercel preview can use the existing preview/live backend configuration without hardcoding a new endpoint.

**Tech Stack:** Static HTML, CSS, vanilla JavaScript, Vercel, Python serverless functions, Supabase-backed existing APIs, pytest.

## Global Constraints

- Work only on `codex/redesign`; do not modify `master` or deploy production.
- Impeccable is inspiration and a review lens only; it is not a runtime dependency or replacement architecture.
- Do not change APIs, database schema, authentication flows, ranking logic, match scoring, forfeits, membership rules, or player data.
- Preserve the existing gradient, typography, logo, glass-card treatment, page composition, and brand personality.
- Keep Players and Rankings hidden for logged-out visitors and visible only with both existing player and token session signals.
- Keep `/rules` as a separate page and make cross-page section links use `/#how-it-works` and `/#courts`.
- Make only small copy edits that improve clarity or punctuation without changing substantive rules.
- Target approximately 320–430px phone widths first, with desktop and tablet layouts preserved.
- Do not add secrets, hardcode production credentials, or alter environment configuration.
- A preview must be openly reachable by link; production deployment remains a separate explicit gate.

---

### Task 1: Add navigation contract tests before implementation

**Files:**
- Create: `tests/test_public_navigation.py`
- Read: `public/index.html`, `public/rules.html`, `public/profiles.html`, `public/profile.html`, `public/privacy.html`, `public/support.html`

**Interfaces:**
- Produces a static test contract for the shared navigation migration.
- Consumes the public page files directly; it does not make network calls or inspect credentials.

- [ ] **Step 1: Write the failing static contract tests**

Create a test module with this concrete contract:

```python
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
        assert '/css/site-nav.css' in html, name
        assert '/js/site-nav.js' in html, name
        assert 'data-site-nav' in html, name


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
    assert 'Game Play &amp; Scoring' in html or 'Game Play & Scoring' in html


def test_gated_navigation_is_marked_for_shared_auth_behavior():
    for name in PUBLIC_PAGES:
        html = page(name)
        assert 'data-members-only="true"' in html, name
        assert 'data-auth-action' in html, name
```

- [ ] **Step 2: Run the new tests and verify they fail for the current markup**

Run:

```bash
pytest -q tests/test_public_navigation.py
```

Expected: failures because the current pages do not all load shared navigation assets or expose the shared data contract.

- [ ] **Step 3: Commit the red test contract**

```bash
git add tests/test_public_navigation.py
git commit -m "test: define public navigation contract"
```

### Task 2: Implement the shared navigation behavior and styles

**Files:**
- Create: `public/js/site-nav.js`
- Create: `public/css/site-nav.css`

**Interfaces:**
- `public/js/site-nav.js` consumes `header[data-site-nav]`, `nav[data-site-menu]`, `button[data-menu-toggle]`, `a[data-members-only="true"]`, and `body[data-page]`.
- The module produces auth-aware visibility, `aria-current="page"`, mobile-menu state, and a safe `window.NetWorthNav` object with `closeMenu()` for page-local links if needed.

- [ ] **Step 1: Add the shared navigation configuration and session reader**

Implement the canonical link configuration in `public/js/site-nav.js` with these destinations and labels:

```js
const NAV_LINKS = [
  { key: 'how-it-works', label: 'How It Works', href: '/#how-it-works' },
  { key: 'courts', label: 'Courts', href: '/#courts' },
  { key: 'rules', label: 'Game Play & Scoring', href: '/rules' },
  { key: 'players', label: 'Players', href: '/profiles', membersOnly: true },
  { key: 'rankings', label: 'Rankings', href: '/#rankings', membersOnly: true },
];

function readSession() {
  let player = {};
  try {
    player = JSON.parse(localStorage.getItem('networth_player') || '{}');
  } catch {
    player = {};
  }
  const token = localStorage.getItem('networth_token') || '';
  return { loggedIn: Boolean(player.email && token) };
}
```

The module must treat malformed JSON or a missing token as logged out and must not make network calls.

- [ ] **Step 2: Add active-state and gated-link behavior**

Use `document.body.dataset.page` to mark the current page. The `rules`, `players`, `profile`, and `rankings` contexts must set `aria-current="page"` only on their corresponding navigation link. Members-only anchors must be hidden while logged out and shown when both session signals exist.

Use CSS-hidden state rather than removing elements so the menu remains keyboard-safe and predictable:

```js
function setVisibility(element, visible) {
  element.hidden = !visible;
  element.setAttribute('aria-hidden', String(!visible));
}
```

- [ ] **Step 3: Add accessible mobile-menu behavior**

The module must:

1. Toggle `aria-expanded` on `button[data-menu-toggle]`.
2. Toggle an `is-open` class on `[data-site-menu]`.
3. Close on Escape, outside pointerdown, and navigation-link activation.
4. Return focus to the menu button when closing with Escape.
5. Avoid changing body scroll behavior unless the current page needs it.

Use this event shape:

```js
function closeMenu({ restoreFocus = false } = {}) {
  menu.classList.remove('is-open');
  toggle.setAttribute('aria-expanded', 'false');
  if (restoreFocus) toggle.focus();
}

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && menu.classList.contains('is-open')) {
    closeMenu({ restoreFocus: true });
  }
});
```

Expose only the close helper needed by existing inline page code:

```js
window.NetWorthNav = { closeMenu };
```

- [ ] **Step 4: Add navigation-only CSS without restyling page content**

`public/css/site-nav.css` must provide:

- Shared header/menu layout that respects the current color variables when present.
- A desktop layout that keeps the existing centered links and auth controls visually familiar.
- A phone breakpoint at `max-width: 768px` that hides the full menu until opened and exposes a comfortable menu button.
- Minimum approximately 44px interactive height for menu controls and auth actions.
- Visible `:focus-visible` outline using the existing white/pink palette.
- `prefers-reduced-motion: reduce` behavior that removes menu transitions.
- No new icon library and no model-authored decorative SVG artwork.

- [ ] **Step 5: Run the navigation tests and commit the shared layer**

Run:

```bash
pytest -q tests/test_public_navigation.py
git diff --check
```

Expected: the test suite still fails until the page shells are migrated in Task 3, but the new files must be syntactically valid and the diff check must pass.

Commit:

```bash
git add public/js/site-nav.js public/css/site-nav.css
git commit -m "feat: add shared responsive navigation"
```

### Task 3: Migrate public pages to the shared navigation shell

**Files:**
- Modify: `public/index.html`
- Modify: `public/rules.html`
- Modify: `public/profiles.html`
- Modify: `public/profile.html`
- Modify: `public/privacy.html`
- Modify: `public/support.html`

**Interfaces:**
- Each page includes `/css/site-nav.css` and `/js/site-nav.js`.
- Each page has `<body data-page="...">` and a semantic `<header data-site-nav>` containing the shared data attributes.
- Existing page-specific content, API calls, footer copy, Instagram link, hero CTAs, and profile back links remain intact.

- [ ] **Step 1: Replace duplicated public headers with the shared semantic shell**

Use this markup pattern, adapting only the page-context value and preserving the current page's logo/auth placement:

```html
<header class="site-header" data-site-nav>
    <a href="/" class="logo" aria-label="Net Worth home">net worth</a>
    <button
        class="site-menu-toggle"
        type="button"
        data-menu-toggle
        aria-controls="site-menu"
        aria-expanded="false"
        aria-label="Open navigation"
    >
        <span aria-hidden="true">☰</span>
    </button>
    <nav id="site-menu" class="site-menu" data-site-menu aria-label="Primary navigation">
        <a href="/#how-it-works" class="nav-link" data-nav-key="how-it-works">How It Works</a>
        <a href="/#courts" class="nav-link" data-nav-key="courts">Courts</a>
        <a href="/rules" class="nav-link" data-nav-key="rules">Game Play &amp; Scoring</a>
        <a href="/profiles" class="nav-link" data-nav-key="players" data-members-only="true" hidden>Players</a>
        <a href="/#rankings" class="nav-link" data-nav-key="rankings" data-members-only="true" hidden>Rankings</a>
    </nav>
    <div class="nav-auth" data-auth-actions>
        <a href="/login" class="btn" data-auth-action="signin">Sign In</a>
        <a href="/join" class="btn btn-primary" data-auth-action="join">Join Now</a>
        <a href="/dashboard" class="btn" data-auth-action="profile" hidden>My Profile</a>
        <a href="#" class="btn btn-primary" data-auth-action="signout" hidden>Sign Out</a>
    </div>
</header>
```

On the home page, retain the existing Instagram link in the auth area and the current hero buttons. Do not expose Players or Rankings to logged-out visitors in the initial visible state.

- [ ] **Step 2: Remove per-page navigation auth mutations**

Delete or bypass the duplicated inline blocks that separately rewrite `.nav-center`, `.nav-links`, `.nav-auth`, `nav-dashboard`, `nav-signin`, or `nav-signout` on the migrated pages. Preserve unrelated auth/session code used by the dashboard, profile data, and API calls.

- [ ] **Step 3: Normalize page context and cross-page destinations**

Set these body contexts:

```html
<body data-page="home">
<body data-page="rules">
<body data-page="players">
<body data-page="profile">
<body data-page="privacy">
<body data-page="support">
```

Ensure every migrated page has `/#how-it-works`, `/#courts`, and `/rules` in the shared navigation, and that the active Game Play & Scoring link is present on `/rules`.

- [ ] **Step 4: Run the static navigation contract and existing tests**

Run:

```bash
pytest -q tests/test_public_navigation.py tests/test_api.py tests/test_pairings.py
git diff --check
```

Expected: all selected tests pass; no API or pairing test behavior changes.

- [ ] **Step 5: Commit the public-page migration**

```bash
git add public/index.html public/rules.html public/profiles.html public/profile.html public/privacy.html public/support.html
git commit -m "feat: standardize public page navigation"
```

### Task 4: Apply narrowly scoped Game Play & Scoring copy cleanup

**Files:**
- Modify: `public/rules.html`
- Review only: `content/rules.json`

**Interfaces:**
- `/rules` remains a separate route and retains all current sections, examples, and substantive values.
- No scoring, forfeiture, ranking, membership, or API behavior changes.

- [ ] **Step 1: Update only readability and punctuation**

Make these non-substantive copy changes in the rendered page:

- Use the consistent title `Game Play & Scoring`.
- Use typographic score separators: `6–2`, `4–6`, `6–5`, `7–5`, and `6–6`.
- Replace hyphen-as-punctuation in the set example with an em dash where it improves readability.
- Preserve the existing terminology “points” in the forfeiture section unless the source rule itself is changed in a later, separately approved task.

- [ ] **Step 2: Confirm the source content does not contradict the rendered page**

Compare the rendered rules against `content/rules.json` and record no semantic changes. Do not rewrite `content/rules.json` merely to make the files look identical if it is not the active renderer.

- [ ] **Step 3: Run tests and commit the copy cleanup**

Run:

```bash
pytest -q
git diff --check
```

Commit:

```bash
git add public/rules.html
git commit -m "copy: clarify game play and scoring page"
```

### Task 5: Validate the branch and create a shareable Vercel preview

**Files:**
- Modify only if required by the existing preview workflow: no application files expected.
- Do not create `.openai/hosting.json`; Sites is not the selected deployment path for this Vercel/Python project.

**Interfaces:**
- The preview must resolve at a normal public HTTPS URL without requiring the reviewer to be logged into Codex, GitHub, or Vercel.
- The preview must use the existing relative `/api/*` calls and only the already-configured Vercel Preview environment settings.
- No production alias, `vercel --prod`, `master` push, database migration, or secret change is allowed.

- [ ] **Step 1: Run the complete local verification**

Run:

```bash
pytest -q
git diff --check
git status --short --branch
```

Expected: all tests pass, the diff check is clean, and the only branch is `codex/redesign` with intended commits.

- [ ] **Step 2: Inspect preview configuration without printing secrets**

Check only names and linkage:

```bash
git remote -v
vercel project ls 2>/dev/null || true
vercel env ls 2>/dev/null || true
```

Do not print environment values. Confirm that the Vercel project has the necessary Preview variables for the existing Supabase/API behavior. If the preview environment is not configured, stop before deployment and report the exact missing variable names.

- [ ] **Step 3: Start the local server and exercise the public routes**

Run the existing server in a retained process:

```bash
python3 serve.py
```

Check Home, `/rules`, `/profiles`, `/profile`, `/privacy`, and `/support` at phone-sized and desktop-sized viewports. Confirm menu focus/close behavior, section-link destinations, auth-gated link visibility, and unchanged page content. Do not submit scores, trigger email flows, or mutate production data during QA.

- [ ] **Step 4: Request the branch-preview push/deployment gate**

Because the repository's Vercel preview is driven by the GitHub branch, request explicit approval immediately before:

```bash
git push -u origin codex/redesign
```

Never use `git push origin master`, `git push --force`, or a production deployment command.

- [ ] **Step 5: Verify the public preview URL and live-data behavior**

After Vercel reports the branch deployment, open the exact preview URL in a private/unauthenticated browser session and verify:

- The URL resolves without a Codex, GitHub, or Vercel login.
- Home and `/rules` load directly.
- The mobile menu works.
- Public content is visible.
- Players and Rankings remain hidden until the site's existing login flow is used.
- Authenticated reads use the existing backend/data path.
- No production alias or `www.networthtennis.com` content was changed.

Return the preview URL as the primary handoff. Production merge/deploy remains outside this plan.

