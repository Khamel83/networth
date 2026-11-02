## December 2026 league pause (November 2, 2026)

- [x] Production `GET /api/email` returns `paused_periods: ["December 2026"]`. Evidence: PR #43, merge `5a4e6a7`, checked November 2, 2026.
- [ ] November 27: confirm the scheduled run skips with a notice and sends nothing.
- [ ] January 1, 2027: confirm January pairings and match-email counts match, and that scheduled workflows stayed on. GitHub's 60-day shutoff was the risk the keep-alive now addresses. If the count is odd, confirm Natalie sat out and got the skip email, and that Ashley is next.
- [ ] Copy the production `CRON_SECRET` from Vercel into the vault as `NETWORTH_CRON_SECRET` (owner request, November 2, 2026). Blocked: this agent connection needs Vercel team access, and GitHub secrets cannot be read. Do not change the Vercel or GitHub values. The existing vault `CRON_SECRET` gets 401 from production; it lives in the shared `services.env`, so check other users before overwriting it. Scheduled jobs are unaffected.

## Public repo exposure (November 2, 2026)

- [x] Rewrite `master` history to remove member data and exposed values. Done and force-pushed November 2, 2026; final file tree unchanged.
- [x] Gmail app password deleted (owner reported Ashley's confirmation, November 2, 2026).
- [x] GitHub secret scanning and push protection enabled; the one alert, a dead Resend key, is resolved as revoked.
- [x] GitHub Support purge request submitted November 2, 2026, from khamel83@gmail.com. Confirmation page shown; purge not yet confirmed. Old commits keep opening by exact hash until Support acts. No further work is planned: the owner accepts what remains.

## Join signup follow-up (October 15, 2026)

- [x] Add a return-after-Venmo note to `/join`. Evidence: PR #37, merge `02472f0`, live page checked.
- [x] Owner retested signup (owner, November 2, 2026).
- [x] Natalie's test signup handled (owner, November 2, 2026). Jessica and Mae need no follow-up.

## PR29 acceptance repair

- [x] Accept final-head source review and successful required checks for PR29. Evidence: https://github.com/Khamel83/networth/pull/29 (merge1d9a65781a046a04f9d8d37b8d225b7dc4d66aa3; final-head PASS and required checks succeeded).
  Annual domain/Resend/CSV/renewal follow-ups remain outside the managed block.
  The prior run passed198 API tests, then failed optional Codecov TLS upload;
  coverage transport is now advisory without weakening pytest.

<!-- janitor:begin:todo -->
- [x] PR #28 follow-up. Merged as `ef79caf5`; November 2026 scheduled pairings ran with 17 of 17 match emails accepted (run `41349485297`).
<!-- janitor:end:todo -->

## Owner follow-ups (outside the janitor block)

- [x] Repo stays public; `keep-alive.yml` re-enables schedules every 5 days, and the watchdog emails if GitHub disables them anyway (fix: Actions > Enable workflow)
- [ ] Yearly: domain renewal, Resend domain check, CSV export of players/matches, reset Paid boxes at renewal
