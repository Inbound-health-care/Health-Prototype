# 0012 — Free-text matching modes (strict / synonyms / fuzzy / both) + merge-safety guards

**Date:** 2026-06-05
**Evidence level:** IMPLEMENTED_UNVERIFIED — slice shipped on `claude/hopeful-albattani-sYkkR`:
`extract.py` modes + guards + `tests/test_extract_modes.py`. CONFIRMED_ASSISTANT_SIDE
(`make check` green — 144 tests / self-test 6+7 / `ruff` clean); promotes to
CONFIRMED_USER_SIDE when Scott runs it. The legal/market reasoning below is **RESEARCH_ONLY**
(web-sourced, not counsel-verified). Refines ADR 0008's deferred "fuzzy/synonym" item.
**Type:** Architecture / safety / front-end

## Context
Free-text slice 2 adds synonym/fuzzy matching to the extractor (`extract.py`) so it catches
paraphrase and typos — recall the behavioral-health "pre-visit pattern digest" (ADR 0011) needs.
But matching is **fragile** in clinical text, and the prior design (Drive `freetext-design`) waved
it through as a safe "reuse the engine's v1 layer, opt-in" drop-in. Research says otherwise — two
classes of pairing that string-similarity silently fuses:

- **Affix antonyms** — one morpheme flips meaning at a *high* `difflib` ratio: `hypertension`↔
  `hypotension`, `hyper/hypoglycemia`, `compliant`↔`noncompliant`, `symptomatic`↔`asymptomatic`,
  `tachy`↔`brady`.
- **Look-alike/sound-alike (LASA) drug names** — ISMP catalogs ~528 confusable pairs
  (`bupropion`/`buspirone`, `clonazepam`/`clonidine`/`clobazam`, …).

The repo had **no merge-safety guard** at all. Scott reframed the work: rather than bake one
fuzzy/synonym behavior in, make matching an **explicit, named mode the user must consciously
choose**, ship the *mechanism + guards + tiny examples*, and let clinical users supply their own
vocabulary (domain-agnostic / minimal). He asked whether forcing an explained, opt-in choice helps
the liability posture.

## Decision

**Four matching modes via a `MatchConfig` (default = `strict`):**
- `strict` — exact, case-insensitive, whole-word, longest-match (slice-1 behavior, unchanged).
- `synonyms` — strict + a curated `{variant -> canonical}` map the **caller** supplies.
- `fuzzy` — strict + `difflib` near-match of text against gazetteer terms above a caller cutoff,
  **guarded**.
- `both` — synonyms + fuzzy together (guards still apply).

`MatchConfig.__post_init__` **forces a coherent, explicit choice**: a mode requires its inputs and
*rejects* mismatched ones (a `strict` config with a synonyms map raises; `fuzzy` needs a cutoff).
You cannot smuggle looser matching past a strict default — it is opt-in by construction.

**Merge-safety guards, always on in fuzzy/both** (`extract.py`):
- A general **affix-swap detector** (`_is_affix_antonym`) — blocks a near-match whose strings are
  equal after toggling a meaning-flipping affix (`hyper`/`hypo`, `tachy`/`brady`, negators
  `un/non/a/...`). Domain-agnostic string morphology, not a clinical vocabulary. Deliberately
  over-inclusive (a blocked borderline pair only costs recall; a wrong merge is a false pattern).
- An explicit **`anti_pairings` denylist** of unordered pairs (seed `DEFAULT_ANTI_PAIRINGS` carries
  ONE illustrative LASA pair + a pointer to the ISMP list; deployments extend it).
- A **drug-name exemption** (`no_fuzzy_terms`) — listed terms never fuzzy-match.
- Declared synonyms are validated too: an affix-antonym synonym (`stable -> unstable`) is refused.

Fuzzy is **anchored to the gazetteer** (text windows are compared only against allowlisted terms),
so only curated concepts ever surface — the HIPAA allowlist (ADR 0009) holds under fuzzy. Matching
reuses the engine's v1 primitives (`recurrence._normalize`, `_check_fuzzy_cutoff`, `difflib`) so
"canonical" means the same thing on both sides; `recurrence.py` and its 90 tests are untouched.

