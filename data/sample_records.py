"""
sample_records.py — placeholder record set for the recurrence engine.
=====================================================================

ZERO real PHI. Every record here is invented. The author is the oracle:
write the answer key FIRST (what *should* surface), then let the engine run
and confirm it matches — never patch the answer key toward whatever the code
produces.

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

Fill SAMPLE_RECORDS with 5-10 invented records carrying known recurrence
patterns, and record the expected hits in ANSWER_KEY. `python recurrence.py
--demo` surfaces recurrences across SAMPLE_RECORDS.
"""

from __future__ import annotations

# Scott invents 5-10 placeholder records here (zero real PHI).
SAMPLE_RECORDS: list[dict] = []

# The externally-known answer: for each record id, the items that SHOULD surface
# mapped to the dates they recur on. Example shape (delete when filling in):
#   ANSWER_KEY = {
#       "R001": {"poor sleep": ["2026-01-10", "2026-02-02"]},
#   }
ANSWER_KEY: dict = {}
