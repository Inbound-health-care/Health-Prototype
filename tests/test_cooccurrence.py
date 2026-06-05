"""
test_cooccurrence.py — the co-occurrence rule.

detect_cooccurrence surfaces two distinct items in one record that BOTH appear
on the same date, on ``min_count`` or more distinct shared dates. These tests
assert the hand-written CO_OCCURRENCE_ANSWER_KEY, the pair combinatorics, the two
negative controls (items recur but never share a date / share only one date),
undated exclusion, input validation, and the output firewall.

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import CO_OCCURRENCE_ANSWER_KEY, SAMPLE_RECORDS  # noqa: E402
from recurrence import (  # noqa: E402
    CooccurrenceHit,
    detect_cooccurrence,
    detect_recurrence,
    format_cooccurrence_hit,
)


def _record(rid: str) -> dict:
    for r in SAMPLE_RECORDS:
        if r["id"] == rid:
            return r
    raise AssertionError(f"Record {rid} not found in SAMPLE_RECORDS")


def _reshape(hits) -> dict:
    out: dict = {}
    for h in hits:
        out.setdefault(h.record_id, []).append((h.item_a, h.item_b, h.count, h.dates))
    return out


class TestCooccurrenceMatchesAnswerKey(unittest.TestCase):
    def test_cooccurrence_output_equals_answer_key(self):
        self.assertEqual(
            _reshape(detect_cooccurrence(SAMPLE_RECORDS)), CO_OCCURRENCE_ANSWER_KEY
        )


class TestCooccurrenceInputValidation(unittest.TestCase):
    """Invalid parameters fail loudly (library code raises, never silently misbehaves)."""

    def test_min_count_below_one_raises(self):
        with self.assertRaises(ValueError):
            detect_cooccurrence(SAMPLE_RECORDS, min_count=0)

    def test_fuzzy_cutoff_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            detect_cooccurrence(SAMPLE_RECORDS, fuzzy_cutoff=1.5)


class TestCooccurrenceBehavior(unittest.TestCase):
    def test_clean_pair_surfaces(self):
        hits = detect_cooccurrence([_record("R017")])
        self.assertEqual(len(hits), 1)
        h = hits[0]
        self.assertEqual((h.item_a, h.item_b), ("knee pain", "poor sleep"))
        self.assertEqual(h.count, 2)
        self.assertEqual(h.dates, ["2026-01-10", "2026-02-14"])
        self.assertEqual(h.item, "knee pain + poor sleep")  # pair label property

    def test_three_items_produce_all_pairs_in_order(self):
        hits = detect_cooccurrence([_record("R018")])
        self.assertEqual(
            [(h.item_a, h.item_b) for h in hits],
            [("dizziness", "fatigue"), ("dizziness", "nausea"), ("fatigue", "nausea")],
        )
        self.assertTrue(all(h.count == 2 for h in hits))

    def test_both_recur_but_never_share_date_does_not_flag(self):
        # R019: cough and rash each recur, but on different dates — they never
        # share one. The load-bearing control: co-occurrence is NOT "both recur".
        self.assertEqual(detect_cooccurrence([_record("R019")]), [])
        # ...and recurrence DOES still flag both, proving the records do recur.
        self.assertEqual(len(detect_recurrence([_record("R019")])), 2)

    def test_single_shared_date_below_threshold(self):
        # R020: edema + back pain share exactly one date -> below default min_count.
        self.assertEqual(detect_cooccurrence([_record("R020")]), [])
        # At min_count=1 the single shared date qualifies — so it is the
        # threshold, not the absence of any shared date, that suppresses it.
        hits = detect_cooccurrence([_record("R020")], min_count=1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].count, 1)
        self.assertEqual(hits[0].dates, ["2026-01-12"])

    def test_undated_entries_never_count_as_a_shared_date(self):
        rec = {
            "id": "RU",
            "entries": [
                {"item": "a"},  # undated
                {"item": "b"},  # undated
                {"date": "2026-01-01", "item": "a"},
                {"date": "2026-01-01", "item": "b"},
            ],
        }
        # Only the one real date is shared; the undated "" is excluded. So at
        # min_count=1 there is exactly one shared date, never two.
        hits = detect_cooccurrence([rec], min_count=1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].count, 1)
        self.assertEqual(hits[0].dates, ["2026-01-01"])

    def test_min_count_parameter_respected(self):
        self.assertEqual(detect_cooccurrence([_record("R017")], min_count=3), [])
        self.assertEqual(len(detect_cooccurrence([_record("R017")], min_count=2)), 1)


class TestCooccurrenceFirewall(unittest.TestCase):
    """Output cites provenance only — pure counting, never a relationship claim."""

    BANNED = (
        "worsening", "worsen", "severe", "severity", "suggests", "diagnos",
        "risk", "concern", "caution", "abnormal", "score", "acute",
        "associated", "correlated", "linked", "cause", "caused", "relationship",
    )

    def test_format_is_count_only(self):
        for hit in detect_cooccurrence([_record("R017")]) + detect_cooccurrence(
            [_record("R018")]
        ):
            line = format_cooccurrence_hit(hit)
            self.assertIn(hit.item_a, line)
            self.assertIn(hit.item_b, line)
            self.assertIn("co-occurred", line)
            for banned in self.BANNED:
                self.assertNotIn(banned, line.lower(), f"banned word: {banned!r}")

    def test_merged_provenance_is_attributed_per_item(self):
        # Only item_a merged (two spellings); item_b did not. The clause must
        # cite item_a's variants and NOT fabricate one for item_b.
        hit = CooccurrenceHit(
            "R", "bp", "sleep", 2, ["2026-01-01", "2026-02-01"], ["BP", "bp"], ["sleep"]
        )
        line = format_cooccurrence_hit(hit)
        self.assertEqual(line.count("[merged:"), 1)
        self.assertIn('"bp" [merged: "BP", "bp"]', line)


class TestCooccurrenceWindow(unittest.TestCase):
    """The opt-in ``window_days`` extension: two items co-occur if their dates
    fall within N days, not only the same day. Default (0) stays exact v0."""

    def test_window_zero_is_byte_identical_to_default(self):
        # The whole point of the opt-in: window_days=0 reproduces v0 exactly.
        self.assertEqual(
            _reshape(detect_cooccurrence(SAMPLE_RECORDS, window_days=0)),
            CO_OCCURRENCE_ANSWER_KEY,
        )
        self.assertEqual(
            _reshape(detect_cooccurrence(SAMPLE_RECORDS, window_days=0)),
            _reshape(detect_cooccurrence(SAMPLE_RECORDS)),
        )

    def test_near_date_pair_surfaces_within_window(self):
        # R020: edema + back pain share 2026-01-12 (gap 0) AND are 4 days apart in
        # March (03-18 vs 03-22). At window_days=4 that is two matched pairs -> it
        # flags (count 2); at v0 same-date it shares only one date -> stays silent.
        hits = detect_cooccurrence([_record("R020")], window_days=4)
        self.assertEqual(len(hits), 1)
        h = hits[0]
        self.assertEqual((h.item_a, h.item_b), ("back pain", "edema"))
        self.assertEqual(h.count, 2)
        self.assertEqual(h.window_days, 4)
        self.assertEqual(
            h.pairs,
            [("2026-01-12", "2026-01-12", 0), ("2026-03-22", "2026-03-18", 4)],
        )
        self.assertEqual(h.dates, ["2026-01-12", "2026-03-18", "2026-03-22"])

    def test_boundary_inclusive_and_just_outside_is_silent(self):
        # gap is exactly 4: included at window_days=4, excluded at window_days=3
        # (only the same-date pair remains -> 1 < min_count 2 -> no hit).
        self.assertEqual(len(detect_cooccurrence([_record("R020")], window_days=4)), 1)
        self.assertEqual(detect_cooccurrence([_record("R020")], window_days=3), [])
        # And v0 (same-date only) never surfaced R020 at all.
        self.assertEqual(detect_cooccurrence([_record("R020")]), [])

    def test_greedy_one_to_one_does_not_double_count(self):
        # 'a' has one date; 'b' has two dates both within a's window. Greedy
        # one-to-one matches a's single date to ONE of b's, not both: count 1.
        rec = {
            "id": "RW",
            "entries": [
                {"date": "2026-01-10", "item": "a"},
                {"date": "2026-01-11", "item": "b"},
                {"date": "2026-01-12", "item": "b"},
            ],
        }
        hits = detect_cooccurrence([rec], window_days=5, min_count=1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].count, 1)
        self.assertEqual(hits[0].pairs, [("2026-01-10", "2026-01-11", 1)])

    def test_negative_window_days_raises(self):
        with self.assertRaises(ValueError):
            detect_cooccurrence(SAMPLE_RECORDS, window_days=-1)

    def test_window_format_shows_window_and_stays_count_only(self):
        hit = detect_cooccurrence([_record("R020")], window_days=4)[0]
        line = format_cooccurrence_hit(hit)
        self.assertIn("co-occurred 2 times within 4 days", line)
        self.assertIn("(2026-03-22 ~ 2026-03-18: 4d)", line)
        for banned in TestCooccurrenceFirewall.BANNED:
            self.assertNotIn(banned, line.lower(), f"banned word: {banned!r}")


if __name__ == "__main__":
    unittest.main()
