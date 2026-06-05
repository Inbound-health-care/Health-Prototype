# 0008 — Free-text extraction: design kickoff (deterministic front-end)

**Date:** 2026-06-05
**Evidence level:** RESEARCH_ONLY — design + research only; nothing built. Promotes
when a first slice ships with a passing oracle test (→ IMPLEMENTED_UNVERIFIED →
CONFIRMED_*).
**Type:** Architecture / kickoff

## Context
With the five rules + polish (ADR/PR history through #15) landed, the next increment
Scott picked is **free-text extraction** — the long-deferred heavy one. `data/RECORDS.md`
deliberately excluded free-text at v0 *to protect the firewall*, so adding it is a real
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
- **Firewall stance (the crux — OPEN for Scott):** a gazetteer would extract `chest pain`
  from *"denies chest pain."* Deciding it's absent / hypothetical / non-patient is
  **interpretation — forbidden.** Resolution: **surface the literal mention + provenance,
  and surface negation/context CUES as cited evidence**, never as a verdict; the
  human/policy filters. NegEx/ConText **cue lists** are borrowed as provenance; their
  **assertion verdicts are out of scope.** Two stances (A strict-literal / B cue-tagged)
  in DESIGN §2 — **Scott decides at go/no-go.**
- **Home:** a new `extract.py` module (keep `recurrence.py` the pure librarian) +
  `tests/test_extract.py`, oracle-first. The engine + its 90 tests stay untouched.
- **Scope this round = design only.** No extractor code. The first-slice scope is written
  down (DESIGN §6) for Scott to approve before any build.

Rejected for now: ML/NER models; NegEx/ConText assertion *verdicts*; a UMLS dependency;
relative-date normalization (all break determinism / stdlib-only / the firewall, or are
deferred to a later slice).

## Consequences
- A clear, low-risk path to the heavy feature without touching the proven engine.
- The negation/context line is named honestly as the one real risk; it gets a human
  decision *before* code, not after.
- Introduces optional, additive entry fields (`source_span`, `context_cue`) the rules
  ignore — same pattern as the carried `tag` (`data/RECORDS.md`), so no rule signatures change.
- Until a slice ships, this stays `RESEARCH_ONLY` and surfaces nothing in the engine.

## Confirmation
- **Now:** the design + a hand-written extraction oracle + cited research exist in Drive
  `health-prototype/freetext-design`; the engine is unchanged (`make check` still 90 tests
  / self-test 6 / `ruff` clean on this branch).
- **On first slice (future):** `tests/test_extract.py` proves extractor output equals the
  hand-written oracle; the extracted records feed the existing rule oracles end-to-end; a
  firewall test asserts no banned interpretive words and that cues are surfaced as cited
  text, never as verdicts. Only then does this promote off `RESEARCH_ONLY`.
