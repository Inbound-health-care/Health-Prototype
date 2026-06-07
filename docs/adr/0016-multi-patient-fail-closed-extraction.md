# 0016 — Multi-patient free-text extraction (fail-closed identity, per-patient de-id)

**Date:** 2026-06-06
**Evidence level:** CONFIRMED_USER_SIDE — Scott ran `python extract.py --demo-multi` on his laptop
(2026-06-06). (`make check` green at merge: **207 tests** + self-test 6+10 + `ruff`; **3 Hypothesis
properties** green via `make proptest`.) The clinical-safety / de-identification claims stay
**RESEARCH_ONLY**. **Realizes the design specced (and deferred) in ADR 0013 "Rejected" +
`docs/COUNSEL_VERIFICATION_CHECKLIST.md` §Multi-patient — on SYNTHETIC data only.**
**Type:** Architecture / front-end / safety

## Context
Scott asked how the tool keeps one client's data from bleeding into another's. The engine is already
safe *per record* — `recurrence.run_report` groups every hit by `record_id` and every rule is strictly
per-record (co-occurrence is "two items in ONE record"), so nothing computes across records — and
`extract.extract_records` turns exactly one note into one record via the first `Patient:` header. The
"bleed" risk lives at the front door: the moment one input holds several patients and something must
decide attribution. That case was specced-but-deferred, naming **patient mis-attribution / record
bleed** as the dominant risk.

2026 research backs the approach (RESEARCH_ONLY; web; judge by concept): wrong-patient / note-mismatch
is a named, quantified clinical-safety problem (~0.3–0.5% mismatch; ~58 wrong-patient orders per
100k); "abstain under uncertainty / fail-closed" is established clinical-AI safety practice (ICLR 2026
*KNOWGUARD*; *Knowing When to Abstain* / MedAbstain) — our deterministic refuse-on-ambiguity **is**
abstention; and de-identification best practice is a consistent **per-patient** interval-preserving
date shift, where partial date-text de-id can re-enable date re-identification.

## Decision
A new `extract_records_multi(...)` in `extract.py` (single-note `extract_records` left untouched, no
engine change — `run_report` already handles N records):
- **Explicit delimiter only.** Split the input on an operator-supplied `delimiter` (required;
  `_validate_delimiter` raises on empty/whitespace — boundaries are never guessed). The preamble before
  the first delimiter is segment 0, never special-cased to attach to patient 1.
- **Fail-closed identity.** Per segment, find ALL `Patient:` headers (`parse_patient_ids` → values +
  whole-note offsets). Accept only when exactly **one distinct** key is present and that key does not
  collide with another segment; otherwise quarantine (refuse), never merge or guess. Four neutral
  reasons: `missing_key`, `ambiguous_key`, `duplicate_key`, `missing_shift`.
- **Duplicate key → quarantine ALL colliding segments** (incl. the first), never suffix/dedupe:
  `run_report` groups by `record_id`, so two records sharing an id would silently merge two patients —
  exactly the bleed. Refusing is abstention-under-uncertainty.
- **Per-patient de-id.** `shift_by_id: dict[str,int]` maps a raw key to its day offset; `require_shift`
  (default False) makes a missing shift a fail-closed `missing_shift` quarantine so de-identification
  can never be partial (the re-identification footgun the research names). Default keeps single-note
  parity (missing → 0).
- **Whole-note spans + provenance.** Reuse `extract_entries` per segment, then **rebase**
  `source_span`/`date_span` to whole-note offsets (preserves the repo-wide span contract used by the
  tests and `report_html`). Each accepted record carries an additive `provenance`
  `{segment_index, segment_span, patient_key_span}` the engine ignores (the `tag`/`source_span`
  precedent). Bad DATA never raises (fail-closed = quarantine); only bad CONFIG raises.
- **Property tests folded in** (the freshness-check pick): a dev-only Hypothesis module asserts the
  invariants on arbitrary generated batches (no-bleed + accounting; consistent-shift date invariance;
  single-segment reduces to `extract_records`). It SKIPS cleanly when hypothesis is absent, so
  `make test` / CI stay pure-stdlib; `make proptest` runs it via `uvx`. No runtime dependency.

**Rejected:** inferring identity from prose; suffix/dedupe on duplicate keys (that infers identity);
silent-0 shift under real de-id; auto-normalizing CRLF/BOM (would break the whole-note span contract —
the note is assumed `\n`-normalized and the delimiter is matched byte-literally); any engine change;
ML/NER.

## Consequences
- The product's safety claim ("separate clients, no bleed") is now real code + tested invariants, not
  just a per-record side-effect. One input → N correctly-keyed records; bad input degrades to
  quarantine, never mis-attribution.
- New function + helpers + fixtures + two test modules; `recurrence.py` / `extract_records` and their
  tests are untouched (additive). `VERSION` `0.3.0` → `0.4.0`; new `--demo-multi`.
- Foot-guns named as the human's responsibility (librarian framing): the operator picks a delimiter
  that can't occur in prose (a bad choice degrades to quarantine, not bleed); input is `\n`-normalized.
- Multi-patient **rendering** in the views (`report_html`/`digest_html`, single-note today) is a later
  slice. **The real-PHI counsel / Expert-Determination gate is UNCHANGED** — this is synthetic-data only.

## Confirmation
- `make check` green — **207 tests** (engine 90 + extract slice-1 27 + modes 27 + relative 15 +
  report_html 8 + digest 10 + multi 29 + 1 skipped property placeholder), self-test 6+10, `ruff`.
- `tests/test_extract_multi.py`: oracle (accepted records + quarantine reasons); the **no-bleed**
  invariant (every entry span ⊆ its segment; shared item → separate records; `run_report` never
  cross-attributes; no cross-patient co-occurrence; header-less preamble doesn't leak); duplicate-key
  quarantines ALL colliding (neither accepted); same-value-twice accepted; per-patient shift
  (intervals preserved / calendars differ / `require_shift` fail-closed / bool rejected); fail-loud
  config vs fail-closed data; refusal output banned-words-clean.
- `tests/test_extract_multi_properties.py` (Hypothesis, `make proptest`): 3 properties green over
  generated batches.
- `python extract.py --demo-multi` shows accepted records + the quarantine report; quarantined
  segments never reach `run_report`. `recurrence.py` + its 90 engine tests untouched.

## Sources (RESEARCH_ONLY; web; judge by concept, re-confirm before any real-PHI use)
- Patient-note mismatch / wrong-patient errors: PMC `PMC3128397`; ClinicalTrials `NCT02876588`.
- Abstain-under-uncertainty as a clinical-AI safety principle: ICLR 2026 *KNOWGUARD*; *Knowing When to
  Abstain* (MedAbstain), arXiv `2601.12471`.
- Per-patient date-shift de-id + partial-date re-identification: HIPAA Journal 2026 de-identification
  update; Accountable Expert-Determination guide; PMC `PMC9552287` (date-like-text re-identification).
