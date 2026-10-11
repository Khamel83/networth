## PR29 acceptance repair

- [x] Accept final-head source review and successful required checks for PR29. Evidence: https://github.com/Khamel83/networth/pull/29 (merge1d9a65781a046a04f9d8d37b8d225b7dc4d66aa3; final-head PASS and required checks succeeded).
  Annual domain/Resend/CSV/renewal follow-ups remain outside the managed block.
  The prior run passed198 API tests, then failed optional Codecov TLS upload;
  coverage transport is now advisory without weakening pytest.

<!-- janitor:begin:todo -->
- [ ] Complete PR #28's remaining deployment, durable receipt and downstream
  verification follow-up. Source merged as `ef79caf5`; that merge does not
  establish runtime adoption or downstream effect. Preserve the source-only
  boundary until the corresponding evidence exists.
<!-- janitor:end:todo -->

## Owner follow-ups (outside the janitor block)

- [x] Repo stays public; the watchdog emails if GitHub disables schedules after 60 quiet days (fix: Actions > Enable workflow)
- [ ] Yearly: domain renewal, Resend domain check, CSV export of players/matches, reset Paid boxes at renewal

## Owning repository plan

Use [the ordered reconciliation](docs/REPO_PLAN.md) and [coordinator #34](https://github.com/Khamel83/networth/issues/34). It maps every observed open source record. Existing incomplete acceptance and holds remain in force.
