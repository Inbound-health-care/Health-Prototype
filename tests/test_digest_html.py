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
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import (  # noqa: E402
    DIGEST_SAMPLE_GAZETTEER,
    DIGEST_SAMPLE_NOTE,
)
from digest_html import build_demo_html, render_digest  # noqa: E402
from extract import extract_records  # noqa: E402
from recurrence import run_report  # noqa: E402

# The suite-wide union of interpretive / ranking words the librarian rule forbids in
# output. Mirrors tests/test_report_html.py; the digest must add none either.
BANNED = (
    "worsening", "worsen", "severe", "severity", "suggests", "diagnos", "risk",
    "concern", "caution", "abnormal", "score", "relapse", "acute", "accelerat",
    "decelerat", "increasing", "decreasing", "escalat", "declining", "deteriorat",
    "improving", "trend", "associated", "correlated", "linked", "cause", "caused",
    "relationship", "top", "most", "priority", "prioritize", "rank", "ranking",
    "total", "highest", "lowest", "worst", "best",
)

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
        self.assertIn("anxiety + poor sleep — co-noted on 2 dates", html)


class TestProvenanceIsVisible(unittest.TestCase):
    def test_cards_cite_their_dates(self):
        html = build_demo_html(REF)
        # Each lens cites concrete provenance the engine produced.
        self.assertIn("cited: 2025-10-24 → 2026-03-15", html)   # gap brackets
        self.assertIn("cited: 2026-02-02 … 2026-03-02", html)   # frequency window
        self.assertIn("cited: pivot 2026-01-29", html)          # cadence pivot

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


if __name__ == "__main__":
    unittest.main()
