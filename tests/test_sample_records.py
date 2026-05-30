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


# ---------------------------------------------------------------------------
# Additional structural and regression tests
# ---------------------------------------------------------------------------


class TestSampleRecordsStructure(unittest.TestCase):
    """SAMPLE_RECORDS must have the expected shape for the engine to operate on."""

    def test_sample_records_is_a_list(self):
        self.assertIsInstance(SAMPLE_RECORDS, list)

    def test_sample_records_has_five_entries(self):
        self.assertEqual(len(SAMPLE_RECORDS), 5)

    def test_each_record_is_a_dict(self):
        for rec in SAMPLE_RECORDS:
            self.assertIsInstance(rec, dict)

    def test_each_record_has_id_key(self):
        for rec in SAMPLE_RECORDS:
            self.assertIn("id", rec)

    def test_each_record_has_entries_key(self):
        for rec in SAMPLE_RECORDS:
            self.assertIn("entries", rec)

    def test_each_entries_is_a_list(self):
        for rec in SAMPLE_RECORDS:
            self.assertIsInstance(rec["entries"], list)

    def test_each_entry_has_date_and_item(self):
        for rec in SAMPLE_RECORDS:
            for entry in rec["entries"]:
                self.assertIn("date", entry, msg=f"Missing 'date' in {rec['id']}: {entry}")
                self.assertIn("item", entry, msg=f"Missing 'item' in {rec['id']}: {entry}")

    def test_record_ids_are_unique(self):
        ids = [rec["id"] for rec in SAMPLE_RECORDS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_record_ids_match_expected_set(self):
        ids = {rec["id"] for rec in SAMPLE_RECORDS}
        self.assertEqual(ids, {"R001", "R002", "R003", "R004", "R005"})

    def test_dates_are_iso8601_strings(self):
        import re
        iso_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for rec in SAMPLE_RECORDS:
            for entry in rec["entries"]:
                self.assertRegex(
                    entry["date"], iso_re,
                    msg=f"Bad date in {rec['id']}: {entry['date']}"
                )

    def test_item_values_are_non_empty_strings(self):
        for rec in SAMPLE_RECORDS:
            for entry in rec["entries"]:
                self.assertIsInstance(entry["item"], str)
                self.assertGreater(len(entry["item"]), 0,
                                   msg=f"Empty item in {rec['id']}")


class TestAnswerKeyStructure(unittest.TestCase):
    """ANSWER_KEY must be internally consistent and cover every record."""

    def test_answer_key_is_a_dict(self):
        self.assertIsInstance(ANSWER_KEY, dict)

    def test_answer_key_covers_all_sample_record_ids(self):
        sample_ids = {rec["id"] for rec in SAMPLE_RECORDS}
        self.assertEqual(set(ANSWER_KEY.keys()), sample_ids)

    def test_answer_key_values_are_dicts(self):
        for rid, items in ANSWER_KEY.items():
            self.assertIsInstance(items, dict, msg=f"ANSWER_KEY[{rid!r}] is not a dict")

    def test_answer_key_dates_are_sorted_chronologically(self):
        # The oracle's dates for each item must already be in sorted order.
        for rid, items in ANSWER_KEY.items():
            for item, dates in items.items():
                self.assertEqual(
                    dates, sorted(dates),
                    msg=f"Dates not sorted for {rid}/{item!r}: {dates}"
                )

    def test_answer_key_dates_appear_in_sample_records(self):
        # Every date listed in the answer key must exist in the corresponding record.
        records_by_id = {rec["id"]: rec for rec in SAMPLE_RECORDS}
        for rid, items in ANSWER_KEY.items():
            record = records_by_id[rid]
            record_dates_for_item: dict = {}
            for entry in record["entries"]:
                record_dates_for_item.setdefault(entry["item"], []).append(entry["date"])
            for item, expected_dates in items.items():
                actual_dates = sorted(record_dates_for_item.get(item, []))
                self.assertEqual(
                    sorted(expected_dates), actual_dates,
                    msg=f"Date mismatch for {rid}/{item!r}"
                )

    def test_r003_has_no_expected_hits(self):
        # R003 is the deliberate zero-hit record — its answer key must be empty.
        self.assertEqual(ANSWER_KEY["R003"], {})

    def test_r001_poor_sleep_recurs_three_times(self):
        self.assertIn("poor sleep", ANSWER_KEY["R001"])
        self.assertEqual(len(ANSWER_KEY["R001"]["poor sleep"]), 3)

    def test_r002_has_two_independent_recurring_items(self):
        self.assertIn("appetite change", ANSWER_KEY["R002"])
        self.assertIn("fatigue", ANSWER_KEY["R002"])

    def test_r005_anxiety_recurs_four_times(self):
        self.assertIn("anxiety", ANSWER_KEY["R005"])
        self.assertEqual(len(ANSWER_KEY["R005"]["anxiety"]), 4)

    def test_non_recurring_items_not_in_answer_key(self):
        # Items that appear only once in SAMPLE_RECORDS must not appear in ANSWER_KEY.
        single_occurrence_items = {
            "R001": "headache",
            "R004": "nausea",
            "R005": "chest tightness",
        }
        for rid, single_item in single_occurrence_items.items():
            self.assertNotIn(
                single_item, ANSWER_KEY[rid],
                msg=f"Single-occurrence item {single_item!r} wrongly in ANSWER_KEY[{rid!r}]"
            )


class TestEnginePerRecordRegression(unittest.TestCase):
    """Per-record regression: each record in isolation must match its answer key entry."""

    def _run_record(self, record_id):
        record = next(r for r in SAMPLE_RECORDS if r["id"] == record_id)
        hits = detect_recurrence([record])
        return {h.item: h.dates for h in hits}

    def test_r001_individual(self):
        got = self._run_record("R001")
        self.assertEqual(got, ANSWER_KEY["R001"])

    def test_r002_individual(self):
        got = self._run_record("R002")
        self.assertEqual(got, ANSWER_KEY["R002"])

    def test_r003_individual(self):
        got = self._run_record("R003")
        self.assertEqual(got, {})

    def test_r004_individual(self):
        got = self._run_record("R004")
        self.assertEqual(got, ANSWER_KEY["R004"])

    def test_r005_individual(self):
        got = self._run_record("R005")
        self.assertEqual(got, ANSWER_KEY["R005"])
