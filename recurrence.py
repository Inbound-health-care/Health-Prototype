#!/usr/bin/env python3
"""
recurrence.py — Recurrence Detection Engine (Prototype v0)
==========================================================

Pure-stdlib. Zero external dependencies. Local-only (no network egress).

Given a set of records, surface every case where the same item appears across
multiple dated entries, and cite exactly where each occurrence came from.

This is a LIBRARIAN, not an interpreter. It surfaces, counts, and cites
provenance. It never scores, ranks, diagnoses, or says what a pattern *means*.
That separation is the design principle and the legal firewall in one.

Domain-agnostic by design: a record can be a patient, a pharmacy profile, a
session log — the engine does not care. v0 matches EXACTLY; fuzzy / synonym
matching (e.g. "can't sleep" == "insomnia") is deferred to v1.

  Self-test:  python recurrence.py --self-test
  Demo:       python recurrence.py --demo
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Surfaced result — sourced, never interpreted
# ---------------------------------------------------------------------------


@dataclass
class RecurrenceHit:
    """One surfaced recurrence.

    Carries provenance only: which record, which item, how many times, and the
    exact dates it appeared on. No severity, no score, no interpretation.
    """

    record_id: str
    item: str
    count: int
    dates: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# The function
# ---------------------------------------------------------------------------


def detect_recurrence(
    records: list,
    field: str = "item",
    min_count: int = 2,
) -> list[RecurrenceHit]:
    """Return a list of recurrence hits.

    Scan each record's entries. When the same value of ``field`` appears in
    ``min_count`` or more entries, emit a :class:`RecurrenceHit` citing the
    record id, the item, the count, and the dates it appeared on. Surfaces
    only — no interpretation.

    Domain-agnostic and defensive: anything malformed (missing entries, a
    non-dict entry, a missing/empty item field, a missing date) is skipped
    rather than raising. The result is deterministic — hits are ordered by
    record, then by item, and dates within a hit are sorted chronologically.
    """
    hits: list[RecurrenceHit] = []

    if not records:
        return hits

    for record in records:
        if not isinstance(record, dict):
            continue

        record_id = str(record.get("id", ""))
        entries = record.get("entries")
        if not isinstance(entries, list):
            continue

        # Map each item value -> the list of dates it was seen on.
        dates_by_item: dict[str, list[str]] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            item = entry.get(field)
            # Skip entries with no usable item value (None, "", missing field).
            if item is None or item == "":
                continue
            item_key = str(item)
            date = entry.get("date")
            date_str = "" if date is None else str(date)
            dates_by_item.setdefault(item_key, []).append(date_str)

        for item_key in sorted(dates_by_item):
            dates = dates_by_item[item_key]
            if len(dates) >= min_count:
                hits.append(
                    RecurrenceHit(
                        record_id=record_id,
                        item=item_key,
                        count=len(dates),
                        dates=sorted(dates),
                    )
                )

    return hits


def format_hit(hit: RecurrenceHit) -> str:
    """Render a hit as a single provenance-cited line.

    Example:
      Record R001: "poor sleep" recurred 2 times — 2026-01-10, 2026-02-02

    An occurrence whose entry carried no date is stored as "" in ``hit.dates``
    and rendered here as "(undated)" — a visible data-quality marker, not an
    interpretation. It flags incomplete provenance rather than hiding it.
    """
    dates = ", ".join(d if d else "(undated)" for d in hit.dates)
    return (
        f'Record {hit.record_id}: "{hit.item}" recurred {hit.count} times — {dates}'
    )


# ---------------------------------------------------------------------------
# Self-test — the six required spec cases, asserted toward known answers
# ---------------------------------------------------------------------------


def _self_test_scenarios() -> list[tuple[str, bool]]:
    """Run the six required cases. Return (name, ok) for each.

    Each scenario defines its own input and its externally-known answer; the
    code is patched toward the answer, never the answer toward the code.
    """
    results: list[tuple[str, bool]] = []

    # 1. Item recurs 3 times in one record -> caught, count == 3, all 3 dates.
    hits = detect_recurrence(
        [
            {
                "id": "R001",
                "entries": [
                    {"date": "2026-01-10", "item": "poor sleep"},
                    {"date": "2026-02-02", "item": "poor sleep"},
                    {"date": "2026-03-15", "item": "poor sleep"},
                ],
            }
        ]
    )
    ok = (
        len(hits) == 1
        and hits[0].count == 3
        and hits[0].item == "poor sleep"
        and hits[0].dates == ["2026-01-10", "2026-02-02", "2026-03-15"]
    )
    results.append(("recurs_three_times", ok))

    # 2. Item appears exactly once -> NOT flagged (below min_count).
    hits = detect_recurrence(
        [{"id": "R002", "entries": [{"date": "2026-01-10", "item": "headache"}]}]
    )
    results.append(("single_occurrence_not_flagged", hits == []))

    # 3. Record with nothing recurring -> clean empty result, zero false positives.
    hits = detect_recurrence(
        [
            {
                "id": "R003",
                "entries": [
                    {"date": "2026-01-10", "item": "cough"},
                    {"date": "2026-02-02", "item": "rash"},
                    {"date": "2026-03-15", "item": "fatigue"},
                ],
            }
        ]
    )
    results.append(("nothing_recurring_empty", hits == []))

    # 4. Two different items each recur in one record -> both caught independently.
    hits = detect_recurrence(
        [
            {
                "id": "R004",
                "entries": [
                    {"date": "2026-01-10", "item": "poor sleep"},
                    {"date": "2026-02-02", "item": "poor sleep"},
                    {"date": "2026-02-20", "item": "appetite change"},
                    {"date": "2026-03-01", "item": "appetite change"},
                ],
            }
        ]
    )
    by_item = {h.item: h for h in hits}
    ok = (
        len(hits) == 2
        and by_item.get("poor sleep") is not None
        and by_item["poor sleep"].count == 2
        and by_item.get("appetite change") is not None
        and by_item["appetite change"].count == 2
    )
    results.append(("two_items_each_recur", ok))

    # 5. Empty record / missing field -> handled gracefully, no crash, no false hit.
    try:
        hits = detect_recurrence(
            [
                {"id": "R005", "entries": []},
                {"id": "R006"},
                {"id": "R007", "entries": [{"date": "2026-01-10"}, {"item": None}]},
                {},
            ]
        )
        ok = hits == []
    except Exception:
        ok = False
    results.append(("malformed_handled_gracefully", ok))

    # 6. min_count respected (set to 3 -> a 2x item does NOT flag).
    hits = detect_recurrence(
        [
            {
                "id": "R008",
                "entries": [
                    {"date": "2026-01-10", "item": "poor sleep"},
                    {"date": "2026-02-02", "item": "poor sleep"},
                ],
            }
        ],
        min_count=3,
    )
    results.append(("min_count_respected", hits == []))

    return results


def _run_self_test() -> int:
    """Run the built-in self-test. Return 0 on success, non-zero on failure."""
    results = _self_test_scenarios()
    failures = [name for name, ok in results if not ok]
    if failures:
        print(f"FAILED ({len(failures)}):", file=sys.stderr)
        for name in failures:
            print(f"  - {name}", file=sys.stderr)
        return 1
    print(f"OK: {len(results)} scenarios passed.")
    return 0


# ---------------------------------------------------------------------------
# Demo — runs against the (Scott-supplied) placeholder record set
# ---------------------------------------------------------------------------


def _run_demo() -> int:
    """Surface recurrences in the placeholder record set, if one is present."""
    try:
        from data.sample_records import SAMPLE_RECORDS
    except Exception:
        SAMPLE_RECORDS = []

    if not SAMPLE_RECORDS:
        print(
            "No records yet — awaiting the placeholder record set in "
            "data/sample_records.py (SAMPLE_RECORDS)."
        )
        return 0

    hits = detect_recurrence(SAMPLE_RECORDS)
    if not hits:
        print("No recurrences surfaced across the placeholder records.")
        return 0

    for hit in hits:
        print(format_hit(hit))
    return 0


# ---------------------------------------------------------------------------
# CLI — local-only, no server, no network
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Recurrence Detection Engine (v0) — surface, count, and cite "
        "recurring items across dated entries. Surfaces only; never interprets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--self-test", action="store_true", help="Run the six built-in spec cases"
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="Surface recurrences in data/sample_records.py",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        return _run_self_test()
    if args.demo:
        return _run_demo()
    build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
