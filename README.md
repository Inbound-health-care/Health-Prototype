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

```
Record R001: "poor sleep" recurred 2 times — 2026-01-10, 2026-02-02
```

## Running it

```bash
python recurrence.py --self-test                  # run the six required spec cases
python recurrence.py --demo                        # surface recurrences in data/sample_records.py
python -m unittest discover -s tests -t .          # full test suite (from repo root)
```

The placeholder record set lives in `data/sample_records.py` — invent 5–10
records with known recurrence patterns, write the answer key first, then run
`--demo` to confirm the engine surfaces exactly those patterns.

## v0 limitation

**Exact-match only.** Same meaning in different words (e.g. "can't sleep" ==
"insomnia") is *not* matched in v0 — that is a known, documented limitation, not
a bug. Fuzzy / synonym matching is deferred to v1, so the core is proven first.
