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
from recurrence import detect_recurrence  # noqa: E402


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
            record = next(r for r in SAMPLE_RECORDS if r["id"] == rid)
            self.assertEqual(detect_recurrence([record]), [])


if __name__ == "__main__":
    unittest.main()
