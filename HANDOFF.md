# Managed rule repair handoff — 2026-10-05

## Source

PR [#28](https://github.com/Khamel83/networth/pull/28) started from source
candidate `24e91819088e4e301eba03d1f98b25cd8097c295`. This repair changes only
managed working documentation: the Janitor rule now requires the latest
trusted, non-dismissed OCI reviewer Bot PASS for the exact current commit, and
stale, superseded or contradictory PASS does not qualify. All-PR eligibility,
catalog exclusions, normal GitHub protections, and the single PASS gate remain
as authorized.

## Runtime and effects

- Source scope: `AGENTS.md`, `TODO.md`, `CONTEXT.md`, and this handoff only.
- Source operation: no runtime, provider, or deployment operation was performed
  by this repair.
- Durable runtime receipt and downstream effect: not established by this
  source-only change; verify them separately after merge.

## Next verification

Push the existing PR branch without force, let the natural webhook review the
new head, then inspect native current-head reviews and recheck the PR state.
