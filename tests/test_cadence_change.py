"""
test_cadence_change.py — the cadence-change rule (#5).

detect_cadence_change surfaces an item whose inter-event spacing shifted by
``ratio`` or more across a single change point. The change point is located with
Pettitt's rank statistic (nonparametric, deterministic), and the flag compares
the median interval before vs after. These tests assert the hand-written
CADENCE_CHANGE_ANSWER_KEY, both shift directions, the steady / too-few / undated
controls, input validation, and the librarian rule (it never says a faster or
slower cadence means anything).

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import (  # noqa: E402
    CADENCE_CHANGE_ANSWER_KEY,
    CADENCE_CHANGE_RECORDS,
)
from recurrence import (  # noqa: E402
    CadenceChangeHit,
    detect_cadence_change,
    format_cadence_change_hit,
)
from tests.banned_words import BANNED  # noqa: E402


def _reshape(hits) -> dict:
    out: dict = {}
    for h in hits:
        out.setdefault(h.record_id, []).append(
            (h.item, h.before_interval, h.after_interval, h.pivot_date, h.dates)
        )
    return out


def _rec(entries) -> dict:
    return {"id": "RX", "entries": entries}


def _monthly_then_weekly() -> dict:
    # Intervals [30, 30, 30, 7, 7, 7]; change point at the 4th visit.
    return _rec(
        [
            {"date": "2026-01-01", "item": "insulin"},
            {"date": "2026-01-31", "item": "insulin"},
            {"date": "2026-03-02", "item": "insulin"},
            {"date": "2026-04-01", "item": "insulin"},
            {"date": "2026-04-08", "item": "insulin"},
            {"date": "2026-04-15", "item": "insulin"},
            {"date": "2026-04-22", "item": "insulin"},
        ]
    )


class TestCadenceChangeMatchesAnswerKey(unittest.TestCase):
    def test_output_equals_answer_key(self):
        self.assertEqual(
            _reshape(detect_cadence_change(CADENCE_CHANGE_RECORDS)),
            CADENCE_CHANGE_ANSWER_KEY,
        )


class TestCadenceChangeInputValidation(unittest.TestCase):
    """Invalid parameters fail loudly (library code raises, never misbehaves)."""

    def test_min_occurrences_below_two_raises(self):
        with self.assertRaises(ValueError):
            detect_cadence_change(CADENCE_CHANGE_RECORDS, min_occurrences=1)

    def test_ratio_not_above_one_raises(self):
        with self.assertRaises(ValueError):
            detect_cadence_change(CADENCE_CHANGE_RECORDS, ratio=1.0)

    def test_fuzzy_cutoff_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            detect_cadence_change(CADENCE_CHANGE_RECORDS, fuzzy_cutoff=1.5)


class TestCadenceChangeBehavior(unittest.TestCase):
    def test_tightening_surfaces_with_pivot(self):
        hits = detect_cadence_change([_monthly_then_weekly()])
        self.assertEqual(len(hits), 1)
        h = hits[0]
        self.assertEqual(h.item, "insulin")
        self.assertEqual((h.before_interval, h.after_interval), (30, 7))
        self.assertEqual(h.pivot_date, "2026-04-01")

    def test_loosening_also_surfaces(self):
        # Weekly then monthly: intervals [7, 7, 7, 30, 30]; pivot at the 4th day.
        rec = _rec(
            [
                {"date": "2026-01-01", "item": "labs"},
                {"date": "2026-01-08", "item": "labs"},
                {"date": "2026-01-15", "item": "labs"},
                {"date": "2026-01-22", "item": "labs"},
                {"date": "2026-02-21", "item": "labs"},
                {"date": "2026-03-23", "item": "labs"},
            ]
        )
        hits = detect_cadence_change([rec])
        self.assertEqual(len(hits), 1)
        h = hits[0]
        self.assertEqual((h.before_interval, h.after_interval), (7, 30))
        self.assertEqual(h.pivot_date, "2026-01-22")

    def test_steady_cadence_does_not_flag(self):
        rec = _rec(
            [
                {"date": "2026-01-05", "item": "checkup"},
                {"date": "2026-02-05", "item": "checkup"},
                {"date": "2026-03-05", "item": "checkup"},
                {"date": "2026-04-05", "item": "checkup"},
                {"date": "2026-05-05", "item": "checkup"},
            ]
        )
        self.assertEqual(detect_cadence_change([rec]), [])

    def test_below_min_occurrences_is_silent(self):
        # Three dated days -> fewer than the default min_occurrences of 4.
        rec = _rec(
            [
                {"date": "2026-01-01", "item": "scan"},
                {"date": "2026-02-01", "item": "scan"},
                {"date": "2026-05-01", "item": "scan"},
            ]
        )
        self.assertEqual(detect_cadence_change([rec]), [])

    def test_undated_occurrences_are_excluded(self):
        # Undated entries never form an interval; only the 4 dated days count,
        # and they still surface the same shift.
        rec = _rec(
            [
                {"item": "insulin"},  # undated
                {"date": "2026-01-01", "item": "insulin"},
                {"date": "2026-02-01", "item": "insulin"},
                {"item": "insulin"},  # undated
                {"date": "2026-02-08", "item": "insulin"},
                {"date": "2026-02-15", "item": "insulin"},
            ]
        )
        hits = detect_cadence_change([rec])
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].dates.count(""), 0)  # no undated in provenance

    def test_ratio_threshold_respected(self):
        # Intervals [10, 10, 15, 15] -> a 1.5x shift: below default ratio 2.0,
        # surfaces only when the threshold is lowered.
        rec = _rec(
            [
                {"date": "2026-01-01", "item": "visit"},
                {"date": "2026-01-11", "item": "visit"},
                {"date": "2026-01-21", "item": "visit"},
                {"date": "2026-02-05", "item": "visit"},
                {"date": "2026-02-20", "item": "visit"},
            ]
        )
        self.assertEqual(detect_cadence_change([rec]), [])
        hits = detect_cadence_change([rec], ratio=1.4)
        self.assertEqual(len(hits), 1)
        self.assertEqual((hits[0].before_interval, hits[0].after_interval), (10, 15))


class TestCadenceChangeLibrarianRule(unittest.TestCase):
    """Output states the interval change and where — never what it means."""

    BANNED = BANNED  # the shared suite-wide union — see tests/banned_words.py

    def test_format_is_neutral_and_cited(self):
        hits = detect_cadence_change([_monthly_then_weekly()])
        self.assertTrue(hits)
        for hit in hits:
            line = format_cadence_change_hit(hit)
            self.assertIn(hit.item, line)
            self.assertIn("interval changed", line)
            self.assertIn(hit.pivot_date, line)
            for banned in self.BANNED:
                self.assertNotIn(banned, line.lower(), f"banned word: {banned!r}")

    def test_merged_spellings_are_cited(self):
        hit = CadenceChangeHit(
            "R", "insulin", 30, 7, "2026-04-01",
            ["2026-01-01"], ["Insulin", "insulin"],
        )
        line = format_cadence_change_hit(hit)
        self.assertIn('[merged: "Insulin", "insulin"]', line)


if __name__ == "__main__":
    unittest.main()
