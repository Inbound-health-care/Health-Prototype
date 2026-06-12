# 0029 — Clinical expert rollout: a three-stage, deterministic, librarian-safe plan

**Status:** RESEARCH_ONLY — Stage 1 landed via **ADR 0030** (governance audit
trail + deterministic monitor); Stage 2 design fixed (addendum below, build
deferred to a fresh session); Stage 3 remains planned.

This ADR is a **plan**, not an implementation. It records the decision to pursue a staged rollout
and the boundary every stage must respect. Each stage graduates only via its own ADR + tests
(`DOC_DISCIPLINE.md` §Research gate). No engine code changes with this ADR.

## Context

An external "Mixture-of-Experts maps onto your three engines" document proposed six "experts" across
ingestion, pattern detection, and governance. It is the "six experts" item STATUS has carried as
**PARKED** since 2026-06-07. Scott asked for a full run: verify it, then plan a low-risk staged
rollout from what already exists.

Independent web verification (`docs/RESEARCH_2026-06-11_moe-clinical-rollout.md`, RESEARCH_ONLY)
found the citable systems real (SparseDoctor, CLINES, the drift-monitor paper) and the soft claims
inflated or fabricated (the "TRIAGE" framework, the follow-up extractor's 0.997 F1 / 0.00-day MAE,
"sparse MoE outperforms dense on clinical tasks," and "the AMA *requires* audits"). Four of the six
experts break a repository pillar as written: 1B emits risk scores (librarian rule), 2A/2B name
neural models + UMLS (stdlib + local-only + license), and 3A is ML model-adaptation (a deterministic
engine has no model to drift).

## Decision

Adopt a **three-stage rollout** of only the deterministic, librarian-safe subset, lowest-risk first.
Pillars held for this rollout (operator decision, 2026-06-11):

- **Librarian rule: held.** No scoring/ranking/interpretation. The 1B "TRIAGE" risk corrector is
  **cut**, not deferred.
- **Local-only / zero-PHI: held.** No cloud calls; synthetic data only.
- **No-deps: relaxed to "optional + graceful-skip" only.** Core still imports and runs on bare
  stdlib; any dependency is an enhancer that skips cleanly when absent (the existing Hypothesis /
  Playwright pattern). CI stays green without it.
- **Stage 3 stays deterministic** — lexicons / date libraries permitted, **no ML model**.

Stages (each is additive; the five clinical modules' public behavior is unchanged until its own ADR
graduates it):

1. **Governance engine — audit trail + deterministic monitor (Stage-1 lead).** An append-only,
   hash-chained (tamper-evident) log of every surface/extract event — input digest, rules fired,
   findings cited, timestamp — plus a deterministic rule-firing-rate / input-stats monitor. Pure
   stdlib (`hashlib`/`hmac`/`json`). Extends the ADR 0028 governance baseline. Reframes the doc's 3B
   (audit) and 3A (telemetry, not ML drift). Reword the regulatory framing to "AMA/ATA *recommend*".
2. **Pattern engine — temporal-relation surfacing.** Deterministic before / after / same-day /
   within-window relations (Allen-interval style) over already-cited dates, feeding a fuller
   timeline. Additive to `recurrence.py`; surfaces relations, never interprets them. The doc's 1A.
3. **Ingestion engine — follow-up + assertion context.** Deterministic (action, date) follow-up
   extraction via date arithmetic (extends ADR 0013 relative-date anchoring) + NegEx-style
   negation/assertion context as an optional graceful-skip lexicon. The doc's 2A symbolic half and
   2B assertion slice. UMLS normalization is **deferred** (license + interpretation).

## Stage 2 design addendum (2026-06-11; build deferred to a fresh session)

Decided after the Stage-2 standards research (`docs/RESEARCH_2026-06-11_temporal-relations.md`,
RESEARCH_ONLY). Records the shape so the build starts clean; still no code in this ADR.

- **Relation vocabulary:** `BEFORE` / `AFTER` / `SAME_DAY` / `WITHIN_WINDOW(days)` over day-dated
  POINT events. This is point algebra (Allen's 13 collapse to 3 for instantaneous events) plus one
  metric bound; the THYME/i2b2 `CONTAINS` relation is dropped (it is for narrative interval time, not
  explicit dates).
- **Adjacent-pair only**, sorted by `(date, document-order, item)` — a documented, NON-interpretive
  same-day tie-break (NOT clinical event-type precedence, which would be interpretation). Transitive
  closure is refused (O(n^2), floods output); "all events before X" is a post-hoc filter, not
  pre-computed.
- **Undated entries** are surfaced separately as "undated," never placed on the ordered axis (mirrors
  ADR 0013's "cited but undated" stance).
- **Opt-in lens (Scott's call, 2026-06-11):** a new `build_timeline` / `format_timeline` API in
  `recurrence.py` + a `--demo-timeline`, plus a SEPARATE opt-in registry or `--report-timeline` so the
  default `--report` stays clean. Rationale: an adjacent-sequence lens fires on nearly every record
  with 2+ dated entries, unlike the 5 pattern rules that flag only when a pattern is present; adding it
  to the default `EXPERTS` registry would flood the combined report and break "the report surfaces only
  what is present."
- **Librarian-safe:** dates + interval-days + relation token + citations only; the banned-words gate
  (`tests/banned_words.py`) is enforced on timeline output; a fixed "sequence, not causation" caveat
  goes in any Stage-2 view. Sequence is surfaced, never causality (the post-hoc fallacy is the named
  risk). Engine pattern rules and their oracles stay byte-unchanged; the timeline is additive.
- **Confirmation (per-stage gate):** oracle written first (hand timeline over the sample records),
  `make check` green, additive tests + a Hypothesis property (ordering invariance under shuffle; shift
  invariance of interval-days), `git diff` showing the 5 rules + their answer keys unchanged.

## Consequences

- The rollout adds capability while keeping the engine deterministic, librarian-safe, and
  stdlib-runnable; the existing suite stays green by construction.
- The neural/scoring experts (BioBERT MoE, LoRA-MoE, UMLS normalization, TRIAGE risk scores) are
  explicitly out of scope; revisiting any of them is a separate, pillar-changing decision.
- Stage 1 front-loads governance, building directly on ADR 0028, so later stages emit audit events
  from day one.
- This ADR commits to no code. If a stage proves to conflict with a pillar at design time, it is
  re-scoped or dropped, not forced.

## Confirmation

- This ADR is RESEARCH_ONLY: the plan is the artifact; verification is per-stage.
- Each stage lands behind its own ADR with tests (`make check` green, additive tests, engine hashes
  unchanged where claimed), graduating it from RESEARCH_ONLY.
- Verification basis for the framing: `docs/RESEARCH_2026-06-11_moe-clinical-rollout.md`.

## Research basis

- Verification ledger: `docs/RESEARCH_2026-06-11_moe-clinical-rollout.md` (RESEARCH_ONLY).
- Governance baseline this builds on: ADR 0028; OWASP logging guidance (exclude sensitive values):
  https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- Relative-date anchoring Stage 3 extends: ADR 0013.
- AMA AI principles (audit guidance, reworded to "recommend"):
  https://www.ama-assn.org/system/files/ama-ai-principles.pdf
- ATA AI principles (validation / monitoring):
  https://www.americantelemed.org/press-releases/american-telemedicine-association-publishes-new-artificial-intelligence-ai-principles/
