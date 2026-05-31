"""
test_frequency.py — the frequency / burst rule.

detect_frequency surfaces an item that appears ``min_count`` or more times
within any ``window_days`` span. These tests assert the hand-written
FREQUENCY_ANSWER_KEY, the burst window, the no-false-positive cases, and that
the window/threshold parameters are respected.

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import FREQUENCY_ANSWER_KEY, SAMPLE_RECORDS  # noqa: E402
from recurrence import detect_frequency, format_frequency_hit  # noqa: E402


def _record(rid: str) -> dict:
    for r in SAMPLE_RECORDS:
        if r["id"] == rid:
            return r
    raise AssertionError(f"Record {rid} not found in SAMPLE_RECORDS")


def _reshape(hits) -> dict:
    out: dict = {}
    for h in hits:
        out.setdefault(h.record_id, []).append(
            (h.item, h.count, h.window_start, h.window_end, h.dates)
        )
    return out


class TestFrequencyMatchesAnswerKey(unittest.TestCase):
    def test_frequency_output_equals_answer_key(self):
        self.assertEqual(
            _reshape(detect_frequency(SAMPLE_RECORDS)), FREQUENCY_ANSWER_KEY
        )


class TestFrequencyInputValidation(unittest.TestCase):
    """Invalid parameters fail loudly (library code raises, never silently misbehaves)."""

    def test_negative_window_days_raises(self):
        with self.assertRaises(ValueError):
            detect_frequency(SAMPLE_RECORDS, window_days=-1)

    def test_min_count_below_one_raises(self):
        with self.assertRaises(ValueError):
            detect_frequency(SAMPLE_RECORDS, min_count=0)

    def test_fuzzy_cutoff_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            detect_frequency(SAMPLE_RECORDS, fuzzy_cutoff=1.5)


class TestFrequencyBehavior(unittest.TestCase):
    def test_burst_surfaces_densest_window(self):
        hits = detect_frequency([_record("R016")])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].item, "chest pain")
        self.assertEqual(hits[0].count, 3)
        self.assertEqual(hits[0].window_start, "2026-02-01")
        self.assertEqual(hits[0].window_end, "2026-02-20")
        self.assertEqual(
            hits[0].dates, ["2026-02-01", "2026-02-10", "2026-02-20"]
        )

    def test_spread_out_item_does_not_burst(self):
        # R015's depression is never 3x within 30 days.
        self.assertEqual(detect_frequency([_record("R015")]), [])

    def test_window_parameter_respected(self):
        # Widen the window to 120 days and the isolated 4th visit joins in.
        hits = detect_frequency([_record("R016")], window_days=120)
        self.assertEqual(hits[0].count, 4)
        self.assertEqual(hits[0].window_end, "2026-05-10")

    def test_min_count_parameter_respected(self):
        # At min_count=5 the 4-occurrence record no longer qualifies.
        self.assertEqual(
            detect_frequency([_record("R016")], window_days=120, min_count=5), []
        )

    def test_format_is_descriptive_only(self):
        line = format_frequency_hit(detect_frequency([_record("R016")])[0])
        self.assertIn("chest pain", line)
        self.assertIn("3 times", line)
        for banned in ("worsening", "severe", "acute", "concern", "risk"):
            self.assertNotIn(banned, line.lower())


if __name__ == "__main__":
    unittest.main()
