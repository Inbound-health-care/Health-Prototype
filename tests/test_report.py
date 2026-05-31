"""Tests for the combined per-record report (router + expert registry).

The report is a VIEW over the three existing rules. These tests pin it two
ways: against the hand-written REPORT_ANSWER_KEY (oracle agreement), and
against the three detect_* functions themselves (composition consistency) — so
the combined view can never silently diverge from any single rule. The firewall
test additionally bans ranking/aggregation words, not only severity words: a
combined report is the place a "which record is worst" temptation would creep
in, and it must not.
"""

import dataclasses
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.sample_records import REPORT_ANSWER_KEY, SAMPLE_RECORDS
from recurrence import (
    EXPERTS,
    Expert,
    Finding,
    RecordReport,
    detect_frequency,
    detect_gap,
    detect_recurrence,
    format_report,
    run_report,
)


def _group_hits_by_record(hits):
    grouped = {}
    for hit in hits:
        grouped.setdefault(hit.record_id, []).append(hit)
    return grouped


class TestReportOracle(unittest.TestCase):
    """run_report reproduces the hand-written REPORT_ANSWER_KEY exactly."""

    def test_report_output_equals_answer_key(self):
        reports = run_report(SAMPLE_RECORDS)
        shaped = {
            rep.record_id: [(f.expert, f.hit.item) for f in rep.findings]
            for rep in reports
        }
        self.assertEqual(shaped, REPORT_ANSWER_KEY)


class TestReportComposition(unittest.TestCase):
    """The view never diverges from the rules it composes."""

    def setUp(self):
        self.reports = run_report(SAMPLE_RECORDS)

    def _findings_for(self, expert_name):
        grouped = {}
        for rep in self.reports:
            hits = [f.hit for f in rep.findings if f.expert == expert_name]
            if hits:
                grouped[rep.record_id] = hits
        return grouped

    def test_recurrence_findings_match_detect_recurrence(self):
        self.assertEqual(
            self._findings_for("recurrence"),
            _group_hits_by_record(detect_recurrence(SAMPLE_RECORDS)),
        )

    def test_gap_findings_match_detect_gap(self):
        self.assertEqual(
            self._findings_for("gap"),
            _group_hits_by_record(detect_gap(SAMPLE_RECORDS)),
        )

    def test_frequency_findings_match_detect_frequency(self):
        self.assertEqual(
            self._findings_for("frequency"),
            _group_hits_by_record(detect_frequency(SAMPLE_RECORDS)),
        )


class TestReportOrderingAndOmission(unittest.TestCase):
    """Deterministic ordering; clean records omitted; empties handled."""

    def test_records_sorted_by_id(self):
        reports = run_report(SAMPLE_RECORDS)
        ids = [rep.record_id for rep in reports]
        self.assertEqual(ids, sorted(ids))

    def test_experts_within_record_follow_registry_order(self):
        order = {e.name: i for i, e in enumerate(EXPERTS)}
        for rep in run_report(SAMPLE_RECORDS):
            ranks = [order[f.expert] for f in rep.findings]
            self.assertEqual(ranks, sorted(ranks))

    def test_deterministic_across_runs(self):
        a = run_report(SAMPLE_RECORDS)
        b = run_report(SAMPLE_RECORDS)
        self.assertEqual(
            [(r.record_id, [(f.expert, f.hit.item) for f in r.findings]) for r in a],
            [(r.record_id, [(f.expert, f.hit.item) for f in r.findings]) for r in b],
        )
        self.assertEqual(format_report(a), format_report(b))

    def test_clean_records_omitted(self):
        ids = {rep.record_id for rep in run_report(SAMPLE_RECORDS)}
        for clean in ("R003", "R006", "R007", "R014"):
            self.assertNotIn(clean, ids)

    def test_empty_records_yield_empty_report(self):
        self.assertEqual(run_report([]), [])
        self.assertEqual(format_report([]), "")

    def test_malformed_records_do_not_raise(self):
        junk = [{"id": "RX", "entries": ["not-a-dict", {"item": None}]}, "nope"]
        run_report(junk)  # must not raise


class TestReportFirewall(unittest.TestCase):
    """Output cites provenance only — no interpretation, no ranking."""

    BANNED = (
        # interpretive (the existing per-rule firewall set)
        "worsening", "worsen", "severe", "severity", "suggests", "diagnos",
        "risk", "concern", "caution", "abnormal", "score", "relapse", "acute",
        # ranking / aggregation (stricter, specific to a combined view)
        "top", "most", "priority", "prioritize", "rank", "ranking",
        "total", "highest", "lowest", "worst", "best",
    )

    def test_report_text_has_no_banned_words(self):
        text = format_report(run_report(SAMPLE_RECORDS)).lower()
        for word in self.BANNED:
            self.assertNotIn(word, text, f"banned word surfaced: {word!r}")

    def test_report_cites_provenance(self):
        text = format_report(run_report(SAMPLE_RECORDS))
        # record ids and the lens tags are present as provenance
        self.assertIn("Record R015:", text)
        self.assertIn("[recurrence]", text)
        self.assertIn("[gap]", text)
        self.assertIn("[frequency]", text)


class TestExpertRegistry(unittest.TestCase):
    """The registry is well-formed and the abstraction is immutable."""

    def test_registry_order_and_names(self):
        self.assertEqual([e.name for e in EXPERTS], ["recurrence", "gap", "frequency"])

    def test_names_unique(self):
        names = [e.name for e in EXPERTS]
        self.assertEqual(len(names), len(set(names)))

    def test_callables(self):
        for e in EXPERTS:
            self.assertTrue(callable(e.detect))
            self.assertTrue(callable(e.formatter))

    def test_expert_is_frozen(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            EXPERTS[0].name = "mutated"


if __name__ == "__main__":
    unittest.main()
