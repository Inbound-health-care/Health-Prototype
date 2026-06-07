"""test_extract_multi.py — the fail-closed multi-patient extractor (ADR 0016).

extract_records_multi splits a multi-patient batch on an EXPLICIT delimiter and
accepts a segment only when its identity is unambiguous; anything missing,
ambiguous, or duplicated is quarantined (refused), never merged or guessed. These
tests assert the hand-written oracle (accepted records + quarantine reasons), the
load-bearing NO-BLEED invariant (each entry traces only to its own segment; two
patients sharing an item stay separate records the engine never cross-attributes),
per-patient de-identifying shift, fail-loud config (vs fail-closed data), and that
the librarian rule holds in the refusal output. Pure stdlib.

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import contextlib
import datetime
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import (  # noqa: E402
    FREETEXT_EXPECTED_MULTI_QUARANTINE,
    FREETEXT_EXPECTED_MULTI_RECORDS,
    FREETEXT_GAZETTEER,
    FREETEXT_MULTI_DELIMITER,
    FREETEXT_MULTI_NOTE,
    FREETEXT_MULTI_SHIFTS,
)
from extract import (  # noqa: E402
    _QUARANTINE_REASONS,
    _run_demo_multi,
    extract_records_multi,
    format_entry,
    parse_patient_ids,
)
from recurrence import detect_cooccurrence, run_report  # noqa: E402

DELIM = FREETEXT_MULTI_DELIMITER

# The librarian-rule banned words live once in tests/banned_words.py (shared union).
from tests.banned_words import BANNED  # noqa: E402


def _run(**kw):
    return extract_records_multi(FREETEXT_MULTI_NOTE, FREETEXT_GAZETTEER, delimiter=DELIM, **kw)


def _struct(records):
    """Structural projection (id + segment + date/item) for oracle comparison;
    whole-note spans are checked separately by recovery."""
    return [
        {
            "id": r["id"],
            "segment_index": r["provenance"]["segment_index"],
            "entries": [{"date": e["date"], "item": e["item"]} for e in r["entries"]],
        }
        for r in records
    ]


class TestMultiMatchesOracle(unittest.TestCase):
    def test_accepted_records_equal_oracle(self):
        self.assertEqual(_struct(_run().records), FREETEXT_EXPECTED_MULTI_RECORDS)

    def test_quarantine_equals_oracle(self):
        q = [(s.index, s.reason) for s in _run().quarantined]
        self.assertEqual(q, FREETEXT_EXPECTED_MULTI_QUARANTINE)

    def test_every_segment_is_accounted_for(self):
        result = _run()
        self.assertEqual(
            len(result.records) + len(result.quarantined),
            FREETEXT_MULTI_NOTE.count(DELIM) + 1,  # N delimiters -> N+1 segments
        )

    def test_source_spans_recover_whole_note_surface(self):
        for r in _run().records:
            for e in r["entries"]:
                s, t = e["source_span"]
                self.assertEqual(
                    FREETEXT_MULTI_NOTE[s:t].casefold(), e["item"].casefold()
                )

    def test_patient_key_span_recovers_the_raw_id(self):
        for r in _run().records:
            s, t = r["provenance"]["patient_key_span"]
            self.assertEqual(FREETEXT_MULTI_NOTE[s:t], r["id"])


class TestNoBleed(unittest.TestCase):
    """The safety core: a surfaced line can never trace to another patient."""

    def test_each_entry_span_is_inside_its_own_segment(self):
        for r in _run().records:
            a, b = r["provenance"]["segment_span"]
            for e in r["entries"]:
                s, t = e["source_span"]
                self.assertTrue(a <= s and t <= b, f"{e} escapes segment {a,b}")

    def test_shared_item_yields_separate_records(self):
        # EXAMPLE-001 and EXAMPLE-002 both mention "poor sleep" — they must stay
        # two records (2 each), never one merged record of 4.
        recs = {r["id"]: r for r in _run().records}
        for rid in ("EXAMPLE-001", "EXAMPLE-002"):
            ps = [e for e in recs[rid]["entries"] if e["item"] == "poor sleep"]
            self.assertEqual(len(ps), 2)

    def test_engine_never_cross_attributes(self):
        reports = run_report(_run().records)
        by = {rep.record_id: rep for rep in reports}
        self.assertEqual(set(by), {"EXAMPLE-001", "EXAMPLE-002"})
        for rid in by:
            rec = [f for f in by[rid].findings if getattr(f.hit, "item", "") == "poor sleep"]
            self.assertTrue(rec and rec[0].hit.count == 2)

    def test_no_cross_patient_cooccurrence(self):
        # Two patients sharing item+date must NOT co-occur (co-occurrence is per
        # record). Feeding all accepted records yields no co-occurrence hit here.
        self.assertEqual(detect_cooccurrence(_run().records), [])

    def test_headerless_preamble_does_not_bleed_into_first_patient(self):
        # Segment 0 ("...headache noted in triage") is header-less -> quarantined;
        # its content must appear in NO accepted record.
        first_patient_at = FREETEXT_MULTI_NOTE.index("Patient: EXAMPLE-001")
        for r in _run().records:
            for e in r["entries"]:
                self.assertGreater(e["source_span"][0], first_patient_at)


class TestQuarantineReasons(unittest.TestCase):
    def test_missing_key_segments(self):
        q = {s.index: s.reason for s in _run().quarantined}
        self.assertEqual(q[0], "missing_key")
        self.assertEqual(q[3], "missing_key")

    def test_ambiguous_two_headers(self):
        q = {s.index: s.reason for s in _run().quarantined}
        self.assertEqual(q[4], "ambiguous_key")
        # Neither EXAMPLE-003 nor EXAMPLE-004 was accepted under either guess.
        ids = {r["id"] for r in _run().records}
        self.assertNotIn("EXAMPLE-003", ids)
        self.assertNotIn("EXAMPLE-004", ids)

    def test_duplicate_key_quarantines_all_colliding(self):
        result = _run()
        dups = [s.index for s in result.quarantined if s.reason == "duplicate_key"]
        self.assertEqual(dups, [5, 6])  # BOTH colliding segments, not just one
        self.assertNotIn("EXAMPLE-005", {r["id"] for r in result.records})

    def test_same_value_twice_in_one_segment_is_accepted(self):
        note = "Patient: EXAMPLE-007\nPatient: EXAMPLE-007\n2026-01-05 poor sleep.\n"
        result = extract_records_multi(note, FREETEXT_GAZETTEER, delimiter=DELIM)
        self.assertEqual([r["id"] for r in result.records], ["EXAMPLE-007"])
        self.assertEqual(result.quarantined, [])


class TestPerPatientShift(unittest.TestCase):
    def test_intervals_preserved_calendars_differ(self):
        recs = {r["id"]: r for r in _run(shift_by_id=FREETEXT_MULTI_SHIFTS).records}
        e2 = recs["EXAMPLE-002"]["entries"]
        d0 = datetime.date.fromisoformat(e2[0]["date"])
        d1 = datetime.date.fromisoformat(e2[1]["date"])
        self.assertEqual((d1 - d0).days, 37)            # interval preserved
        self.assertNotEqual(e2[0]["date"], "2026-01-06")  # calendar moved (shift 10000)
        self.assertEqual(recs["EXAMPLE-001"]["entries"][0]["date"], "2026-01-05")  # shift 0

    def test_missing_shift_defaults_zero_when_not_required(self):
        recs = {r["id"]: r for r in _run(shift_by_id={"EXAMPLE-001": 0}).records}
        self.assertEqual(recs["EXAMPLE-002"]["entries"][0]["date"], "2026-01-06")

    def test_missing_shift_quarantines_when_required(self):
        result = _run(shift_by_id={"EXAMPLE-001": 0}, require_shift=True)
        q = {s.index: s.reason for s in result.quarantined}
        self.assertEqual(q[2], "missing_shift")  # EXAMPLE-002 (segment 2) refused
        self.assertNotIn("EXAMPLE-002", {r["id"] for r in result.records})
        self.assertIn("EXAMPLE-001", {r["id"] for r in result.records})

    def test_bool_shift_value_rejected(self):
        with self.assertRaises(ValueError):
            _run(shift_by_id={"EXAMPLE-001": True})


class TestFailLoudConfig(unittest.TestCase):
    def test_empty_delimiter_raises(self):
        with self.assertRaises(ValueError):
            extract_records_multi(FREETEXT_MULTI_NOTE, FREETEXT_GAZETTEER, delimiter="")

    def test_whitespace_delimiter_raises(self):
        with self.assertRaises(ValueError):
            extract_records_multi(FREETEXT_MULTI_NOTE, FREETEXT_GAZETTEER, delimiter="   ")

    def test_non_dict_shift_by_id_raises(self):
        with self.assertRaises(ValueError):
            _run(shift_by_id=[("EXAMPLE-001", 0)])

    def test_non_bool_require_shift_raises(self):
        with self.assertRaises(ValueError):
            _run(require_shift="yes")

    def test_bad_data_never_raises(self):
        # An all-missing-key note returns a result (fail-closed), never crashes.
        result = extract_records_multi("no headers here.\n", FREETEXT_GAZETTEER, delimiter=DELIM)
        self.assertEqual(result.records, [])
        self.assertEqual([s.reason for s in result.quarantined], ["missing_key"])


class TestLibrarianRuleInRefusals(unittest.TestCase):
    def test_reasons_are_fixed_neutral_tokens(self):
        for s in _run().quarantined:
            self.assertIn(s.reason, _QUARANTINE_REASONS)

    def test_no_banned_words_in_details_or_entries(self):
        result = _run()
        for s in result.quarantined:
            for banned in BANNED:
                self.assertNotIn(banned, (s.reason + " " + s.detail).lower(), banned)
        for r in result.records:
            for e in r["entries"]:
                low = format_entry(e).lower()
                for banned in BANNED:
                    self.assertNotIn(banned, low, banned)

    def test_demo_output_is_banned_words_clean(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = _run_demo_multi()
        self.assertEqual(rc, 0)
        low = buf.getvalue().lower()
        for banned in BANNED:
            self.assertNotIn(banned, low, banned)


class TestParsePatientIdsHelper(unittest.TestCase):
    def test_returns_all_headers_with_whole_note_offsets(self):
        seg = "Patient: A\nPatient: B\n2026-01-01 poor sleep.\n"
        got = parse_patient_ids(seg, base_offset=100)
        self.assertEqual([v for v, _ in got], ["A", "B"])
        for value, start in got:
            self.assertEqual(seg[start - 100 : start - 100 + len(value)], value)

    def test_no_header_returns_empty(self):
        self.assertEqual(parse_patient_ids("2026-01-01 poor sleep.\n"), [])


class TestEndToEndMultiIntoEngine(unittest.TestCase):
    def test_provenance_block_does_not_perturb_engine(self):
        records = _run().records
        stripped = [{"id": r["id"], "entries": r["entries"]} for r in records]
        self.assertEqual(
            [(rep.record_id, len(rep.findings)) for rep in run_report(records)],
            [(rep.record_id, len(rep.findings)) for rep in run_report(stripped)],
        )


if __name__ == "__main__":
    unittest.main()
