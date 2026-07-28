# Public Navigation and Game Play & Scoring Design

## Status

Approved for specification review; implementation has not started.

## Goal

Improve Net Worth's public-site navigation and the `/rules` Game Play & Scoring experience for a mobile-first audience, especially iPhone users, without changing the site's established visual identity or any meaningful league behavior.

The change will remain isolated to the `codex/redesign` branch and will be easy to apply through the existing Vercel deployment flow later. No live deployment is part of this work.

## Non-goals and invariants

- Do not replace Net Worth with Impeccable or add Impeccable as a runtime dependency. Impeccable is inspiration and a review lens only.
- Do not change APIs, database schema, authentication flows, ranking logic, match scoring, forfeits, membership rules, or player data.
- Do not substantially redesign the gradient, typography, logo, glass-card treatment, page composition, or existing brand personality.
- Do not introduce a frontend framework or a new build system.
- Do not deploy to production or modify `master`.
- Do not change the meaning of the rules. Copy edits are limited to small clarity, punctuation, and consistency improvements that help new players.

## User experience

### Public navigation

All public-facing pages will share the same navigation contract and visual treatment:

- The Net Worth logo returns to Home.
- How It Works links to `/#how-it-works`.
- Courts links to `/#courts`.
- Game Play & Scoring links to `/rules`.
- Players and Rankings remain members-only and are hidden while logged out.
- Logged-out visitors see Sign In and Join Now.
- Logged-in visitors see My Profile and Sign Out.
- The current page receives a clear active state where applicable.
- Footer navigation follows the same destinations and access model.

Links to home-page sections from another route must return to Home and scroll to the target section.

### Mobile behavior

The navigation is designed primarily for approximately 320–430px phone widths, with desktop and tablet layouts preserved as secondary experiences.

- A compact menu button opens the full navigation.
- The button exposes `aria-expanded` and `aria-controls` state.
- The menu supports keyboard focus, Escape-to-close, and outside-click close behavior.
- Navigating to another page closes the menu naturally.
- Controls have comfortable touch targets and visible focus states.
- The mobile treatment is restrained and uses the existing brand styling rather than introducing a new visual language.

### Game Play & Scoring page

`/rules` remains a separate page. It receives the shared navigation and footer, an active Game Play & Scoring state, and responsive header/menu behavior. Its existing rule sections and examples remain intact except for narrowly scoped copy editing that improves readability without changing substantive rules.

## Technical design

### Shared navigation layer

Add a small shared navigation module and navigation-only stylesheet under `public/`. The module is responsible for:

1. Defining the canonical public link configuration and destinations.
2. Reading the existing local-storage session signals without changing auth semantics.
3. Showing or hiding members-only links based on the current auth state.
4. Rendering or upgrading the page navigation with the correct active state.
5. Managing mobile-menu interactions and accessibility attributes.

Each public page will include the shared navigation contract and identify its page context with a data attribute. Page-specific content and styles remain local to each page.

The implementation should preserve a basic semantic navigation shell in the page markup where practical, with the shared module enhancing state and interaction. A missing navigation container or a script error must not prevent the page body from rendering.

### Scope of page updates

The first pass covers the public pages that expose site navigation: Home, `/rules`, Players, player profile detail, privacy, and the authentication/join surfaces where the shared header is present. Existing page-specific actions such as Instagram, Join Now hero CTAs, and profile-specific back links remain unchanged unless required to avoid a navigation conflict.

No ranking or player API code is changed.

## Error handling and edge cases

- Missing or malformed local-storage auth data is treated as logged out.
- Members-only links must not be exposed merely because a stale partial session value exists; preserve the existing requirement that both player and token signals are present.
- Mobile menu state is local to the current page and resets on navigation.
- The navigation module should fail quietly if an expected optional element is absent.
- Existing page content must remain usable if JavaScript does not finish initializing.

## Verification plan

### Automated checks

- Run the existing Python/API test suite.
- Add lightweight static checks for shared navigation inclusion, required page context, canonical destinations, and gated-link markers where useful.
- Verify the working tree contains no changes outside the intended branch/specification scope before implementation begins.

### Manual matrix

Check logged-out and logged-in states across:

- Home.
- `/rules`.
- Players and player profile pages.
- Privacy, login, and join pages where the shared header is present.

At minimum, inspect phone widths around 320px, 375px, and 430px, plus representative tablet and desktop widths. Confirm:

- The menu opens, closes, and remains usable by keyboard.
- Active navigation state is understandable.
- Home-section links land on the correct section.
- Players and Rankings visibility matches auth state.
- My Profile and Sign Out replace logged-out actions after login.
- No visual regression to the current gradient, typography, cards, rankings, or page content.

## Deployment shape

The implementation should be deployable through the repository's existing Vercel process without migrations, secrets, or infrastructure changes. Work remains on `codex/redesign`; deployment, merge, and any production verification require a later explicit decision.

