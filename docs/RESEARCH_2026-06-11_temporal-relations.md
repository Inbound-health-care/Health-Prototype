# Research — deterministic temporal-relation surfacing (Stage 2) (2026-06-11) — RESEARCH_ONLY

**Status: RESEARCH_ONLY.** Web research for **Stage 2 of ADR 0029** (deterministic temporal-relation
surfacing + fuller per-record timelines in `recurrence.py`), per the new-phase discipline: search
first, document, then build. Nothing here is project truth until the Stage-2 tests prove the parts we
adopt (`DOC_DISCIPLINE.md` §Research gate). The build is deferred to a fresh session (Scott's
~600k-token re-lock heuristic); this note + the ADR 0029 Stage-2 addendum are the durable handoff.

## What was researched (web, 2026-06-11; judge by concept)

The engine consumes records of **day-dated POINT events** (`{"date":"YYYY-MM-DD","item":...}`). Stage 2
surfaces the temporal RELATIONS between those events and builds a fuller per-record timeline — factual
sequence only, never causation (the librarian rule).

1. **Allen's interval algebra → point algebra.** Allen's 13 interval relations degenerate to **3**
   for instantaneous events (before / equal / after — Vilain & Kautz point algebra). For day-dated
   points that is the whole qualitative vocabulary. "Within-window/near" is a **metric** extension
   (Dechter–Meiri–Pearl Simple Temporal Networks: a bound `dateB − dateA ≤ δ` in integer days) — pure
   arithmetic, stdlib-trivial, no constraint solver needed for adjacent pairs.
2. **Clinical relation standards.** THYME corpus (ISO-TimeML for clinical text) and the i2b2-2012
   temporal challenge standardize on **BEFORE / AFTER / OVERLAP** (THYME's dominant CONTAINS is for
   *narrative* interval-in-interval time and is **irrelevant** when both endpoints are explicit dates).
   HL7 FHIR has no point-relation vocabulary to borrow. → adopt **BEFORE / AFTER / SAME_DAY** +
   the metric **WITHIN_WINDOW(days)**.
3. **Timeline value (verified, with the claim corrected).** The source doc's "supports rare-disease
   diagnosis and care coordination" is **real by concept but must be reworded**: timelines help by
   *evidential accumulation / weak-signal surfacing* over a longitudinal window, **not** by temporal
   inference and **not** causally (medRxiv 2026 rare-disease set-to-sequence work; IRDiRC diagnostic-
   odyssey data). Cite as "surfaces the cited-date sequence for a human to read," never "diagnoses."
4. **Determinism pitfalls.** (a) **Same-day tie-break** needs an explicit, documented rule (events
   sharing a date have no intrinsic order) — adopt a deterministic, NON-interpretive tie-break:
   document order, then item string, with the date as primary key. NOT clinical event-type precedence
   (that would be interpretation). (b) **Undated entries** are excluded from the ordered axis and
   surfaced separately as "undated," never interleaved (mirrors the relative-date "cited but undated"
   stance, ADR 0013). (c) **Closure explosion:** emitting all transitive pairs is O(n²) and floods
   output; real systems emit **adjacent pairs only** (sorted, O(n log n)) and filter on demand. Adopt
   adjacent-pair only.
5. **Sequence ≠ causality (the librarian boundary).** The post-hoc fallacy is the central risk:
   temporal proximity is necessary-not-sufficient for causation, and clinical LLMs routinely conflate
   the two. The antidote is structural: output dates + interval-days + relation token + citations, use
   **before/after** never **causes/leads-to/due-to**, and the existing banned-words gate already
   forbids the interpretive vocabulary. A fixed "sequence, not causation" caveat belongs in any Stage-2
   view.

## What this means for the build (folded into ADR 0029 Stage-2 addendum)
- Relation vocabulary: **BEFORE / AFTER / SAME_DAY / WITHIN_WINDOW(days)** over day-dated points.
- **Adjacent-pair only**, sorted by (date, document-order, item) — a documented, non-interpretive
  tie-break; pure stdlib (`datetime`), deterministic, oracle-pinned.
- Undated entries surfaced separately ("undated"), never placed on the ordered axis.
- **Opt-in lens** (Scott's call): a new `build_timeline` / `format_timeline` API + a separate opt-in
  registry or `--report-timeline` so the default `--report` stays clean (an adjacent-sequence lens
  would otherwise fire on nearly every record and flood the report — unlike the 5 pattern rules).
- Librarian-safe: dates/intervals/citations only; banned-words gate enforced; fixed sequence-not-
  causation caveat in any view.

## Sources (RESEARCH_ONLY, web; primary where reachable)
- Allen's interval algebra (NP-complete full algebra). https://en.wikipedia.org/wiki/Allen%27s_interval_algebra
- Dechter, Meiri & Pearl, "Temporal constraint networks," Artif. Intell. 49 (1991). https://www.sciencedirect.com/science/article/abs/pii/0004370291900066
- THYME / clinical TimeML annotation (Styler et al., TACL 2014). https://aclanthology.org/Q14-1012/
- i2b2 2012 temporal relations challenge. https://pmc.ncbi.nlm.nih.gov/articles/PMC3756273/
- Temporal reasoning over clinical text — state of the art. https://pmc.ncbi.nlm.nih.gov/articles/PMC3756277/
- Rare-disease early detection via structured-EHR sequence modeling (medRxiv 2026). https://www.medrxiv.org/content/10.64898/2026.05.04.26352393v1.full
- IRDiRC diagnostic-odyssey time-to-diagnosis. https://link.springer.com/article/10.1186/s13023-024-03319-2
- "Being honest with causal language in writing for publication." https://onlinelibrary.wiley.com/doi/10.1111/jan.14311
- "LLMs Are Prone to Fallacies in Causal Inference" (arXiv 2406.12158). https://arxiv.org/pdf/2406.12158
