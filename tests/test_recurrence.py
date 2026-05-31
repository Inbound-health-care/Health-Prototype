"""
test_recurrence.py — the six required spec cases for detect_recurrence.

Run from the repo root:
    python -m unittest discover -s tests -t .

Each test asserts toward an externally-known answer, never toward whatever the
code happens to produce.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recurrence import RecurrenceHit, detect_recurrence, format_hit  # noqa: E402


class TestDetectRecurrence(unittest.TestCase):
    # 1. Item recurs 3 times in one record -> caught, count == 3, all 3 dates.
    def test_recurs_three_times(self):
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
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].record_id, "R001")
        self.assertEqual(hits[0].item, "poor sleep")
        self.assertEqual(hits[0].count, 3)
        self.assertEqual(
            hits[0].dates, ["2026-01-10", "2026-02-02", "2026-03-15"]
        )

    # 2. Item appears exactly once -> NOT flagged (below min_count).
    def test_single_occurrence_not_flagged(self):
        hits = detect_recurrence(
            [{"id": "R002", "entries": [{"date": "2026-01-10", "item": "headache"}]}]
        )
        self.assertEqual(hits, [])

    # 3. Record with nothing recurring -> clean empty result, zero false positives.
    def test_nothing_recurring_is_empty(self):
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
        self.assertEqual(hits, [])

    # 4. Two different items each recur in one record -> both caught independently.
    def test_two_items_each_recur(self):
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
        self.assertEqual(len(hits), 2)
        self.assertIn("poor sleep", by_item)
        self.assertIn("appetite change", by_item)
        self.assertEqual(by_item["poor sleep"].count, 2)
        self.assertEqual(by_item["appetite change"].count, 2)
        self.assertEqual(
            by_item["appetite change"].dates, ["2026-02-20", "2026-03-01"]
        )

    # 5. Empty record / missing field -> handled gracefully, no crash, no false hit.
    def test_malformed_handled_gracefully(self):
        hits = detect_recurrence(
            [
                {"id": "R005", "entries": []},          # empty entries
                {"id": "R006"},                          # missing entries
                {"id": "R007", "entries": [              # missing item / None item
                    {"date": "2026-01-10"},
                    {"item": None, "date": "2026-02-02"},
                ]},
                {},                                      # empty record
                "not-a-record",                          # wrong type entirely
            ]
        )
        self.assertEqual(hits, [])

    # 6. min_count respected (set to 3 -> a 2x item does NOT flag).
    def test_min_count_respected(self):
        records = [
            {
                "id": "R008",
                "entries": [
                    {"date": "2026-01-10", "item": "poor sleep"},
                    {"date": "2026-02-02", "item": "poor sleep"},
                ],
            }
        ]
        self.assertEqual(detect_recurrence(records, min_count=3), [])
        # sanity: the same 2x item DOES flag at the default min_count of 2.
        self.assertEqual(len(detect_recurrence(records)), 1)


class TestInputValidation(unittest.TestCase):
    """Invalid arguments raise ValueError (library code fails loudly)."""

    def test_min_count_below_one_raises(self):
        with self.assertRaises(ValueError):
            detect_recurrence([], min_count=0)

    def test_fuzzy_cutoff_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            detect_recurrence([], fuzzy_cutoff=2.0)


class TestSurfacingFirewall(unittest.TestCase):
    """Output cites provenance and carries no interpretation."""

    def test_format_hit_cites_provenance_only(self):
        line = format_hit(
            RecurrenceHit(
                record_id="R001",
                item="poor sleep",
                count=2,
                dates=["2026-01-10", "2026-02-02"],
            )
        )
        # provenance present: record id, item, count, every date
        self.assertIn("R001", line)
        self.assertIn("poor sleep", line)
        self.assertIn("2", line)
        self.assertIn("2026-01-10", line)
        self.assertIn("2026-02-02", line)
        # no interpretation present
        lowered = line.lower()
        for banned in ("worsening", "severe", "severity", "suggests", "diagnos",
                       "risk", "concern", "abnormal", "score"):
            self.assertNotIn(banned, lowered)


if __name__ == "__main__":
    unittest.main()
