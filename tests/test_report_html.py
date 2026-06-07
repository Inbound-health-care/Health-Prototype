"""test_report_html.py — the self-contained HTML view (report_html.py, UI slice 1).

The renderer visualizes provenance the engine already produces: cited spans in the
source note beside the patterns the five rules surface. These tests assert it stays
self-contained (no network / external resources), that every cited span is marked and
recovers its source text, that findings link to their cited concept spans, that note
content is HTML-escaped (no injection), and that the librarian rule holds in the view
layer too (no banned/interpretive words, no ranking). Pure stdlib.

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import datetime
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import (  # noqa: E402
    FREETEXT_GAZETTEER,
    FREETEXT_RELATIVE_NOTE,
)
from extract import extract_records  # noqa: E402
from recurrence import run_report  # noqa: E402
from report_html import build_demo_html, build_demo_multi_html, render_html  # noqa: E402

# The librarian-rule banned words live once in tests/banned_words.py (shared union).
from tests.banned_words import BANNED  # noqa: E402

REF = datetime.date(2026, 3, 15)


def _demo_records():
    return extract_records(
        FREETEXT_RELATIVE_NOTE,
        FREETEXT_GAZETTEER,
        resolve_relative=True,
        reference_date=REF,
    )


class TestSelfContained(unittest.TestCase):
    def test_is_a_single_self_contained_document(self):
        html = build_demo_html(REF)
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn("</html>", html)
        # No network / external resources: inline CSS+JS only.
        for forbidden in ("http://", "https://", "<link", "src=", "cdn", "@import"):
            self.assertNotIn(forbidden, html, forbidden)

    def test_deterministic(self):
        self.assertEqual(build_demo_html(REF), build_demo_html(REF))


class TestProvenanceIsVisible(unittest.TestCase):
    def test_every_cited_span_is_marked_and_recovers_source(self):
        records = _demo_records()
        html = render_html(
            FREETEXT_RELATIVE_NOTE, records, run_report(records), reference_date=REF
        )
        from html import escape

        for entry in records[0]["entries"]:
            start, end = entry["source_span"]
            surface = escape(FREETEXT_RELATIVE_NOTE[start:end], quote=True)
            # The exact source text sits inside a closing <mark> (longest-match,
            # so the surface equals the note slice).
            self.assertIn(f">{surface}</mark>", html)

    def test_relative_date_phrases_are_also_cited(self):
        records = _demo_records()
        html = render_html(FREETEXT_RELATIVE_NOTE, records, run_report(records))
        # The cited temporal phrase (ADR 0013) is highlighted as a date span.
        self.assertIn('cite-date', html)
        self.assertIn("3 weeks ago", html)

    def test_findings_link_to_concept_spans(self):
        records = _demo_records()
        html = render_html(FREETEXT_RELATIVE_NOTE, records, run_report(records))
        # The recurrence finding for "poor sleep" must reference an item that exists
        # as a clickable mark in the note (link integrity).
        self.assertIn('data-items="poor sleep"', html)
        self.assertIn('data-item="poor sleep"', html)

    def test_note_content_is_escaped_no_injection(self):
        note = "Patient: EX-1\n2026-01-05 <script>alert(1)</script> poor sleep.\n"
        records = extract_records(note, FREETEXT_GAZETTEER)
        html = render_html(note, records, run_report(records))
        # The note's angle brackets are escaped; the raw injected tag never appears.
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)", html)


class TestLibrarianRuleInTheView(unittest.TestCase):
    def test_no_banned_words_anywhere(self):
        html = build_demo_html(REF).lower()
        for banned in BANNED:
            self.assertNotIn(banned, html, f"banned word in HTML: {banned!r}")

    def test_empty_report_does_not_assert_clean(self):
        html = render_html("Patient: EX-1\n", [{"id": "EX-1", "entries": []}], [])
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn("No patterns surfaced", html)
        # Surfaces nothing; never claims the record is clean of patterns.
        for banned in BANNED:
            self.assertNotIn(banned, html.lower(), banned)


class TestMultiPatientReport(unittest.TestCase):
    """The multi-patient batch inspection view (ADR 0021): the inspection idiom (a
    findings LIST per patient) brought to parity with the digest (ADR 0020) — one
    block per accepted patient in segment order, a jump index, a neutral quarantine
    section, and the load-bearing guarantee: no cross-patient highlight bleed."""

    def _block(self, html, patient_id):
        # The HTML for exactly one patient's <section> (anchor id -> first </section>).
        m = re.search(r'id="patient-%s".*?</section>' % re.escape(patient_id), html, re.S)
        self.assertIsNotNone(m, f"no rendered block for {patient_id}")
        return m.group(0)

    def test_is_a_single_self_contained_document(self):
        html = build_demo_multi_html(REF)
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn("</html>", html)
        for forbidden in ("http://", "https://", "<link", "src=", "cdn", "@import"):
            self.assertNotIn(forbidden, html, forbidden)

    def test_deterministic(self):
        self.assertEqual(build_demo_multi_html(REF), build_demo_multi_html(REF))

    def test_one_block_per_accepted_patient_in_segment_order(self):
        html = build_demo_multi_html(REF)
        self.assertIn('id="patient-EXAMPLE-001"', html)
        self.assertIn('id="patient-EXAMPLE-002"', html)
        # Segment order (001 before 002), never reordered.
        self.assertLess(
            html.index('id="patient-EXAMPLE-001"'),
            html.index('id="patient-EXAMPLE-002"'),
        )
        # Inspection idiom: a findings list per patient (not the digest's cards).
        # Each accepted patient surfaces its one recurrence finding (poor sleep 2x).
        self.assertEqual(html.count('<li class="finding"'), 2)

    def test_patient_index_jumps_to_each_patient(self):
        html = build_demo_multi_html(REF)
        self.assertIn('class="patient-index"', html)
        self.assertIn('href="#patient-EXAMPLE-001"', html)
        self.assertIn('href="#patient-EXAMPLE-002"', html)

    def test_quarantine_section_surfaces_refused_segments_neutrally(self):
        # The five refused segments (2x missing_key, 1x ambiguous_key, 2x duplicate_key)
        # are surfaced with their engine reason code — never merged, guessed, or judged.
        html = build_demo_multi_html(REF)
        self.assertIn("Quarantined segments", html)
        for reason in ("missing_key", "ambiguous_key", "duplicate_key"):
            self.assertIn(reason, html)

    def test_no_cross_patient_highlight_bleed(self):
        # The guarantee: each patient renders its OWN source segment only, so a click
        # can never light up another patient's marks. Two patients SHARE "poor sleep";
        # prove each block carries only its own dates (structural isolation).
        html = build_demo_multi_html(REF)
        b1 = self._block(html, "EXAMPLE-001")
        b2 = self._block(html, "EXAMPLE-002")
        self.assertIn("2026-01-05", b1)  # 001's own date
        self.assertNotIn("2026-02-12", b1)  # 002's date must NOT appear in 001's block
        self.assertIn("2026-02-12", b2)  # 002's own date
        self.assertNotIn("2026-01-05", b2)  # 001's date must NOT appear in 002's block
        # Both blocks still carry the shared concept mark (each scoped to its own note).
        self.assertIn('data-item="poor sleep"', b1)
        self.assertIn('data-item="poor sleep"', b2)

    def test_no_banned_words_anywhere(self):
        html = build_demo_multi_html(REF).lower()
        for banned in BANNED:
            self.assertNotIn(banned, html, f"banned word in multi report HTML: {banned!r}")


if __name__ == "__main__":
    unittest.main()
