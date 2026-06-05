# Health-Prototype

**Recurrence Detection Engine — Prototype v0.** The smallest function that
attacks the root surfacing gap: systems *store* everything but *surface* almost
nothing useful at the moment of need.

## What it does

Given a set of records, `detect_recurrence` surfaces every case where the same
item appears across multiple dated entries, and cites exactly where each
occurrence came from.

It is a **librarian, not an interpreter**. It surfaces, counts, and cites
provenance — it never scores, ranks, or diagnoses, and it never says what a
pattern *means*. That separation is the design principle and the legal firewall
in one.

Domain-agnostic by design: a record can be a patient, a pharmacy profile, or a
session log — the engine does not care. Pure stdlib, local-only, placeholder
data only (zero real PHI).

## Record shape

```python
record = {
    "id": "R001",
    "entries": [
        {"date": "2026-01-10", "item": "poor sleep"},   # ISO 8601 date
        {"date": "2026-02-02", "item": "poor sleep"},
        {"date": "2026-02-20", "item": "appetite change"},
    ],
}
```

## The function

```python
def detect_recurrence(records: list, field: str = "item", min_count: int = 2) -> list[RecurrenceHit]:
    """Return recurrence hits. Each hit cites the record id, the item, the
    count, and the dates it appeared on. Surfaces only — no interpretation."""
```

Each hit reports the **record ID**, the **recurring item**, the **count**, and
the **exact dates** it appeared on (provenance). Rendered output line:

```text
Record R001: "poor sleep" recurred 2 times — 2026-01-10, 2026-02-02
```

## Running it

```bash
python recurrence.py --self-test                  # run the six required spec cases
python recurrence.py --demo                        # recurrence, v0 exact match
python recurrence.py --demo-v1                      # recurrence, v1 opt-in matching
python recurrence.py --demo-gap                     # gap / re-emergence rule
python recurrence.py --demo-frequency               # frequency / burst rule
python recurrence.py --demo-cooccurrence            # co-occurrence rule (same date)
python recurrence.py --demo-cooccurrence-window     # co-occurrence within a 7-day window (opt-in)
python recurrence.py --report                        # combined per-record report (all rules)
make check                                           # full local verification (tests + self-test + lint)
python -m unittest discover -s tests -t .          # full test suite (from repo root)
```

The placeholder record set lives in `data/sample_records.py` (records +
hand-written `ANSWER_KEY`, side by side). Each record exists for one documented
reason and the answer key is written first; `--demo` and the test suite confirm
the engine surfaces exactly those patterns. The full design rationale, field
dictionary (grounded in 2026 USCDI/FHIR/SDOH standards), per-record reasons, and
the v0 limitations each record demonstrates are in
[`data/RECORDS.md`](data/RECORDS.md).

## Surfacing rules

The engine surfaces patterns through independent rules that all read the same
grouped occurrences (so they share the matching behavior below). Each surfaces,
counts, and cites — none interprets.

| Rule | Function | Question it answers |
|---|---|---|
| Recurrence | `detect_recurrence` | Has the same item come up repeatedly (≥ `min_count`)? |
| Gap / re-emergence | `detect_gap` | Did an item return after a long absence (> `gap_days`)? |
| Frequency / burst | `detect_frequency` | Did an item cluster (`min_count`+ within `window_days`)? |
| Co-occurrence | `detect_cooccurrence` | Did two items show up together — the same date, or within an opt-in `window_days` — on ≥ `min_count` dates? |

One record can surface under several rules — see [`data/RECORDS.md`](data/RECORDS.md)
§7 for the gap/frequency walkthrough and their hand-written answer keys.

### Combined report — all rules, one per-record view

`run_report` (CLI `--report`) runs all four rules over one record set and groups
every finding under its record, each line tagged with the lens that surfaced it.
(The report uses each rule's defaults, so co-occurrence there is same-date; the
`window_days` variant is opt-in via `detect_cooccurrence` / `--demo-cooccurrence-window`.)
Records that surface nothing are omitted — it lists what is present, and it never
ranks, scores, totals, or prioritizes records.

```text
Record R015:
  [recurrence] "depression" recurred 3 times — 2026-01-10, 2026-09-10, 2026-10-05
  [gap] "depression" returned after 243 days — last seen 2026-01-10, then 2026-09-10

Record R016:
  [recurrence] "chest pain" recurred 4 times — 2026-02-01, 2026-02-10, 2026-02-20, 2026-05-10
  [frequency] "chest pain" appeared 3 times within 19 days — 2026-02-01, 2026-02-10, 2026-02-20
```

## Matching: exact by default, fuzzy when asked

**The default is exact match** — same meaning in different words is *not*
combined, so v0 stays simple and provable.

**v1 adds three opt-in matching layers** to `detect_recurrence` (defaults keep
exact v0 behavior, so nothing regresses):

```python
detect_recurrence(records, normalize=True, synonyms={"insomnia": "poor sleep"}, fuzzy_cutoff=0.85)
```

- `normalize=True` — case-fold + trim + collapse whitespace.
- `synonyms={variant: canonical}` — merge declared synonyms. The mapping is data
  **you** supply; the engine never infers meaning. This is the only way to unite
  truly dissimilar synonyms like "insomnia" = "can't sleep".
- `fuzzy_cutoff=0.0–1.0` — also merge lookalikes/typos via stdlib `difflib`. This
  is the one layer where the engine groups without a declared rule, so it is off
  by default.

**The firewall holds.** Whenever entries with different spellings are combined,
the hit cites every original via `variants`, and the output shows them:

```text
Record R006: "poor sleep" recurred 3 times — … [merged: "can't sleep", "insomnia", "poor sleep"]
```

The engine surfaces, counts, and cites — including *which spellings it merged* —
and still never interprets what the recurrence means. See
[`data/RECORDS.md`](data/RECORDS.md) §5 for the full v1 walkthrough.
