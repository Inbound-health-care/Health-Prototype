"""test_view_html.py — the shared view floor (view_html.py, ADR 0021).

view_html.py is the dependency FLOOR for the two HTML views: it holds the one
source of truth for the calm theme, neutral span rendering, HTML-escaping, the
click-to-highlight scripts, and the multi-patient chrome (jump-index, quarantine,
per-patient scoped JS). report_html.py and digest_html.py both import FROM it;
neither imports from the other (that would be circular). These tests prove the
no-cycle dependency direction, the back-compat re-export of THEME, that the moved
multi-patient primitives are reachable here, and that the librarian rule holds in
the shared static strings (no banned/interpretive words). Pure stdlib.

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import datetime
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import digest_html  # noqa: E402
import report_html  # noqa: E402
import view_html  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REF = datetime.date(2026, 3, 15)


def _all_demos() -> dict[str, str]:
    """Every view surface (both views, single + multi) keyed by a readable name, so
    a shared-layer guarantee can be asserted across all four at once."""
    return {
        "report": report_html.build_demo_html(REF),
        "report-multi": report_html.build_demo_multi_html(REF),
        "digest": digest_html.build_demo_html(REF),
        "digest-multi": digest_html.build_demo_multi_html(REF),
    }

# The librarian-rule banned words live once in tests/banned_words.py (shared union).
from tests.banned_words import BANNED  # noqa: E402


class TestSharedModuleIsTheFloor(unittest.TestCase):
    """view_html imports nothing from the two views (no cycle); each module also
    imports standalone."""

    def _import_alone(self, module: str) -> str:
        # A fresh interpreter so nothing else has pre-populated sys.modules.
        code = (
            f"import {module}, sys; "
            "print('report_html' in sys.modules, 'digest_html' in sys.modules)"
        )
        out = subprocess.run(
            [sys.executable, "-c", code],
            cwd=_ROOT, capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()

    def test_view_html_does_not_import_the_views(self):
        # Importing the floor must NOT drag in either view (that would be a cycle).
        self.assertEqual(self._import_alone("view_html"), "False False")

    def test_each_view_imports_standalone(self):
        # Both views import cleanly on their own (they pull the floor, not each other).
        for module in ("report_html", "digest_html"):
            with self.subTest(module=module):
                subprocess.run(
                    [sys.executable, "-c", f"import {module}"],
                    cwd=_ROOT, capture_output=True, text=True, check=True,
                )


class TestReExportIdentity(unittest.TestCase):
    def test_theme_is_one_object_across_modules(self):
        # THEME is defined once in view_html and re-exported by report_html for
        # back-compat (tests/test_view_theme.py imports it from report_html). One
        # object, so the two views can never drift on colour.
        import digest_html
        import report_html

        self.assertIs(report_html.THEME, view_html.THEME)
        # Both views render through the SAME neutral-span helper (one provenance path).
        self.assertIs(report_html._render_note, view_html._render_note)
        self.assertIs(digest_html._render_note, view_html._render_note)
        self.assertIs(report_html._JS, view_html._JS)


class TestMultiPrimitivesAvailable(unittest.TestCase):
    def test_multi_patient_helpers_live_in_the_floor(self):
        # The multi-patient primitives were promoted out of digest_html into the
        # shared floor (ADR 0021) so report_html can reuse them without a cycle.
        for name in (
            "_anchor_id", "_localized_note", "_render_patient_index",
            "_render_quarantine", "_QUARANTINE_LABELS", "_MULTI_JS",
            "_MULTI_CHROME_CSS", "_collect_spans", "_render_note", "_esc", "_JS",
        ):
            self.assertTrue(hasattr(view_html, name), f"view_html missing {name}")

    def test_anchor_id_is_safe(self):
        self.assertEqual(view_html._anchor_id("EXAMPLE-001"), "patient-EXAMPLE-001")
        # Non-alnum collapses to '-' (no broken/unsafe anchors).
        self.assertEqual(view_html._anchor_id("a/b c"), "patient-a-b-c")

    def test_quarantine_empty_does_not_assert_clean(self):
        # No refused segments -> nothing rendered (never an "all clean" claim).
        self.assertEqual(view_html._render_quarantine([]), "")


class TestLibrarianRuleInSharedStrings(unittest.TestCase):
    def test_no_banned_words_in_static_strings(self):
        blobs = [
            view_html._THEME_CSS, view_html._THEME_JS, view_html._THEME_MEDIA_CSS,
            view_html._JS, view_html._MULTI_JS, view_html._INTERACT_JS,
            view_html._MULTI_CHROME_CSS, view_html._PRINT_CSS,
            " ".join(view_html._QUARANTINE_LABELS.values()),
            " ".join(view_html._QUARANTINE_LABELS.keys()),
        ]
        haystack = " ".join(blobs).lower()
        for banned in BANNED:
            self.assertNotIn(banned, haystack, f"banned word in shared string: {banned!r}")


class TestKeyboardAndAria(unittest.TestCase):
    """Keyboard nav + ARIA (ADR 0022), in the shared layer so every view inherits it:
    findings are focusable button-toggles operable by mouse AND keyboard, with a
    visible focus ring and a reflected pressed state."""

    def test_findings_are_focusable_button_toggles(self):
        for name, html in _all_demos().items():
            with self.subTest(view=name):
                # Static markup carries the a11y semantics (present before JS runs).
                # Findings are real <button>s — native focus + Enter/Space — and valid
                # inside a list, not a role=button shim on an <li> (ADR 0026).
                self.assertIn('<button type="button" class="finding"', html)
                self.assertIn('aria-pressed="false"', html)
                self.assertNotIn('role="button"', html)
                # A visible focus indicator using the (3:1-checked) accent-line token.
                self.assertIn(".finding:focus-visible", html)
                self.assertIn("var(--accent-line)", html)

    def test_one_activation_path_no_duplicated_handler(self):
        # Mouse and keyboard share ONE bindFindings/activate body, defined once per
        # page (the single-scope and multi-scope callers both reuse it).
        for name, html in _all_demos().items():
            with self.subTest(view=name):
                self.assertEqual(html.count("function bindFindings"), 1, name)
                self.assertEqual(html.count("function activate"), 1, name)

    def test_pressed_state_count_matches_findings(self):
        # Every finding declares aria-pressed; the count tracks the rendered findings
        # (no stray or missing toggle).
        for name, html in _all_demos().items():
            with self.subTest(view=name):
                n_findings = html.count('class="finding"')
                self.assertGreater(n_findings, 0, name)
                self.assertEqual(html.count('aria-pressed="false"'), n_findings, name)


class TestPrint(unittest.TestCase):
    """Print pass (ADR 0022): a clinician hands the page off on paper — single
    column, no on-screen chrome, grayscale-legible marks, full provenance expanded."""

    def test_print_stylesheet_is_present_and_complete(self):
        for name, html in _all_demos().items():
            with self.subTest(view=name):
                self.assertIn("@media print", html)
                self.assertIn("@page", html)
                # On-screen chrome dropped; marks stay legible without colour.
                self.assertIn(".theme-toggle, footer { display: none; }", html)
                self.assertIn("mark.cite { border: 1px solid currentColor;", html)
                # Collapsed cited-date lists print in full (CSS fallback).
                self.assertIn("details > .cites-full { display: block; }", html)
                # Blocks do not split across a page (logical break, no `top` token).
                self.assertIn("break-inside: avoid", html)

    def test_details_are_forced_open_for_print(self):
        # CSS cannot set a <details> open state, so a beforeprint/afterprint handler
        # opens every disclosure for printing and restores it after.
        for name, html in _all_demos().items():
            with self.subTest(view=name):
                self.assertIn("beforeprint", html)
                self.assertIn("afterprint", html)

    def test_print_strings_have_no_banned_words(self):
        haystack = (view_html._PRINT_CSS + view_html._THEME_JS).lower()
        for banned in BANNED:
            self.assertNotIn(banned, haystack, f"banned word in print string: {banned!r}")


class _Hit:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class _Finding:
    def __init__(self, expert, hit):
        self.expert = expert
        self.hit = hit


class TestTimelineAxis(unittest.TestCase):
    """The at-a-glance timeline (ADR 0023): axis math + neutral row extraction."""

    def test_axis_bounds(self):
        d = datetime.date
        self.assertEqual(
            view_html._axis_bounds(["2026-03-01", "2026-01-01", "2026-02-01"]),
            (d(2026, 1, 1), d(2026, 3, 1)),
        )
        # Undated "" is ignored; duplicates collapse.
        self.assertEqual(
            view_html._axis_bounds(["", "2026-01-01", "2026-01-01", "2026-03-01"]),
            (d(2026, 1, 1), d(2026, 3, 1)),
        )
        # Fewer than two distinct dated points -> no axis to draw.
        self.assertIsNone(view_html._axis_bounds([]))
        self.assertIsNone(view_html._axis_bounds(["2026-01-01"]))
        self.assertIsNone(view_html._axis_bounds(["2026-01-01", "2026-01-01"]))

    def test_tick_offset(self):
        d = datetime.date
        lo, hi = d(2026, 1, 1), d(2026, 3, 2)  # 60-day span
        self.assertEqual(view_html._tick_offset(lo, lo, hi), 0.0)
        self.assertEqual(view_html._tick_offset(hi, lo, hi), 100.0)
        self.assertAlmostEqual(view_html._tick_offset(d(2026, 1, 31), lo, hi), 50.0)
        # Out of range clamps to 0..100; a zero-span places at the midpoint.
        self.assertEqual(view_html._tick_offset(d(2025, 1, 1), lo, hi), 0.0)
        self.assertEqual(view_html._tick_offset(d(2027, 1, 1), lo, hi), 100.0)
        self.assertEqual(view_html._tick_offset(lo, lo, lo), 50.0)

    def test_rows_one_per_finding_in_order(self):
        findings = [
            _Finding("recurrence", _Hit(item="poor sleep", dates=["2026-01-01", "2026-02-01"])),
            _Finding("cooccurrence", _Hit(item_a="anxiety", item_b="poor sleep",
                                          dates=["2026-03-01", "2026-03-15"])),
            # gap carries before/after, not a dates list.
            _Finding("gap", _Hit(item="depression", before_date="2026-01-01", after_date="2026-06-01")),
            # a finding with no cited dates is dropped (nothing to place).
            _Finding("frequency", _Hit(item="nothing", dates=[])),
        ]
        rows = view_html._timeline_rows(findings)
        self.assertEqual(
            rows,
            [
                ("poor sleep", "poor sleep", ["2026-01-01", "2026-02-01"]),
                ("anxiety + poor sleep", "anxiety", ["2026-03-01", "2026-03-15"]),
                ("depression", "depression", ["2026-01-01", "2026-06-01"]),
            ],
        )

    def test_render_timeline_is_neutral_and_aria_hidden(self):
        rows = [
            ("poor sleep", "poor sleep", ["2026-01-01", "2026-02-01", "2026-03-02"]),
        ]
        html = view_html._render_timeline(rows)
        # Decorative echo: the whole section is hidden from assistive tech (the cited
        # dates live in the cards, the text alternative).
        self.assertIn('<section class="timeline" aria-hidden="true">', html)
        self.assertEqual(html.count('class="lane"'), 1)
        self.assertEqual(html.count('class="tick"'), 3)  # one tick per distinct date
        self.assertIn("inset-inline-start", html)  # positioned by logical property
        self.assertNotIn(" left:", html)
        self.assertNotIn("top:", html)
        self.assertIn('data-item="poor sleep"', html)  # links to the same note marks
        # Ticks only — no connecting/trend line, no gradient, no per-lens colour.
        for forbidden in ("<line", "<path", "linearGradient", "lens-"):
            self.assertNotIn(forbidden, html)

    def test_render_timeline_empty_or_single_date_draws_nothing(self):
        self.assertEqual(view_html._render_timeline([]), "")
        # One date -> no axis -> nothing (never a degenerate single-point "axis").
        self.assertEqual(
            view_html._render_timeline([("x", "x", ["2026-01-01"])]), ""
        )


class TestTimelineSurface(unittest.TestCase):
    """The timeline as rendered into every view."""

    def test_every_view_renders_a_neutral_timeline(self):
        for name, html in _all_demos().items():
            with self.subTest(view=name):
                self.assertIn('<section class="timeline" aria-hidden="true">', html)
                self.assertIn('class="tick"', html)
                self.assertIn("inset-inline-start", html)
                # Librarian rule in the timeline: no trend line, no gradient, no
                # per-lens / severity colour class on a tick.
                for forbidden in ("<line", "<path", "linearGradient", "lens-"):
                    self.assertNotIn(forbidden, html, f"{name}: {forbidden}")

    def test_tick_dates_are_also_present_as_text(self):
        # The a11y text alternative survives: the digest's cited chips still carry the
        # dates the (aria-hidden) ticks echo.
        html = digest_html.build_demo_html(REF)
        self.assertIn("cited: 2025-10-24 → 2026-03-15", html)  # gap brackets, as text
        self.assertIn('title="2025-10-24"', html)              # same date, as a tick


if __name__ == "__main__":
    unittest.main()
