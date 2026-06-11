# 0029 — Read-only clinical evidence audit with reviewed history

**Status:** CONFIRMED_ASSISTANT_SIDE

## Context

ADR 0028 adds hard repository and supply-chain controls. The remaining framework
piece is a feedback loop that can identify incomplete PR evidence without
granting an agent write access, commenting automatically, or interpreting
clinical material.

The slot-math repository's audit history demonstrated the useful structure, but
automatic commits are not appropriate here. A public health-adjacent repository
should keep history imports inside ordinary reviewed pull requests and keep the
artifact free of source, record, and PR-body text.

## Decision

Add a Python 3.10-compatible, stdlib-only advisory auditor with stable check IDs.
It reads pull-request metadata from the GitHub event file, resolves the base/head
commits, categorizes changed paths, and compares those categories to the PR
template's evidence fields. It does not evaluate clinical correctness.

The workflow:

- runs only on `pull_request`, never `pull_request_target`;
- has `contents: read` and checkout credentials disabled;
- reads metadata through `$GITHUB_EVENT_PATH` rather than shell interpolation;
- writes a job summary and one metadata-only JSON artifact;
- retains the artifact for 30 days;
- never comments, commits, pushes, changes settings, or accesses secrets;
- remains advisory until a later ADR explicitly changes enforcement.

History is imported only through reviewed PRs. `scripts/audit_history.py import`
validates the exact schema, rejects extra fields, deduplicates by head SHA, and
appends to `docs/evidence-audit-history.ndjson`. `retro` refuses to run before
five unique entries and prints proposals only. The first history PR is due after
five audit runs or 30 days, whichever occurs first.

## Consequences

- Reviewers get stable, low-privilege evidence checks without automated PR
  speech or repository mutation.
- Artifacts can support later tuning without retaining potentially sensitive PR
  prose or file paths.
- Advisory flags may be false positives while the baseline accumulates. They are
  review prompts, not clinical or compliance findings.
- Rule changes require normal code review and a later ADR; the retrospective
  cannot tune itself.

## Confirmation

- `python -m unittest tests.test_evidence_audit tests.test_audit_history -v`
- `python -S -m unittest discover -s tests -t .`
- `ruff check .`
- run the workflow on the stacked draft PR and inspect the job summary plus JSON
  artifact schema
- verify the workflow has no write permission, comment step, commit, push,
  secret reference, or `pull_request_target`
- verify the five clinical modules are unchanged from the PR 1 base

The direct-CLI test creates a temporary Git repository and confirms that the
auditor preserves tracked content while writing only the requested artifact.

Confirmed on stacked draft PR #45 (2026-06-11): all GitHub checks passed,
including the evidence-audit job. The downloaded artifact matched the exact v1
schema; all 11 stable checks passed and the only change detail retained was four
category counts. The five clinical modules match the PR #44 base.
