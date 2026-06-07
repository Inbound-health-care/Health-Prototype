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

# The suite-wide union of interpretive / ranking words the librarian rule forbids.
# Mirrors tests/test_report_html.py and tests/test_digest_html.py; the shared layer
# must add none either.
BANNED = (
    "worsening", "worsen", "severe", "severity", "suggests", "diagnos", "risk",
    "concern", "caution", "abnormal", "score", "relapse", "acute", "accelerat",
    "decelerat", "increasing", "decreasing", "escalat", "declining", "deteriorat",
    "improving", "trend", "associated", "correlated", "linked", "cause", "caused",
    "relationship", "top", "most", "priority", "prioritize", "rank", "ranking",
    "total", "highest", "lowest", "worst", "best",
)


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
                self.assertIn('tabindex="0"', html)
                self.assertIn('role="button"', html)
                self.assertIn('aria-pressed="false"', html)
                # Keyboard is wired (Enter/Space), not mouse-only.
                self.assertIn("keydown", html)
                self.assertIn("'Enter'", html)
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
                n_findings = html.count('class="finding"') + html.count('class="card finding"')
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


if __name__ == "__main__":
    unittest.main()
