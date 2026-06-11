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
