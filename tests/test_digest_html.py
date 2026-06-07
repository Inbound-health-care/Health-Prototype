"""test_digest_html.py — the clinician Pre-visit Pattern Digest (digest_html.py, UI slice 2).

The digest is the PRODUCT view (ADR 0015) the Figma mock specified: the five surfacing
lenses as neutral cards beside the cited source note, distinct from report_html.py's
inspection view (ADR 0014). These tests assert it stays self-contained (no network /
external resources), that all five lenses actually surface from the synthetic sample
(its whole reason for being), that the cards cite real provenance and link to source
spans, that note content is HTML-escaped (no injection), and that the librarian rule
holds in the view layer too (no banned/interpretive words, no ranking). Pure stdlib.

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
    DIGEST_SAMPLE_GAZETTEER,
    DIGEST_SAMPLE_NOTE,
)
from digest_html import (  # noqa: E402
    build_demo_html,
    build_demo_multi_html,
    render_digest,
)
from extract import extract_records  # noqa: E402
from recurrence import run_report  # noqa: E402

# The librarian-rule banned words live once in tests/banned_words.py (shared union).
from tests.banned_words import BANNED  # noqa: E402

REF = datetime.date(2026, 3, 15)

# The five lens labels, exactly as the digest renders them (registry order).
LENSES = ("RECURRENCE", "GAP / RETURN", "FREQUENCY", "CO-OCCURRENCE", "CADENCE CHANGE")


def _demo_records():
    return extract_records(DIGEST_SAMPLE_NOTE, DIGEST_SAMPLE_GAZETTEER)


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


class TestAllFiveLensesSurface(unittest.TestCase):
    def test_every_lens_renders_a_card(self):
        # The digest's reason for being: one synthetic patient surfaces all five
        # lenses, so the clinician view shows a card per lens from real engine output.
        html = build_demo_html(REF)
        for lens in LENSES:
            self.assertIn(lens, html, f"missing lens card: {lens}")

    def test_card_count_matches_engine_findings(self):
        # The sample is tuned to surface exactly seven findings (recurrence x3 +
        # one each of gap / frequency / co-occurrence / cadence change). The cards
        # come straight from run_report, so the counts must agree.
        records = _demo_records()
        reports = run_report(records)
        n_findings = sum(len(r.findings) for r in reports)
        self.assertEqual(n_findings, 7)
        self.assertEqual(build_demo_html(REF).count('class="card finding"'), 7)

    def test_cooccurrence_is_a_pair_not_a_link(self):
        html = build_demo_html(REF)
        # The pair is presented as co-occurrence (counting), never as a relationship.
        self.assertIn("anxiety + poor sleep — appeared together on 2 dates", html)


class TestProvenanceIsVisible(unittest.TestCase):
    def test_cards_cite_their_dates(self):
        html = build_demo_html(REF)
        # Each lens cites concrete provenance the engine produced.
        self.assertIn("cited: 2025-10-24 → 2026-03-15", html)   # gap brackets
        self.assertIn("cited: 2026-02-02 … 2026-03-02", html)   # frequency window
        self.assertIn("cited: pivot 2026-01-29", html)          # cadence pivot

    def test_long_date_list_collapses_but_keeps_every_date(self):
        # A long list of cited dates is summarized to a count (scannable card),
        # but the full provenance stays in the document, one tap away — never
        # dropped or summarized away.
        html = build_demo_html(REF)
        self.assertIn('<details class="chip cites"><summary>cited: 6 dates</summary>', html)
        self.assertIn(
            "2025-10-01, 2025-11-10, 2025-12-20, 2026-01-29, 2026-02-14, 2026-03-02", html
        )
        # Short lists are not collapsed — a 2- or 3-date chip renders inline.
        self.assertNotIn("cited: 2 dates", html)
        self.assertNotIn("cited: 3 dates", html)
        self.assertIn("cited: 2026-02-14, 2026-03-02", html)    # co-occurrence inline

    def test_cards_link_to_concept_spans(self):
        html = build_demo_html(REF)
        # Every card item also exists as a clickable mark in the note (link integrity).
        for item in ("poor sleep", "anxiety", "lithium level"):
            self.assertIn(f'data-item="{item}"', html, f"no note mark for {item}")
            self.assertIn(item, html)
        self.assertIn('data-items="anxiety|poor sleep"', html)  # co-occurrence pair

    def test_note_content_is_escaped_no_injection(self):
        note = "Patient: EX-1\n2026-01-05 <script>alert(1)</script> poor sleep.\n"
        records = extract_records(note, ["poor sleep"])
        html = render_digest(note, records, run_report(records))
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)", html)


class TestLibrarianRuleInTheView(unittest.TestCase):
    def test_no_banned_words_anywhere(self):
        html = build_demo_html(REF).lower()
        for banned in BANNED:
            self.assertNotIn(banned, html, f"banned word in digest HTML: {banned!r}")

    def test_empty_report_does_not_assert_clean(self):
        html = render_digest("Patient: EX-1\n", [{"id": "EX-1", "entries": []}], [])
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn("No patterns surfaced", html)
        for banned in BANNED:
            self.assertNotIn(banned, html.lower(), banned)


class TestMultiPatientDigest(unittest.TestCase):
    """The multi-patient batch view (ADR 0016 batch -> stacked digest): one block
    per accepted patient in segment order, a jump index, a neutral quarantine
    section, and — the load-bearing guarantee — no cross-patient highlight bleed."""

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
        # Each accepted patient surfaces its recurrence card from real engine output.
        self.assertEqual(html.count('class="card finding"'), 2)

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
            self.assertNotIn(banned, html, f"banned word in multi digest HTML: {banned!r}")


if __name__ == "__main__":
    unittest.main()
