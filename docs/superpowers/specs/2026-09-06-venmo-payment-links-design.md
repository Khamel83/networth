# Join Page Venmo Payment Links Design

## Status

Approved for implementation.

## Goal

Make the `/join` payment instruction actionable without adding payment processing to Net Worth. A visitor should be able to open Venmo for the correct recipient with the membership amount and a short payment note already filled in.

## Validated payment URLs

The following HTTPS URLs were opened directly before implementation:

- Player: `https://venmo.com/u/ncoffen?txn=pay&amount=35.00&note=Net%20Worth%20Tennis%20Player%20membership`
- Social Butterfly: `https://venmo.com/u/ncoffen?txn=pay&amount=45.00&note=Net%20Worth%20Tennis%20Social%20Butterfly%20membership`

Both resolve to Natalie Coffen, displayed by Venmo as `@ncoffen`. On the desktop web fallback, Venmo requires sign-in and does not submit a payment automatically. The payer remains responsible for reviewing and confirming the transaction.

## User experience

- The main instruction above the form links the existing `@NCOFFEN (Natalie)` reference to the Player payment URL with `$35.00` prefilled.
- The Social Butterfly membership option includes a lower, explicit `$45` Venmo link in its description.
- Payment links open in a new browser context with `rel="noopener noreferrer"` so the join form remains available.
- The success state contains one payment link. The existing selected membership tier determines whether it points to the `$35` Player URL or the `$45` Social Butterfly URL.
- Existing membership radio buttons, availability rules, form submission, authentication, and API behavior remain unchanged.

## Technical design

Keep the change in `public/join.html`, which already owns the join page markup, styles, and client-side form behavior. Store the two canonical payment URLs in page-local constants. Use static anchors for the initial instruction and tier description so payment remains usable without JavaScript. Update the success-state link only after a successful form submission, using the already selected `membershipTier` value.

## Non-goals and safeguards

- Do not add Venmo SDKs, OAuth, webhooks, or server-side payment handling.
- Do not attempt to send or authorize money from the site.
- Do not treat opening a Venmo URL as proof of payment; existing admin verification remains authoritative.
- Do not change prices, membership definitions, or the join API contract.
- Do not modify the home page or other payment copy unless required by this page-local change.

## Verification

- Add static tests that require both exact payment URLs, visible `$35`/`$45` labels, safe new-context link attributes, and the success-state payment link.
- Run the focused join-page tests, then the full existing pytest suite and `git diff --check`.
- Inspect the deployed `/join` page and open both payment links to confirm the recipient page and query parameters remain intact. No payment will be submitted.
