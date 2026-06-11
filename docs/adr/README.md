# Architecture & process decision records (ADRs)

A running, append-as-you-go log of decisions on this project — **both** durable
build/architecture choices **and the assistant's own process/behavior changes**
(what it started doing differently, and why). The log is written *as the work
happens*, not reconstructed at session end. The session narrative lives in
`JOURNAL.md`; this directory is the finer-grained "decision + why + how it's
checked" record.

Why a log at all: an improvement that lives only in chat dies at the session
reset. Writing it here (a file the next memory-less instance can read) is how a
decision actually persists. See `docs/CLAUDE_OPERATING_MANUAL.md` and
`docs/DOC_DISCIPLINE.md`.

## Format (per `DOC_DISCIPLINE.md` §2)

Each ADR is `NNNN-short-slug.md` and states:

- **Context** — what prompted the decision; the problem or need.
- **Decision** — what was chosen (and notable alternatives rejected).
- **Consequences** — what this makes easier/harder; trade-offs.
- **Confirmation** — *how the decision is verified* (a test, a command, a
  transcript check). No ADR is ceremony; every one is checkable.
- **Evidence level** — `CONFIRMED_USER_SIDE` / `CONFIRMED_ASSISTANT_SIDE` /
  `IMPLEMENTED_UNVERIFIED` / `RESEARCH_ONLY` / `SUPERSEDED`.

Mark a superseded decision `SUPERSEDED` (point to its replacement); don't delete
it — history is the point.

## Index

- [0001 — Tool-call discipline: one decisive call, trust exit codes over prose](0001-tool-call-discipline.md)
- [0002 — Combined report: expert registry, omit clean records, additive formatter kwarg](0002-combined-report-architecture.md)
- [0003 — Co-occurrence: the fourth surfacing rule (two items, same dates)](0003-cooccurrence-rule.md)
- [0004 — `--report-v1`: the combined report with v1 opt-in matching](0004-report-v1.md)
- [0005 — Reconcile the stranded doc/harness stack; adopt Tier-1/Tier-3 split](0005-doc-harness-reconciliation.md)
- [0006 — Adopt AGENTS.md as source of truth; slim CLAUDE.md; add control-doc layer](0006-agents-md-source-of-truth.md)
- [0007 — Cadence change: the fifth surfacing rule (interval shifted)](0007-cadence-change-rule.md)
- [0008 — Free-text extraction: design kickoff (deterministic front-end)](0008-freetext-extraction-kickoff.md)
- [0009 — Legal grounding: the allowlist + the librarian rule (HIPAA Safe Harbor + FDA Non-Device CDS)](0009-legal-grounding.md)
- [0010 — Rename the "firewall" metaphor (librarian rule / allowlist / research gate)](0010-rename-firewall-metaphor.md)
- [0011 — FDA CDS guidance refreshed (Jan 2026) + 2026 compliance audit](0011-fda-cds-guidance-refresh-2026.md)
- [0012 — Free-text matching modes (strict/synonyms/fuzzy/both) + merge-safety guards](0012-freetext-matching-modes.md)
- [0013 — Relative-date anchoring (conservative, opt-in)](0013-relative-date-anchoring.md)
- [0014 — HTML report view (UI slice 1): provenance made visible](0014-html-report-view.md)
- [0015 — Pre-visit Pattern Digest view (UI slice 2): the clinician product surface](0015-pre-visit-digest-view.md)
- [0016 — Multi-patient free-text extraction (fail-closed identity, per-patient de-id)](0016-multi-patient-fail-closed-extraction.md)
- [0017 — Calm, eye-comfort view theme (warm neutrals + one non-semantic accent)](0017-calm-eye-comfort-view-theme.md)
- [0018 — Responsive / mobile pass (Android-targeted)](0018-responsive-mobile-pass.md)
- [0019 — View review refinements (toggle / citation pills / wording / view names)](0019-view-review-refinements.md)
- [0020 — Multi-patient digest rendering (stacked, per-patient scoped, quarantine surfaced)](0020-multi-patient-digest-rendering.md)
- [0021 — Promote shared view primitives to `view_html.py`; report_html multi-patient parity](0021-view-html-extraction-report-multi.md)
- [0022 — Keyboard navigation + print pass (shared interaction layer)](0022-keyboard-nav-and-print.md)
- [0023 — At-a-glance cited-date timeline (ticks-only, single-accent, document order)](0023-at-a-glance-cited-date-timeline.md)
- [0024 — Governance: JOURNAL.md retired (chat-only) + LICENSE = Apache-2.0](0024-journal-retired-and-license.md)
- [0025 — Verification ceiling: live JS test + Hypothesis gates CI + oracle convention](0025-verification-ceiling-closed.md)
- [0026 — CI HTML-validation gate: proof-html on the generated views](0026-ci-html-validation-gate.md)
- [0027 — Rule-layer metamorphic property tests (verification ceiling reaches the five rules)](0027-rule-layer-property-tests.md)
- [0028 — Clinical framework baseline: sensitive-change and supply-chain gates](0028-clinical-framework-baseline.md)
- [0029 — Clinical expert rollout: a three-stage, deterministic, librarian-safe plan (RESEARCH_ONLY)](0029-clinical-expert-rollout-plan.md)
