"""
test_sample_records.py — cross-check the placeholder data against its answer key.

The hand-written ANSWER_KEY is the oracle. This test runs detect_recurrence over
SAMPLE_RECORDS and asserts the engine surfaces EXACTLY the answer key — no more,
no fewer. If the data drifts from the answer key (a typo in either), this fails.

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import ANSWER_KEY, SAMPLE_RECORDS  # noqa: E402
from recurrence import detect_recurrence, format_hit  # noqa: E402


def _record(rid: str) -> dict:
    return next(r for r in SAMPLE_RECORDS if r["id"] == rid)


class TestSampleRecordsMatchAnswerKey(unittest.TestCase):
    def test_engine_output_equals_answer_key(self):
        hits = detect_recurrence(SAMPLE_RECORDS)

        # Reshape engine output to {record_id: {item: [dates]}}.
        got: dict = {}
        for hit in hits:
            got.setdefault(hit.record_id, {})[hit.item] = hit.dates

        # The answer key, dropping records with no expected hit (they emit none).
        expected = {rid: items for rid, items in ANSWER_KEY.items() if items}

        self.assertEqual(got, expected)

    def test_records_with_empty_answer_emit_nothing(self):
        # Every record the oracle marked as {} must surface zero hits.
        for rid, items in ANSWER_KEY.items():
            if items:
                continue
            self.assertEqual(detect_recurrence([_record(rid)]), [])

    def test_no_cross_record_merge(self):
        # "poor sleep" flags within R001 (x3) but the single occurrence in R006
        # must not be pulled in: recurrence is scoped per record, never across.
        hits = detect_recurrence([_record("R001"), _record("R006")])
        sleep_hits = [h for h in hits if h.item == "poor sleep"]
        self.assertEqual(len(sleep_hits), 1)
        self.assertEqual(sleep_hits[0].record_id, "R001")
        self.assertEqual(sleep_hits[0].count, 3)

    def test_undated_occurrence_renders_in_provenance(self):
        # R009 has one undated occurrence: it is counted ("" stored) and shown
        # as "(undated)" in the rendered line, never silently dropped.
        hit = next(
            h for h in detect_recurrence([_record("R009")])
            if h.item == "med refill: metformin"
        )
        self.assertEqual(hit.count, 3)
        self.assertIn("", hit.dates)
        self.assertIn("(undated)", format_hit(hit))


if __name__ == "__main__":
    unittest.main()
