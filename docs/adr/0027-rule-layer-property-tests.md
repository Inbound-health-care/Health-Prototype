# 0027 — Rule-layer metamorphic property tests (the verification ceiling reaches the five rules)

**Date:** 2026-06-07
**Evidence level:** CONFIRMED_ASSISTANT_SIDE — the four new properties run green **derandomized**
(`CI=1`, 8 property tests OK) and `make check` stays green (**253 tests**, 6 skipped without
Hypothesis; self-tests 6+10; ruff clean); the engine is **unchanged** (`git diff` touches only
`tests/`, `Makefile`, `ci.yml`). Promotes to CONFIRMED_USER_SIDE when Scott runs `make proptest`.
The external research that prompted this stays **RESEARCH_ONLY** — see
`docs/RESEARCH_2026-06-07_ai-verification.md`.
**Type:** testing / verification
**Builds on:** ADR 0016 (multi-patient fail-closed → first Hypothesis properties), ADR 0025
(verification ceiling: static-string → live-JS + Hypothesis-in-CI), ADR 0026 (the "vacuous green" framing).

## Context
Three Gemini deep-research docs on AI verification were audited this session (provenance,
the section-by-section verdict, and a fabrication ledger live in the research note above). The
honest finding: this engine is **deterministic, pure-stdlib, no-LLM**, so most of the 2026
eval-methodology corpus is **inapplicable** (LLM-as-judge bias, agentic trajectory eval,
quantization/precision differential testing, benchmark contamination, OTel tracing — nothing in
the engine to apply them to) or merely **corroborates** what the repo already does (oracle
convention, fail-closed abstention, the banned-words gate, the vacuous-green guard).

The **one transferable technique is metamorphic / property-based testing**, and it lands on a real
gap. The five surfacing rules (`recurrence.py`) and the single-note path are pinned only by the
~9 hand-crafted oracle records in `data/sample_records.py`; only the multi-patient EXTRACTOR had
Hypothesis properties (`tests/test_extract_multi_properties.py`, ADR 0016/0025). A rule-layer bug
that the crafted examples don't happen to hit — a cross-record state leak, an order dependence, a
mixed shifted/unshifted-date arithmetic error, or a span-rebase off-by-one — could ship green.

## Decision
Extend property coverage **up to the rule layer** with four metamorphic relations, asserted across
all five rules at their documented defaults. New `tests/test_rule_properties.py`:
- **P1 — record isolation:** appending a disjoint record never changes any OTHER record's findings
  (the no-bleed promise, now tested at the rule layer, not just the extractor).
- **P2 — reordering invariance:** shuffling the record list AND the entries within a record leaves
  the finding set identical (the engine is order-independent under exact matching).
- **P3 — shift invariance:** a constant date shift maps recurrence dates by exactly the offset and
  leaves every interval/count finding (gap days, frequency window span, cadence intervals,
  co-occurrence counts) unchanged.

And one extractor-layer property added to `tests/test_extract_multi_properties.py`:
- **P4 — span integrity:** every accepted entry's `source_span` recovers its item, and a record's
  spans are strictly increasing and non-overlapping — each cited occurrence is a distinct, ordered
  citation (guards `_rebase_spans` + the HTML highlight).

Wired into `make proptest` and the CI proptest step (both now run the two modules), **derandomized
under `CI`** so a failure reproduces locally (ADR 0025). Hypothesis stays dev/CI-only; the engine
and `make test` remain pure-stdlib (the module SKIPS cleanly when Hypothesis is absent).

**Alternatives rejected.** (a) **Docs-only capture** of the research — records it but improves
nothing; Scott named this the "run-around." (b) The pasted **MoE / "six neural experts"** reframe —
needs models, training, a learned router (PyTorch/vLLM), which would break pure-stdlib, determinism,
and the non-interpreting librarian rule (and its FDA Non-Device positioning); its one sound kernel
("separate deterministic concerns") is already the repo's gates. (c) Leaving the relations as prose
in a comment — no enforcement, so no gate.

## Consequences
- Rule-layer regressions (cross-record bleed, order-dependence, mixed-shift date math, span-rebase
  off-by-one) now fail a PR gate instead of shipping. This is the same ceiling-raising step as ADR
  0016 (multi-patient → Hypothesis) and ADR 0025 (static-string → live-JS), applied to the rules.
- One new dev/CI-only test module; the CI proptest step runs both property modules.
- Pure-stdlib runtime preserved; `make test` unaffected (skips when Hypothesis absent).
- The research is now **graduated** per `DOC_DISCIPLINE.md` §Research gate: a source was identified,
  an ADR accepts it, and a test proves it. The non-transferable findings stay RESEARCH_ONLY.

## Confirmation
- `make proptest` → **8 property tests OK** (the 4 new + the 4 pre-existing), `CI=1` derandomized:
  `python -m unittest tests.test_rule_properties tests.test_extract_multi_properties`.
- `make check` green: **253 tests** (6 skipped without Hypothesis), self-test 6+10, ruff clean.
- Engine unchanged: `git diff --stat` shows only `tests/`, `Makefile`, `.github/workflows/ci.yml`.
- CI (authoritative): the proptest step installs Hypothesis and runs both modules derandomized,
  alongside `lint`, the 4-way `test` matrix, and the `html` gate.
- CONFIRMED_USER_SIDE pending: Scott runs `make proptest` locally.
