# Repository learnings

Append-only. Add dated, concise entries when a tool behavior, failure mode, or
verification result should survive the session. Do not rewrite earlier entries;
append a correction that points back to the original date.

## 2026-06-11 — Commit gates must stay narrower than compliance claims

- A diff scanner can block high-confidence secrets and identifier shapes without
  echoing values into logs.
- It cannot establish HIPAA de-identification. Names, addresses, URLs, IPs, and
  bare dates remain contextual and are deliberately outside this regex gate.
- Synthetic exemptions are exact reserved sentinels and apply only under
  `tests/` and `data/`; arbitrary bypass comments are not accepted.
- The scanner must pass against its own staged source. Build reserved sentinel
  literals from fragments in the implementation so the tool does not need to
  exempt itself.

Verification: `python tools/scan_sensitive_changes.py --self-test` and
`python -m unittest tests.test_sensitive_scanner -v`.

## 2026-06-11 — GitHub workflow references are executable dependencies

- Pin third-party actions to full commit SHAs and retain the release tag in a
  comment so the review is both immutable and readable.
- Give workflow tokens explicit read-only permissions unless a job demonstrates
  a narrower write need.
- Read pull-request metadata from the event payload; do not interpolate it into
  shell source.

Verification: inspect `.github/workflows/` and run the normal PR checks.

## 2026-06-11 — Windows verification may need the Makefile commands directly

- This checkout's PowerShell environment did not provide `make`.
- Run the commands behind `make check` directly: unittest discovery, both
  self-tests, compileall, and Ruff. CI remains the authoritative Makefile run on
  Ubuntu.

Verification: each underlying command must exit zero; do not report `make check`
as locally run when only its component commands were available.

## 2026-06-11 — Dependency review requires the repository dependency graph

- A valid dependency-review workflow fails immediately when the repository
  dependency graph is disabled.
- Enabling repository vulnerability alerts also exposed the dependency-graph
  SBOM endpoint for this public repository; rerun the failed job after verifying
  that endpoint.

Verification: `gh api repos/Inbound-health-care/Health-Prototype/dependency-graph/sbom`
returns the repository SBOM name, then the dependency-review rerun must pass.

## 2026-06-11 — Audit history should preserve metadata, not review prose

- A useful retrospective needs stable check IDs, commit IDs, timestamps, and
  category counts; it does not need PR-body or source text.
- Reject unknown artifact fields at import so a later workflow change cannot
  silently widen the retained data boundary.
- Keep imports in reviewed PRs and require five unique entries before proposing
  check changes.

Verification: `python -m unittest tests.test_evidence_audit tests.test_audit_history -v`.
