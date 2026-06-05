# 0008 — Free-text extraction: design kickoff (deterministic front-end)

**Date:** 2026-06-05
**Evidence level:** IMPLEMENTED_UNVERIFIED — slice 1 shipped: `extract.py` +
`tests/test_extract.py`, oracle-passing. CONFIRMED_ASSISTANT_SIDE (`make check` green —
117 tests / self-test 6+3 / `ruff` clean); promotes to CONFIRMED_USER_SIDE when Scott
runs it. The design + research that preceded it (Drive) were RESEARCH_ONLY.
**Type:** Architecture / kickoff

**Update (2026-06-05):** slice-2 matching (synonyms/fuzzy) is specified in **ADR 0012** — explicit,
must-be-chosen modes (strict/synonyms/fuzzy/both) + merge-safety guards.

## Context
With the five rules + polish (ADR/PR history through #15) landed, the next increment
Scott picked is **free-text extraction** — the long-deferred heavy one. `data/RECORDS.md`
deliberately excluded free-text at v0 *to protect the librarian rule*, so adding it is a real
architectural step, not a drop-in rule. Per the new-phase discipline (web-search → doc
→ plan), and to keep an over-docced repo lean, the full design + oracle + cited research
live in **Drive: `health-prototype/freetext-design`** (`DESIGN_freetext_extraction.md`,
`ORACLE_freetext_sample.md`, `RESEARCH_notes.md`). This ADR records the decision and the
open gate; it is intentionally thin.

## Decision
Adopt a **deterministic, stdlib-first extraction FRONT-END** that converts prose into the
engine's existing canonical record shape `{id, entries:[{date, item}]}`, consumed by the
five rules **unchanged**. Extraction is a front door to the librarian, not part of it.

- **Methods (web-checked, judged by concept — see `RESEARCH_notes.md`):** a curated
  domain-agnostic **gazetteer match** (exact default; fuzzy/synonym **reusing the engine's
  existing v1 layer**, opt-in) — the cTAKES/QuickUMLS dictionary path, *not* UMLS;
  **regex explicit-date extraction** (HeidelTime/SUTime family; relative dates deferred —
  they need an anchor date); rule-based **segmentation**; **char-offset provenance** on
  every `(date, item)`. Aho-Corasick/FlashText trie noted as the scale upgrade, not built first.
- **Librarian-rule stance (the crux — RESOLVED: Stance A, strict literal):** a gazetteer would
  extract `chest pain` from *"denies chest pain."* Deciding it's absent / hypothetical /
  non-patient is **interpretation — forbidden.** Resolution: **surface the literal mention +
  char-offset provenance**; the human/policy filters. Scott chose **Stance A (strict literal)**
  for slice 1 — every literal mention emitted, NO cue logic and NO `context_cue` field (Stance
  B's cue-tagging, DESIGN §2, is deferred). NegEx/ConText **assertion verdicts stay out of
  scope**; only their cue *lists* would be borrowed (as surfaced provenance) if B is ever
  adopted. Dates: **de-identified/shifted** posture (ADR 0009), default shift 0.
- **Home:** a new `extract.py` module (keep `recurrence.py` the pure librarian) +
  `tests/test_extract.py`, oracle-first. The engine + its 90 tests stay untouched.
- **Scope: slice 1 built.** The smallest shippable slice (DESIGN §6) is implemented in
  `extract.py`: a tiny curated gazetteer; explicit ISO + US + `Mon D YYYY` dates (no relative
  dates); exact, case-insensitive, word-bounded, longest-match gazetteer matching (one
  `(date, item)` per hit); canonical records + `source_span`; the consistent date shift; and a
  self-test/`--demo`. Fuzzy/synonym matching, relative dates, and multi-patient notes deferred.

Rejected for now: ML/NER models; NegEx/ConText assertion *verdicts*; a UMLS dependency;
relative-date normalization (all break determinism / stdlib-only / the librarian rule, or are
deferred to a later slice).

## Consequences
- A clear, low-risk path to the heavy feature without touching the proven engine.
- The negation/context line is named honestly as the one real risk; it gets a human
  decision *before* code, not after.
- Introduces ONE optional, additive entry field in slice 1 — `source_span` — that the rules
  ignore (same pattern as the carried `tag`, `data/RECORDS.md`), so no rule signatures change.
  `context_cue` is NOT emitted (it belonged to Stance B); a test asserts its absence.
- Until a slice ships, this stays `RESEARCH_ONLY` and surfaces nothing in the engine.

## Confirmation
- **Kickoff (RESEARCH_ONLY):** the design + a hand-written extraction oracle + cited research
  exist in Drive `health-prototype/freetext-design`; the engine was unchanged.
- **Slice 1 (IMPLEMENTED_UNVERIFIED, this branch):** `extract.py` + `tests/test_extract.py`
  (27 tests across 11 classes) prove extractor output equals the hand-written oracle
  (`FREETEXT_EXPECTED_RECORDS`, incl. exact char-offset spans); the extracted records feed
  `detect_recurrence` end-to-end (`poor sleep` ×2); `TestAllowlist` proves identifiers
  are un-extractable; `TestDateShiftDeIdentification` proves a shift preserves intervals;
  `TestLibrarianRuleBannedWords` asserts no banned interpretive words and no `context_cue`.
  `recurrence.py` and its 90 tests are untouched. `make check` green — 117 tests / self-test
  6+3 / `ruff` clean. Awaiting CONFIRMED_USER_SIDE (Scott runs it).
