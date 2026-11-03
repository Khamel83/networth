## Dashboard fixes and private copy — November 2, 2026
The dashboard now links admins to `/admin` and names the opponent in the score boxes (PR #60). A cleaner private copy is in `Khamel83/networth2`; it is not deployed and is not connected to this site or its database. Other fixes wait for a swap decision, not before the January 1 check.
## December 2026 league pause — November 2, 2026

November automation evidence: the October 31 final reminder reported 51 accepted. Run `41349485297` on November 1 created 17 pairings with 17 match emails accepted, and run `41360828765` read back 17 assignments, each with a match email ID.

Decision: organizers want no December matches and a restart in January. `PAUSED_PERIODS` in `api/league_calendar.py` holds December 2026; `RUNBOOK.md` has the date table. Source: PR [#43](https://github.com/Khamel83/networth/pull/43), merge `5a4e6a7`. Runtime: production `GET /api/email` returned the paused month on November 2, 2026. Downstream effect is unverified: no scheduled run has skipped yet. Next check: the November 27 run. No email was sent and no workflow was dispatched.

Organizer skip: an organizer who sits out now gets an email. The turn now passes back and forth instead of following the calendar month (owner decision, November 2, 2026). It starts from Ashley sitting out November 2026, so Natalie is next, in January 2027 if the count is odd. A month where only one organizer was paired counts as the other sitting out, even after a voluntary pause. Source and tests only until the first odd month after this change; no email was sent.

Stale records closed the same day: PRs #28, #29 and #39 are merged, issues #34 and #35 are closed, and scheduled November pairings matched 17 emails to 17 assignments.

Public repo cleanup, November 2, 2026: the owner asked for history to be scrubbed. `master` was rewritten with `git-filter-repo` and force-pushed; the file tree stayed identical. Removed: member spreadsheet and data files, databases, `.env.vercel`, `docs/sessions`, committed virtualenv and bytecode. Redacted everywhere: 84 emails, 42 phones, 22 full names, 3 credentials. Commit hashes in older notes predate the rewrite and no longer match `master`. GitHub still serves old commits by hash and through `refs/pull/*` until Support purges them; a request was submitted November 2, 2026. The pre-scrub backup is `~/archive/git-bundles/networth-pre-history-scrub-20261102.bundle`, and it contains the removed data. Any other clone, including the OCI janitor's, must re-clone and must not push old history back.

Vault: use `secrets get NETWORTH_CRON_SECRET` for this project. The shared `CRON_SECRET` gets 401 from production. Vercel still lists an unused `SMTP_PASSWORD`, for the Gmail app password reported deleted.

Cleanup, November 2, 2026, at the owner's request: local `master` was reset to origin, and all 6 local `auto-wip` branches and 37 remote branches were deleted. Everything, including the 3 unpublished janitor commits, is in `~/archive/git-bundles/networth-all-branches-20261102.bundle` on the Mac mini, with a ref list beside it. The janitor cron has been disabled since July 2026.

## Join page Venmo return note — October 15, 2026

Source: PR [#37](https://github.com/Khamel83/networth/pull/37) merged as `02472f0`. It adds a line under the
`/join` paid checkbox that tells members to come back after Venmo and tap **Join Now**.
Runtime: Vercel production deployment for `02472f0` succeeded, and the live `/join` page contains the note (checked October 15, 2026).
No email, workflow, or player-record action was taken. The owner asked that no emails be sent.
The owner retested signup and handled Natalie's test signup (November 2, 2026). Jessica and Mae need no follow-up (owner, November 2, 2026).
Temporary worktree `.worktrees/venmo-return-note` was removed after the merge.
