# Demo output — captured snapshots

Exact stdout from the project's demo commands, so a reviewer can see the value
without running anything. Everything here is pure stdlib, deterministic, and runs on
synthetic data (zero real PHI). Each block is a **regenerable snapshot** — re-run the
command in its heading and it should match byte-for-byte. Snapshot taken 2026-06-06.

---

## `python recurrence.py --report`

The combined per-record report: all five rules over the synthetic `SAMPLE_RECORDS`,
each line tagged with the lens that surfaced it. Records that surface nothing are
omitted — it lists what is present and never ranks, scores, or totals across records.

```text
Record R001:
  [recurrence] "poor sleep" recurred 3 times — 2026-01-05, 2026-02-10, 2026-03-12

Record R002:
  [recurrence] "appetite change" recurred 2 times — 2026-01-08, 2026-02-15
  [recurrence] "fatigue" recurred 2 times — 2026-02-02, 2026-03-01

Record R004:
  [recurrence] "back pain" recurred 2 times — 2026-01-15, 2026-02-20

Record R005:
  [recurrence] "anxiety" recurred 4 times — 2026-01-03, 2026-01-31, 2026-02-28, 2026-03-30

Record R008:
  [recurrence] "medication review" recurred 2 times — 2026-01-18, 2026-02-22

Record R009:
  [recurrence] "med refill: metformin" recurred 3 times — (undated), 2026-01-07, 2026-03-09

Record R010:
  [recurrence] "edema" recurred 2 times — 2026-01-11, 2026-02-13

Record R011:
  [recurrence] "lab: A1C" recurred 3 times — 2026-01-06, 2026-02-09, 2026-03-20

Record R012:
  [recurrence] "blood pressure elevated" recurred 12 times — 2026-01-04, 2026-02-04, 2026-03-04, 2026-04-04, 2026-05-04, 2026-06-04, 2026-07-04, 2026-08-04, 2026-09-04, 2026-10-04, 2026-11-04, 2026-12-04

Record R013:
  [recurrence] "housing instability" recurred 2 times — 2026-01-22, 2026-02-26

Record R015:
  [recurrence] "depression" recurred 3 times — 2026-01-10, 2026-09-10, 2026-10-05
  [gap] "depression" returned after 243 days — last seen 2026-01-10, then 2026-09-10

Record R016:
  [recurrence] "chest pain" recurred 4 times — 2026-02-01, 2026-02-10, 2026-02-20, 2026-05-10
  [frequency] "chest pain" appeared 3 times within 19 days — 2026-02-01, 2026-02-10, 2026-02-20
  [cadence_change] "chest pain" interval changed from ~10d to ~79d at 2026-02-20 — 2026-02-01, 2026-02-10, 2026-02-20, 2026-05-10

Record R017:
  [recurrence] "knee pain" recurred 2 times — 2026-01-10, 2026-02-14
  [recurrence] "poor sleep" recurred 2 times — 2026-01-10, 2026-02-14
  [cooccurrence] "knee pain" + "poor sleep" co-occurred 2 times — 2026-01-10, 2026-02-14

Record R018:
  [recurrence] "dizziness" recurred 2 times — 2026-03-01, 2026-04-01
  [recurrence] "fatigue" recurred 2 times — 2026-03-01, 2026-04-01
  [recurrence] "nausea" recurred 2 times — 2026-03-01, 2026-04-01
  [cooccurrence] "dizziness" + "fatigue" co-occurred 2 times — 2026-03-01, 2026-04-01
  [cooccurrence] "dizziness" + "nausea" co-occurred 2 times — 2026-03-01, 2026-04-01
  [cooccurrence] "fatigue" + "nausea" co-occurred 2 times — 2026-03-01, 2026-04-01

Record R019:
  [recurrence] "cough" recurred 2 times — 2026-01-05, 2026-02-05
  [recurrence] "rash" recurred 2 times — 2026-01-20, 2026-02-20

Record R020:
  [recurrence] "back pain" recurred 2 times — 2026-01-12, 2026-03-22
  [recurrence] "edema" recurred 2 times — 2026-01-12, 2026-03-18
```

Note `R009` cites an `(undated)` occurrence rather than hiding it, and `R016`
surfaces under three lenses at once (recurrence + frequency + cadence change) — one
record, several views, never a merged judgment.

---

## `python extract.py --demo`

Free-text prose → canonical records → the engine, under **strict** (exact, literal,
whole-word) matching. Note `chest pain` surfaces from *"Denies chest pain"*: Stance A
emits the literal mention with its source span and lets a human judge relevance — it
carries no negation logic. `source_span` is `@[start, end]` character offsets into the
note.

