# 0028 — Clinical framework baseline: sensitive-change and supply-chain gates

**Status:** CONFIRMED_ASSISTANT_SIDE

## Context

The repository already had strong clinical boundaries and a broad test matrix,
but its cross-repository governance framework lagged the operator's newer repos.
The gap was operational rather than clinical: no public vulnerability-reporting
front door, no append-only lessons log, mutable GitHub Action tags, unpinned
Hypothesis installation, no dependency review, and no commit-time sensitive-data
gate.

This repository is stricter than the general framework because a false negative
can place health-adjacent data in public history. A regex scanner still cannot
identify every HIPAA Safe Harbor identifier or establish de-identification.

## Decision

Adopt the shared governance framework without modifying the recurrence engine,
extractor, or views:

- keep `AGENTS.md` canonical and `CLAUDE.md` a thin tool-specific pointer;
- add `SECURITY.md` as the public reporting front door while retaining
  `SECURITY_AND_TOOL_POLICY.md` as the detailed canonical policy;
- add append-only `docs/LEARNINGS.md` and leave archived `JOURNAL.md` unchanged;
- expand the pull-request template with intent, deviation, AI-assistance,
  health/provenance classification, verification, and record-reconciliation
  fields;
- add a stdlib diff scanner, opt-in pre-commit hook, and read-only PR workflow;
- exempt only exact reserved synthetic sentinels under `tests/` and `data/`;
- pin every GitHub Action to a full commit SHA with a release-tag comment;
- centralize exact Ruff/Hypothesis versions in `requirements-dev.txt`;
- add read-only dependency review and weekly Dependabot checks.

The scanner reports detector ID, path, and line only. It does not print matched
values and does not scan names, addresses, URLs, IP addresses, or bare dates.
There is no arbitrary inline bypass marker.

Repository-level secret scanning, push protection, and CodeQL default setup are
enabled after the baseline branch is published so GitHub's own controls layer
with the repository checks. CodeQL uses the default high-precision query suite
for Python and GitHub Actions.

## Consequences

- Pull requests gain independent secret/identifier and dependency gates.
- Runtime remains pure stdlib; exact dev tools are installed only for development
  and CI.
- Action updates become explicit dependency changes instead of mutable tag moves.
- The scanner may block synthetic values that are not one of the reserved test
  sentinels. That is intentional; add a reviewed sentinel rather than a bypass.
- Passing the scanner is evidence about the implemented patterns only, not a
  compliance determination.

## Confirmation

- `python tools/scan_sensitive_changes.py --self-test`
- `python -m unittest tests.test_sensitive_scanner -v`
- `make check`
- `make proptest`
- `make html-demos`
- inspect `.github/workflows/` for `contents: read`, immutable action SHAs,
  `persist-credentials: false`, and absence of `pull_request_target`
- compare SHA-256 hashes of `recurrence.py`, `extract.py`, `view_html.py`,
  `report_html.py`, and `digest_html.py` with `main`

Confirmed on draft PR #44 (2026-06-11): the Python 3.10–3.13 test matrix,
Ruff, generated-HTML validation, sensitive-change scan, and dependency review
passed. The initial CodeQL setup run passed for Python and GitHub Actions;
secret scanning and push protection report enabled. The five clinical module
hashes match `main`.

## Research basis

- GitHub secure-use guidance: immutable action SHAs, least-privilege tokens, and
  untrusted pull-request input handling:
  https://docs.github.com/en/actions/reference/security/secure-use
- GitHub CodeQL default setup:
  https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning/configure-code-scanning
- GitHub dependency graph and supported ecosystems:
  https://docs.github.com/en/code-security/reference/supply-chain-security/dependency-graph-supported-package-ecosystems
- HHS de-identification guidance:
  https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html
- NIST Secure Software Development Framework:
  https://csrc.nist.gov/pubs/sp/800/218/final
- OWASP logging guidance on excluding sensitive values:
  https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
