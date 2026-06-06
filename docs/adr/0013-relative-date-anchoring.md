# 0013 — Relative-date anchoring (opt-in, conservative) in the free-text front-end

**Date:** 2026-06-05
**Evidence level:** IMPLEMENTED_UNVERIFIED — CONFIRMED_ASSISTANT_SIDE (`make check` green:
159 tests / self-test 6+10 / `ruff` clean); promotes to CONFIRMED_USER_SIDE when Scott runs it.
The clinical-NLP grounding and the de-identification notes below are **RESEARCH_ONLY** (web-sourced,
not counsel-verified). Refines ADR 0008's deferred "relative dates" item.
**Type:** Architecture / front-end / safety

## Context
All five surfacing rules are date-driven (`recurrence._record_groups` parses ISO dates; undated
entries are dropped). The free-text front-end `extract.py` resolved only **explicit** dates
(`_parse_leading_date`), so relative clinical prose — "since last visit", "3 weeks ago", "q2wk" —
never entered the canonical `(date, item)` stream. Psychiatric notes are saturated with relative
time, so this was the binding constraint on a single-patient behavioral-health "pre-visit pattern
digest" (ADR 0011).

Research (RESEARCH_ONLY; judge by concept): this is **temporal-expression normalization** (the
TIMEX3 / TimeML standard); the dominant production taggers (HeidelTime, SUTime) are **rule-based**
and resolve relative expressions against a **reference date**. The arithmetic is trivial; the
literature's hard part is **anchor SELECTION** — relative/incomplete TIMEXes are ~26% of clinical
TIMEXes and the best 2012 i2b2 systems normalized them at only ~0.32 (vs ~0.67 overall); guessing a
default anchor caps accuracy near ~59%. The lesson: resolve confidently only when the anchor is
explicit/adjacent; otherwise do not guess.

## Decision
**Opt-in and OFF by default** (mirrors ADR 0012's "explicit, must-be-chosen"): `resolve_relative=False`
keeps output **byte-for-byte** the slice-1/2 behavior. Enabling it adds a relative pass with four
buckets, anchored to the line's leading explicit date if present, else a caller-supplied
`reference_date`:
- **resolved** — `"<N> day|week|month|year(s) ago|prior|earlier"`, `"(for the past|past) <N> <unit>"`,
  `"since <explicit-date>"` → a full ISO date (`date_kind="relative"`).
- **partial** — `"<MonthName> <Year>"` → `date=""`, surfaced + cited (no fabricated day).
- **frequency** — `"q2wk"`, `"bid"`, `"every N weeks"`, … → `date=""`, surfaced + cited, **never**
  expanded into invented event dates.
- **unresolved** — a relative phrase with no available anchor → `date=""`, cited, **never guessed**.

Non-explicit entries carry three **additive** provenance fields — `date_kind`, `date_phrase`,
`date_span` — alongside `date/item/source_span`. The rules read only `date`/`item` (they already
ignore extras like `source_span`/`tag`), so **`recurrence.py` and its 90 tests are untouched**.
Resolved dates are date-shifted with everything else, so a constant per-record shift cancels and all
intervals are invariant (ADR 0009). Pure stdlib (`re` + `datetime` + `calendar` for month-day
clamping). A **leading-token** model is used (consistent with the existing leading-date contract);
the phrase→item association on a line is **co-location only**, with the phrase cited — no
interpretation, banned-word tests hold in this path too.

**Rejected (for now):** ML/NER; `ctparse` (ships a pre-trained model); `dateparser`/`dateutil`
(non-stdlib deps); **heuristic implicit-anchor selection** (the ~59% ceiling means guessed anchors
buy recall at the cost of *silently wrong* dates — a false pattern, the ADR 0011 liability);
partial-date → `YYYY-MM` normalization (deferred — we cite the literal and leave `date=""`);
mid-line (non-leading) temporal expressions; multi-patient input (see
`docs/COUNSEL_VERIFICATION_CHECKLIST.md` for its specced fail-closed design).

## Consequences
- Relative clinical prose now enters the engine for the explicitly-anchored cases; everything else is
  surfaced honestly (cited, undated) rather than dropped or guessed.
- New entry fields are additive/optional; any consumer reading only `date`/`item` is unaffected.
- `extract.py` `VERSION` 0.2.0 → 0.3.0; new `--reference-date` demo.
- Pitfalls deliberately left to the human (per the librarian rule): a resolved date can still sit on a
  negated/hypothetical/historical mention (the ConText problem) — the cited `source_span` is how a
  human sees the qualifier.

## Confirmation
- `make check` green — **159 tests** (engine 90 + extract slice-1 27 + modes 27 + relative 15),
  self-test 6+10, `ruff` clean. `TestRelativeDateAnchoring` proves: oracle match; **default-off is
  byte-for-byte**; weeks-ago resolves against the anchor; month subtraction clamps the day (never
  raises); since-date resolves without an anchor; frequency is surfaced but never dated; partial is
  undated; an anchorless relative is **unresolved, not guessed**; spans recover both the phrase and the
  item text; the date shift preserves the relative/explicit interval; records feed `detect_recurrence`
  unchanged; banned words hold; and validation raises on incoherent inputs.
- Clinical-NLP + de-id claims stay **RESEARCH_ONLY** pending primary-source + counsel verification.

## Sources (RESEARCH_ONLY, web; judge by concept)
- TIMEX3 / TimeML; HeidelTime (rule-based temporal tagger). https://github.com/HeidelTime/heideltime
- SUTime (deterministic rule-based; resolves relatives against the document date). https://stanfordnlp.github.io/CoreNLP/sutime.html
- Sun, Rumshisky, Uzuner, "Normalization of relative and incomplete temporal expressions in clinical
  narratives," JAMIA 2015 (anchor point + anchor relation; RI-TIMEX shares; ~0.32 vs ~0.67; ~59%
  admission-default ceiling). https://arxiv.org/abs/1510.04972
- 2012 i2b2 temporal-relations challenge. https://pmc.ncbi.nlm.nih.gov/articles/PMC3756273/
- THYME corpus / DocTimeRel. https://pmc.ncbi.nlm.nih.gov/articles/PMC5657277/
- ConText (negation / hypothetical / historical / experiencer). https://pubmed.ncbi.nlm.nih.gov/19435614/
- Truncate-and-Shift / interval-preserving de-identification. https://pmc.ncbi.nlm.nih.gov/articles/PMC5070517/
- Re-identification from residual date-like text. https://pmc.ncbi.nlm.nih.gov/articles/PMC9552287/
