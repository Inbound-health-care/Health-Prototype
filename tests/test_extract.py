"""
test_extract.py — the free-text extraction front-end (extract.py, slice 1).

extract_records turns dated-line prose into the engine's canonical record shape;
recurrence.py's five rules then consume it UNCHANGED. These tests assert the
hand-written FREETEXT oracle (items, dates, and exact char-offset spans), the
longest-match / word-boundary matching, case-insensitivity, the three explicit
date formats and the de-identifying date shift (intervals preserved), the
allowlist (only curated concepts can surface through matching), the librarian rule
in output (Stance A: literal mentions, no interpretation, no context_cue), input
validation, and the end-to-end bridge into detect_recurrence.

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import (  # noqa: E402
    FREETEXT_EXPECTED_RECORDS,
    FREETEXT_EXPECTED_RECORDS_RELATIVE,
    FREETEXT_GAZETTEER,
    FREETEXT_RELATIVE_NOTE,
    FREETEXT_SAMPLE_NOTE,
)
from extract import (  # noqa: E402
    extract_entries,
    extract_records,
    find_gazetteer_hits,
    format_entry,
    parse_patient_id,
    shift_date,
)
from recurrence import detect_recurrence  # noqa: E402
from tests.banned_words import BANNED  # noqa: E402


class TestExtractMatchesOracle(unittest.TestCase):
    def test_records_equal_oracle(self):
        self.assertEqual(
            extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER),
            FREETEXT_EXPECTED_RECORDS,
        )

    def test_source_spans_recover_surface_text(self):
        # Every span points at text that casefold-equals its item.
        for entry in FREETEXT_EXPECTED_RECORDS[0]["entries"]:
            start, end = entry["source_span"]
            surface = FREETEXT_SAMPLE_NOTE[start:end]
            self.assertEqual(surface.casefold(), entry["item"].casefold())


class TestLongestMatchAndOverlap(unittest.TestCase):
    def test_poor_sleep_beats_inner_sleep(self):
        # The longer term wins; the "sleep" inside "poor sleep" is not emitted.
        self.assertEqual(
            find_gazetteer_hits("poor sleep", ["poor sleep", "sleep"]),
            [(0, 10, "poor sleep")],
        )

    def test_standalone_sleep_still_matches(self):
        # With no "poor" present, the shorter term fires (case-insensitive).
        self.assertEqual(
            find_gazetteer_hits("Sleep improved", ["poor sleep", "sleep"]),
            [(0, 5, "sleep")],
        )


class TestCaseInsensitivity(unittest.TestCase):
    def test_surface_casing_maps_to_canonical_item(self):
        entries = extract_entries(
            "2026-02-10 Poor sleep. Headache. Sleep.\n", FREETEXT_GAZETTEER
        )
        self.assertEqual(
            [e["item"] for e in entries], ["poor sleep", "headache", "sleep"]
        )


class TestWordBoundaries(unittest.TestCase):
    def test_substring_inside_word_does_not_match(self):
        # "sleep" must not match inside "asleep" or "sleeps".
        self.assertEqual(
            find_gazetteer_hits("He fell asleep; she sleeps.", ["sleep"]), []
        )

    def test_multiword_term_matches_with_internal_space(self):
        self.assertEqual(
            find_gazetteer_hits("has chest pain today", ["chest pain"]),
            [(4, 14, "chest pain")],
        )


class TestDateExtraction(unittest.TestCase):
    def test_iso_us_and_monname_all_parse_to_same_date(self):
        for line in (
            "2026-01-05 poor sleep\n",
            "1/5/2026 poor sleep\n",
            "Jan 5 2026 poor sleep\n",
        ):
            entries = extract_entries(line, FREETEXT_GAZETTEER)
            self.assertEqual(len(entries), 1, line)
            self.assertEqual(entries[0]["date"], "2026-01-05", line)
            self.assertEqual(entries[0]["item"], "poor sleep", line)

    def test_undated_line_yields_no_entries(self):
        self.assertEqual(extract_entries("poor sleep today\n", FREETEXT_GAZETTEER), [])

    def test_malformed_date_is_skipped_not_raised(self):
        # 2026-13-40 is not a real date -> the line is not "dated" -> no entries.
        self.assertEqual(
            extract_entries("2026-13-40 poor sleep\n", FREETEXT_GAZETTEER), []
        )

    def test_relative_date_words_are_ignored(self):
        # "x3 weeks"/"today" never become or alter the date; the explicit one wins.
        entries = extract_entries(
            "2026-01-05 poor sleep x3 weeks today\n", FREETEXT_GAZETTEER
        )
        self.assertEqual([e["date"] for e in entries], ["2026-01-05"])


class TestDateShiftDeIdentification(unittest.TestCase):
    def test_default_shift_is_identity(self):
        self.assertEqual(
            extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER),
            FREETEXT_EXPECTED_RECORDS,
        )

    def test_shift_moves_every_date_equally_and_never_the_span(self):
        shift = 10_000
        base = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
        shifted = extract_records(
            FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, date_shift_days=shift
        )
        for b, s in zip(base[0]["entries"], shifted[0]["entries"]):
            d_b = datetime.date.fromisoformat(b["date"])
            d_s = datetime.date.fromisoformat(s["date"])
            self.assertEqual((d_s - d_b).days, shift)
            self.assertEqual(b["source_span"], s["source_span"])

    def test_shift_preserves_intervals_and_recurrence(self):
        records = extract_records(
            FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, date_shift_days=-3650
        )
        hits = {h.item: h for h in detect_recurrence(records)}
        self.assertIn("poor sleep", hits)
        self.assertEqual(hits["poor sleep"].count, 2)
        d0, d1 = (datetime.date.fromisoformat(x) for x in hits["poor sleep"].dates)
        self.assertEqual((d1 - d0).days, 36)  # 2026-01-05 -> 2026-02-10 preserved


class TestAllowlist(unittest.TestCase):
    """ADR 0009 Layer 1: only gazetteer concepts surface; identifiers cannot."""

    def test_patient_header_value_is_id_not_entry(self):
        records = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
        self.assertEqual(records[0]["id"], "EXAMPLE-001")
        for entry in records[0]["entries"]:
            self.assertNotIn("EXAMPLE", entry["item"])

    def test_identifiers_never_become_entries(self):
        note = (
            "Patient: EXAMPLE-002\n"
            "2026-01-05 John Smith SSN 000-00-0000 MRN 0000000 reports poor sleep.\n"
        )
        records = extract_records(note, FREETEXT_GAZETTEER)
        self.assertEqual([e["item"] for e in records[0]["entries"]], ["poor sleep"])

    def test_no_patient_header_yields_no_records(self):
        self.assertEqual(
            extract_records("2026-01-05 poor sleep\n", FREETEXT_GAZETTEER), []
        )


class TestLibrarianRuleBannedWords(unittest.TestCase):
    """Stance A: the front-end surfaces literal mentions and adds no judgment.

    Checks the full suite-wide union (tests/banned_words.py); the front-end must add none.
    """

    BANNED = BANNED  # the shared suite-wide union — see tests/banned_words.py

    def test_rendered_entries_have_no_banned_words(self):
        records = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
        for entry in records[0]["entries"]:
            line = format_entry(entry).lower()
            self.assertIn(entry["item"], line)  # provenance present
            for banned in self.BANNED:
                self.assertNotIn(banned, line, f"banned word: {banned!r}")

    def test_stance_a_emits_no_context_cue(self):
        records = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
        for entry in records[0]["entries"]:
            self.assertNotIn("context_cue", entry)


class TestEndToEndIntoEngine(unittest.TestCase):
    def test_extract_then_detect_recurrence(self):
        records = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
        hits = detect_recurrence(records)
        self.assertEqual(len(hits), 1)
        hit = hits[0]
        self.assertEqual(hit.record_id, "EXAMPLE-001")
        self.assertEqual(hit.item, "poor sleep")
        self.assertEqual(hit.count, 2)
        self.assertEqual(hit.dates, ["2026-01-05", "2026-02-10"])

    def test_source_span_does_not_perturb_rules(self):
        records = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
        stripped = [
            {
                "id": r["id"],
                "entries": [
                    {"date": e["date"], "item": e["item"]} for e in r["entries"]
                ],
            }
            for r in records
        ]
        self.assertEqual(detect_recurrence(records), detect_recurrence(stripped))


class TestExtractHelpers(unittest.TestCase):
    def test_parse_patient_id_reads_header(self):
        self.assertEqual(parse_patient_id("Patient:  EX-7 \n2026-01-01 x\n"), "EX-7")

    def test_parse_patient_id_absent_is_none(self):
        self.assertIsNone(parse_patient_id("2026-01-01 poor sleep\n"))

    def test_shift_date_preserves_interval(self):
        a = shift_date(datetime.date(2026, 1, 5), 100)
        b = shift_date(datetime.date(2026, 2, 10), 100)
        self.assertEqual((b - a).days, 36)


class TestInputValidation(unittest.TestCase):
    """Invalid parameters fail loudly (library code raises, never misbehaves)."""

    def test_empty_gazetteer_raises(self):
        with self.assertRaises(ValueError):
            extract_records(FREETEXT_SAMPLE_NOTE, [])

    def test_non_str_gazetteer_term_raises(self):
        with self.assertRaises(ValueError):
            extract_records(FREETEXT_SAMPLE_NOTE, ["poor sleep", 123])

    def test_non_int_shift_raises(self):
        with self.assertRaises(ValueError):
            extract_records(
                FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, date_shift_days="x"
            )


class TestRelativeDateAnchoring(unittest.TestCase):
    """ADR 0013: opt-in, conservative relative-date anchoring. OFF by default
    (byte-for-byte explicit behavior); when on, explicitly-anchored relatives
    resolve, while partial/frequency/anchorless phrases stay undated but cited —
    never guessed."""

    REF = datetime.date(2026, 3, 15)

    def test_records_equal_oracle(self):
        self.assertEqual(
            extract_records(
                FREETEXT_RELATIVE_NOTE,
                FREETEXT_GAZETTEER,
                resolve_relative=True,
                reference_date=self.REF,
            ),
            FREETEXT_EXPECTED_RECORDS_RELATIVE,
        )

    def test_default_off_is_explicit_only_and_unannotated(self):
        # Relative off (default): unanchored lines are skipped, exactly as before;
        # the one explicit line carries no extra fields.
        records = extract_records(FREETEXT_RELATIVE_NOTE, FREETEXT_GAZETTEER)
        self.assertEqual(len(records[0]["entries"]), 1)
        only = records[0]["entries"][0]
        self.assertEqual(only["date"], "2026-03-15")
        self.assertNotIn("date_kind", only)

    def test_weeks_ago_resolves_against_reference(self):
        entries = extract_entries(
            "3 weeks ago poor sleep.\n",
            FREETEXT_GAZETTEER,
            resolve_relative=True,
            reference_date=self.REF,
        )
        self.assertEqual(entries[0]["date"], "2026-02-22")
        self.assertEqual(entries[0]["date_kind"], "relative")
        self.assertEqual(entries[0]["date_phrase"], "3 weeks ago")

    def test_months_ago_clamps_day_not_raises(self):
        # 2026-03-31 - 1 month -> 2026-02-28 (clamp; 2026 is not a leap year).
        entries = extract_entries(
            "1 month ago poor sleep.\n",
            FREETEXT_GAZETTEER,
            resolve_relative=True,
            reference_date=datetime.date(2026, 3, 31),
        )
        self.assertEqual(entries[0]["date"], "2026-02-28")

    def test_since_date_resolves_without_anchor(self):
        entries = extract_entries(
            "since 2026-02-01 chest pain.\n",
            FREETEXT_GAZETTEER,
            resolve_relative=True,  # no reference_date needed: the date is explicit
        )
        self.assertEqual(entries[0]["date"], "2026-02-01")
        self.assertEqual(entries[0]["date_kind"], "relative")

    def test_frequency_is_surfaced_but_never_dated(self):
        entries = extract_entries(
            "q2wk sleep.\n", FREETEXT_GAZETTEER, resolve_relative=True
        )
        self.assertEqual(entries[0]["date"], "")
        self.assertEqual(entries[0]["date_kind"], "frequency")
        self.assertEqual(entries[0]["item"], "sleep")

    def test_partial_month_year_is_undated(self):
        entries = extract_entries(
            "March 2026 poor sleep.\n",
            FREETEXT_GAZETTEER,
            resolve_relative=True,
            reference_date=self.REF,
        )
        self.assertEqual(entries[0]["date"], "")
        self.assertEqual(entries[0]["date_kind"], "partial")
        self.assertEqual(entries[0]["date_phrase"], "March 2026")

    def test_anchorless_relative_is_unresolved_not_guessed(self):
        entries = extract_entries(
            "3 weeks ago poor sleep.\n", FREETEXT_GAZETTEER, resolve_relative=True
        )
        self.assertEqual(entries[0]["date"], "")
        self.assertEqual(entries[0]["date_kind"], "unresolved")
        self.assertEqual(entries[0]["date_phrase"], "3 weeks ago")

    def test_spans_recover_phrase_and_item_text(self):
        records = extract_records(
            FREETEXT_RELATIVE_NOTE,
            FREETEXT_GAZETTEER,
            resolve_relative=True,
            reference_date=self.REF,
        )
        for entry in records[0]["entries"]:
            if "date_span" in entry:
                start, end = entry["date_span"]
                self.assertEqual(
                    FREETEXT_RELATIVE_NOTE[start:end], entry["date_phrase"]
                )
            start, end = entry["source_span"]
            self.assertEqual(
                FREETEXT_RELATIVE_NOTE[start:end].casefold(), entry["item"].casefold()
            )

    def test_shift_preserves_relative_explicit_interval(self):
        records = extract_records(
            FREETEXT_RELATIVE_NOTE,
            FREETEXT_GAZETTEER,
            resolve_relative=True,
            reference_date=self.REF,
            date_shift_days=-3650,
        )
        by_span = {tuple(e["source_span"]): e for e in records[0]["entries"]}
        explicit = datetime.date.fromisoformat(by_span[(32, 42)]["date"])
        relative = datetime.date.fromisoformat(by_span[(56, 66)]["date"])
        self.assertEqual((explicit - relative).days, 21)  # 03-15 vs 02-22 preserved

    def test_relative_records_feed_engine_unchanged(self):
        records = extract_records(
            FREETEXT_RELATIVE_NOTE,
            FREETEXT_GAZETTEER,
            resolve_relative=True,
            reference_date=self.REF,
        )
        hits = {h.item: h for h in detect_recurrence(records)}
        # poor sleep on 2026-03-15 (explicit) + 2026-02-22 (relative); the
        # undated frequency "sleep" entry is dropped by the engine.
        self.assertIn("poor sleep", hits)
        self.assertEqual(hits["poor sleep"].count, 2)
        self.assertEqual(hits["poor sleep"].dates, ["2026-02-22", "2026-03-15"])

    def test_relative_entries_have_no_banned_words(self):
        records = extract_records(
            FREETEXT_RELATIVE_NOTE,
            FREETEXT_GAZETTEER,
            resolve_relative=True,
            reference_date=self.REF,
        )
        for entry in records[0]["entries"]:
            line = format_entry(entry).lower()
            self.assertIn(entry["item"], line)
            for banned in TestLibrarianRuleBannedWords.BANNED:
                self.assertNotIn(banned, line, f"banned word: {banned!r}")

    def test_reference_date_without_resolve_raises(self):
        with self.assertRaises(ValueError):
            extract_records(
                FREETEXT_RELATIVE_NOTE, FREETEXT_GAZETTEER, reference_date=self.REF
            )

    def test_bad_reference_date_type_raises(self):
        with self.assertRaises(ValueError):
            extract_records(
                FREETEXT_RELATIVE_NOTE,
                FREETEXT_GAZETTEER,
                resolve_relative=True,
                reference_date="2026-03-15",
            )

    def test_non_bool_resolve_relative_raises(self):
        with self.assertRaises(ValueError):
            extract_records(
                FREETEXT_RELATIVE_NOTE, FREETEXT_GAZETTEER, resolve_relative="yes"
            )


if __name__ == "__main__":
    unittest.main()
