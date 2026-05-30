"""
sample_records.py — placeholder record set for the recurrence engine.
=====================================================================

ZERO real PHI. Every record here is invented. The author is the oracle:
the answer key is written by hand FIRST (what *should* surface), then the
engine runs and must match it — never patch the answer key toward whatever the
code produces. tests/test_sample_records.py enforces that agreement.

Generic record shape (domain-agnostic — a record can be a patient, a pharmacy
profile, a session log, ...):

    record = {
        "id": "R001",
        "entries": [
            {"date": "2026-01-10", "item": "poor sleep"},     # ISO 8601 date
            {"date": "2026-02-02", "item": "poor sleep"},
            {"date": "2026-02-20", "item": "appetite change"},
        ],
    }

Each entry needs a "date" (ISO 8601) and an "item" (the text the engine scans).

`python recurrence.py --demo` surfaces recurrences across SAMPLE_RECORDS.
Default rule: an item flags when it appears in 2+ entries (min_count = 2).
"""

from __future__ import annotations

# Five invented records (zero real PHI), each with a deliberate, known pattern.
SAMPLE_RECORDS: list[dict] = [
    # R001 — one item recurs 3x; a second item appears once (must NOT flag).
    {
        "id": "R001",
        "entries": [
            {"date": "2026-01-05", "item": "poor sleep"},
            {"date": "2026-02-10", "item": "poor sleep"},
            {"date": "2026-03-12", "item": "poor sleep"},
            {"date": "2026-01-20", "item": "headache"},
        ],
    },
    # R002 — two different items each recur 2x; both must flag independently.
    {
        "id": "R002",
        "entries": [
            {"date": "2026-01-08", "item": "appetite change"},
            {"date": "2026-02-15", "item": "appetite change"},
            {"date": "2026-02-02", "item": "fatigue"},
            {"date": "2026-03-01", "item": "fatigue"},
        ],
    },
    # R003 — nothing recurs; all three items are distinct (clean, zero hits).
    {
        "id": "R003",
        "entries": [
            {"date": "2026-01-10", "item": "cough"},
            {"date": "2026-02-05", "item": "rash"},
            {"date": "2026-03-09", "item": "dizziness"},
        ],
    },
    # R004 — one item recurs 2x; a second appears once (must NOT flag).
    {
        "id": "R004",
        "entries": [
            {"date": "2026-01-15", "item": "back pain"},
            {"date": "2026-02-20", "item": "back pain"},
            {"date": "2026-03-25", "item": "nausea"},
        ],
    },
    # R005 — one item recurs 4x; a second appears once (must NOT flag).
    {
        "id": "R005",
        "entries": [
            {"date": "2026-01-03", "item": "anxiety"},
            {"date": "2026-01-31", "item": "anxiety"},
            {"date": "2026-02-28", "item": "anxiety"},
            {"date": "2026-03-30", "item": "anxiety"},
            {"date": "2026-02-14", "item": "chest tightness"},
        ],
    },
]

# The hand-written answer key (oracle): for each record, the items that SHOULD
# surface at min_count = 2, mapped to the exact dates (chronological).
# Records with no expected hit are listed with an empty dict for completeness.
ANSWER_KEY: dict = {
    "R001": {"poor sleep": ["2026-01-05", "2026-02-10", "2026-03-12"]},
    "R002": {
        "appetite change": ["2026-01-08", "2026-02-15"],
        "fatigue": ["2026-02-02", "2026-03-01"],
    },
    "R003": {},
    "R004": {"back pain": ["2026-01-15", "2026-02-20"]},
    "R005": {"anxiety": ["2026-01-03", "2026-01-31", "2026-02-28", "2026-03-30"]},
}
