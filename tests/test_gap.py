"""
test_gap.py — the gap / re-emergence rule.

detect_gap surfaces an item that returns after an absence longer than
``gap_days``. These tests assert the hand-written GAP_ANSWER_KEY, the gap math,
the no-false-positive cases, and that the threshold is respected.

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import GAP_ANSWER_KEY, SAMPLE_RECORDS  # noqa: E402
from recurrence import detect_gap, format_gap_hit  # noqa: E402


def _record(rid: str) -> dict:
    return next(r for r in SAMPLE_RECORDS if r["id"] == rid)


def _reshape(hits) -> dict:
    out: dict = {}
    for h in hits:
        out.setdefault(h.record_id, []).append(
            (h.item, h.gap_days, h.before_date, h.after_date)
        )
    return out


class TestGapMatchesAnswerKey(unittest.TestCase):
    def test_gap_output_equals_answer_key(self):
        self.assertEqual(_reshape(detect_gap(SAMPLE_RECORDS)), GAP_ANSWER_KEY)


class TestGapBehavior(unittest.TestCase):
    def test_long_absence_surfaces_with_dates(self):
        hits = detect_gap([_record("R015")])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].item, "depression")
        self.assertEqual(hits[0].gap_days, 243)
        self.assertEqual(hits[0].before_date, "2026-01-10")
        self.assertEqual(hits[0].after_date, "2026-09-10")

    def test_short_gap_does_not_surface(self):
        # R016's largest gap is 79 days (< default 90) -> nothing.
        self.assertEqual(detect_gap([_record("R016")]), [])

    def test_threshold_respected(self):
        # R009's metformin has a 61-day gap: hidden at 90, shown at 60.
        self.assertEqual(detect_gap([_record("R009")]), [])
        hits = detect_gap([_record("R009")], gap_days=60)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].gap_days, 61)

    def test_undated_occurrence_ignored(self):
        # R009 has an undated metformin entry; the gap uses only the two real
        # dates, never guessing a date for the undated one.
        hits = detect_gap([_record("R009")], gap_days=30)
        self.assertEqual(len(hits), 1)
        self.assertEqual((hits[0].before_date, hits[0].after_date),
                         ("2026-01-07", "2026-03-09"))

    def test_format_is_descriptive_only(self):
        line = format_gap_hit(detect_gap([_record("R015")])[0])
        self.assertIn("depression", line)
        self.assertIn("243 days", line)
        for banned in ("relapse", "worsening", "severe", "concern", "risk"):
            self.assertNotIn(banned, line.lower())


if __name__ == "__main__":
    unittest.main()