**Vocabulary is domain-agnostic / minimal:** the repo ships the mechanism + guards + tiny
illustrative fixtures (`FREETEXT_SYNONYMS`, `DEFAULT_ANTI_PAIRINGS`), not a real clinical lexicon.

**Liability reasoning (RESEARCH_ONLY).** Forcing an explained, opt-in choice *helps* but does **not
waive** exposure. It supports a learned-intermediary "the clinician configures/validates the
settings" defense and FDA Non-Device **criterion 4** transparency (the 2026 CDS final guidance
raises the bar on documenting algorithmic logic) — **only because** it is paired with a safe default
(strict) and guards that stay active even in fuzzy/both, so we are not shipping a foreseeably
dangerous *unguarded* mode. Strict product liability can attach regardless of the clinician's role,
so the modes are framed as a **transparency / human-control mitigation, not a shield** (consistent
with ADR 0011: "surface-only is not tort immunity; mitigation is UX"). `--explain-modes` states the
risk in plain language at the point of choice.

**Distinct from ADR 0009's "no denylist."** That rejected a denylist of *PHI identifiers* (an
allowlist is safer for *what text may surface at all*). This is a *merge*-safety denylist (a
bounded, enumerable set of dangerous fusions). Complementary, not contradictory.

Rejected for now: a baked clinical synonym/LASA vocabulary (deferred to deployments — minimal);
auto-generated synonyms; fuzzy clustering of arbitrary text not anchored to the gazetteer.

## Consequences
- Defaults stay exact: `strict` reproduces the slice-1 oracle **byte-for-byte** (a regression test
  proves it), so nothing changes unless a mode is deliberately chosen.
- The one genuinely new algorithm is fuzzy token-windowing; the open risk is noise. If it proves
  noisy, fall back to single-token fuzzy first (recorded; not needed by the current oracle).
- The engine is untouched; the extractor's one-way dependency on `recurrence.py` is reused, not widened.
- `extract.py` `VERSION` → 0.2.0.

## Confirmation
- `make check` green — **144 tests** (engine 90 + extract slice-1 27 + modes 27), self-test 6+7,
  `ruff` clean. `tests/test_extract_modes.py` proves: strict == slice-1 oracle (safe default);
  synonyms remap to a hand-written oracle and lift the recurrence count 2→3; fuzzy merges a typo but
  **blocks** `hypertension`/`hypotension` and a denylisted look-alike, and honors the drug-name
  exemption; `both` composes; `MatchConfig` validation raises on every incoherent choice; the
  librarian-rule banned-words hold in **every** mode; `--explain-modes` documents the modes + the risk.
- Legal/market claims stay **RESEARCH_ONLY** pending primary-source + counsel verification before any
  real-PHI use.

## Sources (RESEARCH_ONLY, web; judge by concept)
- ISMP List of Confused Drug Names (LASA): https://home.ecri.org/blogs/ismp-resources/list-of-confused-drug-names
- WHO LASA patient-safety solution: https://cdn.who.int/media/docs/default-source/patient-safety/patient-safety-solutions/ps-solution1-look-alike-sound-alike-medication-names.pdf
- SNOMED CT synonymy (vetting reference, not a runtime dep): https://pmc.ncbi.nlm.nih.gov/articles/PMC3900203/
- Learned-intermediary + user-configuration defense for medical software: https://csattorneys.com/2025/07/29/when-software-fails-due-to-configuration-errors-defending-medical-software-developers-against-misplaced-liability/
- FDA 2026 CDS final guidance (transparency / criterion 4): https://www.faegredrinker.com/en/insights/publications/2026/1/key-updates-in-fdas-2026-general-wellness-and-clinical-decision-support-software-guidance
- Product liability can attach despite clinician role (EU/strict liability): https://link.springer.com/chapter/10.1007/978-94-6265-639-0_2
- Enhanced active / forced choice (no silent default): https://www.cmu.edu/dietrich/sds/docs/loewenstein/EnhancedActiveChoice.pdf
