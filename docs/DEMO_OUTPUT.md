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
```
