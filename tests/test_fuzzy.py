"""
test_fuzzy.py — v1 opt-in matching: normalize + declared synonyms + fuzzy.

Every layer is opt-in; the engine never merges differently-spelled entries
unless asked, and when it does it cites the originals in `variants`. These tests
assert the v1 answer key and the specific behaviors of each layer.

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import (  # noqa: E402
    ANSWER_KEY,
    ANSWER_KEY_V1,
    SAMPLE_RECORDS,
    SYNONYMS,
)
from recurrence import detect_recurrence, format_hit  # noqa: E402


def _record(rid: str) -> dict:
    for r in SAMPLE_RECORDS:
        if r["id"] == rid:
            return r
    raise AssertionError(f"Record {rid} not found in SAMPLE_RECORDS")


def _v1(records):
    return detect_recurrence(
        records, normalize=True, synonyms=SYNONYMS, fuzzy_cutoff=0.85
    )


class TestV1MatchesAnswerKey(unittest.TestCase):
    def test_v1_output_equals_answer_key_v1(self):
        got: dict = {}
        for hit in _v1(SAMPLE_RECORDS):
            got.setdefault(hit.record_id, {})[hit.item] = hit.dates
        expected = {rid: items for rid, items in ANSWER_KEY_V1.items() if items}
        self.assertEqual(got, expected)


class TestOptInSafety(unittest.TestCase):
    """With defaults, none of the v1 merges happen — v0 is preserved exactly."""

    def test_defaults_do_not_merge(self):
        for rid in ("R006", "R007", "R014"):
            self.assertEqual(detect_recurrence([_record(rid)]), [])

    def test_v0_answer_key_unchanged_under_defaults(self):
        got: dict = {}
        for hit in detect_recurrence(SAMPLE_RECORDS):
            got.setdefault(hit.record_id, {})[hit.item] = hit.dates
        expected = {rid: items for rid, items in ANSWER_KEY.items() if items}
        self.assertEqual(got, expected)


class TestLayersIndividually(unittest.TestCase):
    def test_normalize_merges_case_and_whitespace(self):
        # R007: "Hypertension" / "hypertension" / "hypertension " -> one group.
        hits = detect_recurrence([_record("R007")], normalize=True)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].count, 3)
        self.assertEqual(
            hits[0].variants, ["Hypertension", "hypertension", "hypertension "]
        )

    def test_synonyms_merge_true_synonyms(self):
        # R006: only a declared map can unite lexically-dissimilar synonyms.
        hits = detect_recurrence(
            [_record("R006")], normalize=True, synonyms=SYNONYMS
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].item, "poor sleep")
        self.assertEqual(hits[0].count, 3)
        self.assertEqual(
            hits[0].variants, ["can't sleep", "insomnia", "poor sleep"]
        )

    def test_normalize_alone_cannot_catch_synonyms(self):
        # Without the declared map, R006's synonyms stay separate.
        self.assertEqual(detect_recurrence([_record("R006")], normalize=True), [])

    def test_fuzzy_merges_typo_but_not_unrelated(self):
        # R014: typo + casing merge under fuzzy; R013's two SDOH items (ratio
        # well below cutoff) must NOT merge.
        hits = detect_recurrence(
            [_record("R014"), _record("R013")], normalize=True, fuzzy_cutoff=0.85
        )
        # Validate every emitted hit, not just the last per record: assert each
        # record produces exactly one group, then check it.
        r014 = [h for h in hits if h.record_id == "R014"]
        self.assertEqual(len(r014), 1, "expected exactly one merged group for R014")
        self.assertEqual(r014[0].count, 3)
        self.assertEqual(
            r014[0].variants,
            ["Blood Pressure", "blood pressure", "blood presure"],
        )
        # R013 still surfaces only the genuinely repeated item, count 2.
        r013 = [h for h in hits if h.record_id == "R013"]
        self.assertEqual(len(r013), 1, "expected exactly one recurring item for R013")
        self.assertEqual(r013[0].item, "housing instability")
        self.assertEqual(r013[0].count, 2)


class TestProvenanceAudit(unittest.TestCase):
    def test_merged_hit_cites_all_variants(self):
        hit = next(h for h in _v1([_record("R006")]))
        line = format_hit(hit)
        self.assertIn("[merged:", line)
        for variant in ("insomnia", "can't sleep", "poor sleep"):
            self.assertIn(variant, line)

    def test_unmerged_hit_has_no_merge_clause(self):
        # An exact (single-variant) hit renders exactly like v0 — no clause.
        hit = next(h for h in detect_recurrence([_record("R001")]))
        self.assertNotIn("[merged:", format_hit(hit))


if __name__ == "__main__":
    unittest.main()
