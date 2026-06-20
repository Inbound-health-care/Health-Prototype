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

## 2026-06-11 — Shared agent-rules core added; STATUS.md stays canonical for state

- AGENTS.md now carries the cross-repo shared core (working agreement, agent
  safety, source-of-truth order, environment/subagents) between the librarian
  rule and Commands. The source-of-truth order governs code-truth conflicts; a
  repo-specific line keeps STATUS.md canonical for "where am I / what's next."
- SECURITY_AND_TOOL_POLICY.md remains the fuller safety policy and governs on
  detail; the core is the cross-repo baseline.
- Verified on this branch: make check green, make test 326 OK (4 pre-existing
  skips), sensitive-change scan clean.

## 2026-06-15 — Repository controls need their own ratchet

- The health repo already had strong rule documents and workflow hygiene, but
  required files and workflow-hardening assumptions were distributed across docs.
- A committed control policy plus stdlib audit makes the layer checkable: if a
  control file disappears, a workflow loses permissions/concurrency/timeouts, or
  an action stops being SHA-pinned, the repository-control gate should fail.
- Keep the audit structural and repo-local. It does not prove HIPAA compliance,
  branch-protection settings, or publication safety.

Verification: `python tools/control_audit.py`, `make control-audit`, `make check`,
and the `Repository controls` PR workflow.

## 2026-06-20 — Describing a capability must not over-claim it (agent-interop)

- Publishing a machine-readable description of `detect_recurrence` (an A2A card +
  MCP tool-def) is low-risk only because the description is **enforced**, not just
  written: `tools/agent_card_validate.py` fails the build if the card claims a
  live endpoint/streaming while `STATUS.md` says `agent_interop_phase: A`, and the
  teeth in `tests/test_agent_card.py` prove the gate bites on six overclaiming
  variants — so it can't go vacuously green.
- The health-domain trap is wording: an "agent skill" can read as a clinical
  capability. The fix is to carry the librarian boundary into the card/tool-def/
  ADR verbatim — surfaces + cites only, synthetic data, no diagnosis/score/
  recommendation — and to make `liveEndpoint: false` a machine-readable fact, not
  a prose promise.
- Phase A is static-only by design (no server → no auth → no new runtime attack
  surface). A live endpoint + machine-to-machine auth is phase B, deferred.

Verification: `make agent-card`, `python -m unittest tests.test_agent_card`, `make check`.
