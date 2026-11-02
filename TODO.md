## December 2026 league pause (November 2, 2026)

- [x] Production `GET /api/email` returns `paused_periods: ["December 2026"]`. Evidence: PR #43, merge `5a4e6a7`, checked November 2, 2026.
- [ ] November 27: confirm the scheduled run skips with a notice and sends nothing.
- [ ] January 1, 2027: confirm January pairings and match-email counts match, and that scheduled workflows stayed on. GitHub's 60-day shutoff was the risk the keep-alive now addresses. If the count is odd, confirm Natalie sat out and got the skip email, and that Ashley is next.
- [ ] Owner: update the vault `CRON_SECRET` to match Vercel. It returned 403 from production on November 2, 2026. Scheduled runs are unaffected.

## Public repo exposure (November 2, 2026)

- [x] Rewrite `master` history to remove member data and exposed values. Done and force-pushed November 2, 2026; final file tree unchanged.
- [ ] Ashley: revoke the Gmail app password exposed from January 2026 (`myaccount.google.com/apppasswords`). The code pointed `SMTP_USER` at Ashley's address until January 10, 2026, so this is probably Ashley's account; not tested. The code no longer uses it.
- [ ] Owner: ask GitHub Support to purge cached commits and `refs/pull/*`. Until then, old commits still open by exact hash, including the `.env.vercel` commit.

## Join signup follow-up (October 15, 2026)

- [x] Add a return-after-Venmo note to `/join`. Evidence: PR #37, merge `02472f0`, live page checked.
- [ ] Owner retests signup on the live site.
- [ ] Owner decision: deactivate Natalie's test signup. Send no email without explicit approval. Jessica and Mae need no follow-up (owner, November 2, 2026).

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