```text
Matching mode: strict
Source note:
Patient: EXAMPLE-001

2026-01-05 Reports poor sleep x3 weeks. Denies chest pain.
2026-02-10 Poor sleep continues. Headache today.
2026-03-12 Sleep improved. Notes family history of insomnia.

Extracted entries (literal mentions, cited — not interpreted):
  2026-01-05  "poor sleep"  @[41, 51]
  2026-01-05  "chest pain"  @[69, 79]
  2026-02-10  "poor sleep"  @[92, 102]
  2026-02-10  "headache"  @[114, 122]
  2026-03-12  "sleep"  @[141, 146]
  2026-03-12  "insomnia"  @[181, 189]

Fed to the engine (detect_recurrence), it surfaces:
  "poor sleep" appears 2x — 2026-01-05, 2026-02-10
```

---

## `python extract.py --demo --match-mode fuzzy`

The same note under **fuzzy** matching. Here the output is **identical** to strict —
every mention in this note is already an exact gazetteer hit, so there is nothing for
fuzzy to merge. Fuzzy diverges only when a near-miss spelling (a typo or look-alike)
appears, and even then it is guarded (affix-antonym detector + look-alike denylist +
gazetteer anchoring). See `data/RECORDS.md` §5 and `tests/test_fuzzy.py` for the cases
where fuzzy actually changes the result.

```text
Matching mode: fuzzy
Source note:
Patient: EXAMPLE-001

2026-01-05 Reports poor sleep x3 weeks. Denies chest pain.
2026-02-10 Poor sleep continues. Headache today.
2026-03-12 Sleep improved. Notes family history of insomnia.

Extracted entries (literal mentions, cited — not interpreted):
  2026-01-05  "poor sleep"  @[41, 51]
  2026-01-05  "chest pain"  @[69, 79]
  2026-02-10  "poor sleep"  @[92, 102]
  2026-02-10  "headache"  @[114, 122]
  2026-03-12  "sleep"  @[141, 146]
  2026-03-12  "insomnia"  @[181, 189]

Fed to the engine (detect_recurrence), it surfaces:
  "poor sleep" appears 2x — 2026-01-05, 2026-02-10
```

---

## `python extract.py --demo-multi`

A synthetic **multi-patient batch** split on an explicit delimiter (`\n---\n`), extracted
**fail-closed on identity** (ADR 0016): a segment is accepted only when it carries exactly one
distinct `Patient:` key that no other segment shares — everything else is **quarantined
(refused), never merged or guessed**. Accepted records are de-identified by a per-patient date
shift (EXAMPLE-002's dates are shifted here); the quarantined segments **never reach the
engine**. Quarantine reasons are fixed neutral tokens — the librarian rule holds in the refusal output.

```text
Source note (multi-patient batch):
2026-01-01 headache noted in triage.

---
Patient: EXAMPLE-001
2026-01-05 poor sleep.
2026-02-10 poor sleep.

---
Patient: EXAMPLE-002
2026-01-06 poor sleep.
2026-02-12 poor sleep.
2026-02-20 headache.

---
2026-03-01 headache.

---
Patient: EXAMPLE-003
Patient: EXAMPLE-004
2026-03-05 poor sleep.

---
Patient: EXAMPLE-005
2026-03-08 poor sleep.

---
Patient: EXAMPLE-005
2026-03-09 headache.

Explicit delimiter: '\n---\n'

Accepted records (cited, de-identified, fail-closed on identity):
  EXAMPLE-001  (segment 1)
    2026-01-05  "poor sleep"  @[74, 84]
    2026-02-10  "poor sleep"  @[97, 107]
  EXAMPLE-002  (segment 2)
    2053-05-24  "poor sleep"  @[146, 156]
    2053-06-30  "poor sleep"  @[169, 179]
    2053-07-08  "headache"  @[192, 200]

Quarantined segments (refused — neutral provenance only):
  segment 0 @offset 0: missing_key (no Patient: header)
  segment 3 @offset 207: missing_key (no Patient: header)
  segment 4 @offset 233: ambiguous_key (2 distinct headers)
  segment 5 @offset 303: duplicate_key (key shared across segments)
  segment 6 @offset 352: duplicate_key (key shared across segments)

Fed to the engine (run_report) — quarantined segments never reach it:
Record EXAMPLE-001:
  [recurrence] "poor sleep" recurred 2 times — 2026-01-05, 2026-02-10

Record EXAMPLE-002:
  [recurrence] "poor sleep" recurred 2 times — 2053-05-24, 2053-06-30
```

## `python audit.py --demo`

Deterministic (fixed demo clock): the audited multi-extract + report over the
sample data, the chain verdict, the externally publishable head, and the
monitor's counts. Digests + counts only — no clinical text (ADR 0030).

```
audit trail demo (synthetic records; digests and counts only)
  seq 1  2026-06-11T00:00:00Z  extract_multi  records 2, entries 5
  seq 2  2026-06-11T00:00:01Z  report  records 16
chain: intact (2 entries)
head: af179c03461be69b69c847bd41c968729d37ba4539b07491e21568a41988fafc

audit summary
  events: 2 (extract_multi 1, report 1)
  findings by lens: cadence_change 1, cooccurrence 4, frequency 1, gap 1, recurrence 22
  quarantined by reason: ambiguous_key 1, duplicate_key 2, missing_key 2
```
