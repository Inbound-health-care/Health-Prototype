"""test_view_theme.py — the shared calm view theme (ADR 0017).

report_html.py and digest_html.py share one warm, low-stimulation theme: light-first
with an optional dark toggle, and a SINGLE non-semantic accent (the same for every
lens — colour never encodes severity, type, or judgment, so the librarian rule holds
in the view). These tests prove (1) WCAG-AA contrast for the theme tokens in both
light and dark, (2) no colour outside the declared token set (no rogue / per-lens /
severity colour), (3) the accent is one uniform token, and (4) the dark toggle is
wired light-first. Pure stdlib.

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

import digest_html  # noqa: E402
import report_html  # noqa: E402
from report_html import THEME  # noqa: E402

REF = datetime.date(2026, 3, 15)


def _luminance(hex_color: str) -> float:
    """WCAG relative luminance of a #rrggbb colour."""
    h = hex_color.lstrip("#")
    chans = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        chans.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = chans
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two #rrggbb colours (1.0 .. 21.0)."""
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# Text / affordance pairs must meet AA (4.5:1). Note text also sits on the resting
# and active mark backgrounds, so those are checked too.
_TEXT_PAIRS = [
    ("text", "bg"), ("text", "surface"), ("text", "mark-rest"), ("text", "accent-weak"),
    ("muted", "bg"), ("muted", "surface"), ("accent", "bg"), ("accent", "surface"),
]
# UI indicators (the active-mark outline, hover/selected borders) must meet 3:1
# (WCAG 1.4.11 non-text contrast).
_UI_PAIRS = [("accent-line", "bg"), ("accent-line", "surface")]


class TestContrastIsAccessible(unittest.TestCase):
    def test_text_pairs_meet_aa(self):
        for mode in ("light", "dark"):
            t = THEME[mode]
            for fg, bg in _TEXT_PAIRS:
                r = _contrast(t[fg], t[bg])
                self.assertGreaterEqual(r, 4.5, f"{mode} {fg}/{bg} = {r:.2f} (< 4.5:1)")

    def test_ui_indicator_pairs_meet_3to1(self):
        for mode in ("light", "dark"):
            t = THEME[mode]
            for fg, bg in _UI_PAIRS:
                r = _contrast(t[fg], t[bg])
                self.assertGreaterEqual(r, 3.0, f"{mode} {fg}/{bg} = {r:.2f} (< 3:1)")


def _style(html: str) -> str:
    return html[html.index("<style>"):html.index("</style>")]


class TestColourIsNonSemantic(unittest.TestCase):
    def test_no_colour_outside_the_token_set(self):
        # Every literal colour in the stylesheet must be a declared theme token —
        # no rogue or per-lens / severity colour can sneak into the view.
        allowed = {v.lower() for mode in THEME.values() for v in mode.values()}
        for html in (
            report_html.build_demo_html(REF), digest_html.build_demo_html(REF),
            report_html.build_demo_multi_html(REF), digest_html.build_demo_multi_html(REF),
        ):
            found = {h.lower() for h in re.findall(r"#[0-9A-Fa-f]{6}", _style(html))}
            self.assertTrue(found, "no colours found in <style>")
            self.assertLessEqual(found, allowed, f"non-token colour(s): {found - allowed}")

    def test_accent_is_one_uniform_token(self):
        # The lens label uses the single --accent for every lens; there is no
        # per-lens colour class, so colour never encodes which lens or how severe.
        html = digest_html.build_demo_html(REF)
        self.assertIn(".lens { color: var(--accent)", html)
        for lens in ("recurrence", "gap", "frequency", "cooccurrence", "cadence"):
            self.assertNotIn(f"lens-{lens}", html)


class TestDarkToggleIsWired(unittest.TestCase):
    def test_light_first_with_optional_dark(self):
        for html in (
            report_html.build_demo_html(REF), digest_html.build_demo_html(REF),
            report_html.build_demo_multi_html(REF), digest_html.build_demo_multi_html(REF),
        ):
            self.assertIn('<html lang="en" data-theme="light">', html)  # light-first
            self.assertIn('class="theme-toggle"', html)
            self.assertIn("prefers-color-scheme", html)
            self.assertIn(':root[data-theme="dark"]', html)


class TestResponsiveAndroid(unittest.TestCase):
    def test_views_stack_on_narrow_android_widths(self):
        # Android-targeted responsive layer (ADR 0018): a viewport meta + a media query
        # that stacks the two columns below 640px (every Android phone portrait; primary
        # width 360px). Desktop / foldable-unfolded keep the two-column layout.
        for html in (
            report_html.build_demo_html(REF), digest_html.build_demo_html(REF),
            report_html.build_demo_multi_html(REF), digest_html.build_demo_multi_html(REF),
        ):
            self.assertIn('name="viewport"', html)
            self.assertIn("@media (max-width: 640px)", html)
            self.assertIn("flex-direction: column", html)


if __name__ == "__main__":
    unittest.main()
