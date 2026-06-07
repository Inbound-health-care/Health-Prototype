"""test_view_js.py — dev-only LIVE JS/DOM test for the HTML views (ADR 0025).

Closes the audit's Tier 2 #3 gap (docs/AUDIT_2026-06-07.md): the views ship
interactive JS — click-to-highlight, keyboard Enter/Space activation, the
``beforeprint`` handler that opens every ``<details>`` for printing, and the
per-patient scope isolation that prevents cross-patient highlight bleed — but the
rest of the suite only asserts that JS as STATIC STRINGS (e.g. ``assertIn("'Enter'",
html)``). A runtime JS bug (a broken keyboard path, real cross-patient bleed) would
pass green. This module actually EXECUTES the JS in headless Chromium via Playwright
and checks the resulting DOM state.

Playwright is a dev-only tool (no runtime dependency) and is deliberately NOT in CI —
the browser binaries are heavy (Scott's call, ADR 0025). This module SKIPS cleanly
when Playwright or its browser is absent, so ``make test`` / CI stay pure-stdlib
green. Run it locally with:

    make jstest
    # first run only, to fetch the browser binary:
    uvx --with playwright playwright install chromium
"""

from __future__ import annotations

import datetime
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import digest_html  # noqa: E402
import report_html  # noqa: E402

try:
    from playwright.sync_api import sync_playwright

    HAS_PLAYWRIGHT = True
except ImportError:  # pragma: no cover - dev-only tool absent
    HAS_PLAYWRIGHT = False

REF = datetime.date(2026, 3, 15)
_ACTIVE = "mark.cite.active, .tick.active"  # a finding's cited marks, once lit


@unittest.skipUnless(HAS_PLAYWRIGHT, "playwright not installed (run: make jstest)")
class LiveViewJSTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls._pw = sync_playwright().start()
            cls._browser = cls._pw.chromium.launch()
        except Exception as exc:  # browser binary missing / launch failed
            raise unittest.SkipTest(
                f"chromium unavailable ({exc}); run: "
                "uvx --with playwright playwright install chromium"
            )

    @classmethod
    def tearDownClass(cls):
        cls._browser.close()
        cls._pw.stop()

    def _page(self, html: str):
        """Write HTML to a temp file and open it (file://) in a fresh page."""
        fh = tempfile.NamedTemporaryFile(
            "w", suffix=".html", delete=False, encoding="utf-8"
        )
        fh.write(html)
        fh.close()
        self.addCleanup(os.unlink, fh.name)
        page = self._browser.new_page()
        self.addCleanup(page.close)
        page.goto("file://" + fh.name)
        return page

    # -- click-to-highlight (both single views) ----------------------------
    def test_click_highlights_then_toggles_off(self):
        for build in (report_html.build_demo_html, digest_html.build_demo_html):
            with self.subTest(view=build.__module__):
                page = self._page(build(REF))
                finding = page.locator(".finding").first
                # click near the top-left so we land on the finding, not a nested
                # cited-date <details> (whose click is intentionally ignored).
                finding.click(position={"x": 5, "y": 5})
                self.assertEqual(finding.get_attribute("aria-pressed"), "true")
                self.assertIn("sel", finding.get_attribute("class"))
                self.assertGreater(
                    page.locator(_ACTIVE).count(), 0, "click lit no cited marks"
                )
                # clicking the same finding again clears the highlight (toggle).
                finding.click(position={"x": 5, "y": 5})
                self.assertEqual(finding.get_attribute("aria-pressed"), "false")
                self.assertEqual(page.locator(_ACTIVE).count(), 0)

    # -- keyboard activation (Enter + Space) -------------------------------
    def test_keyboard_enter_and_space_activate(self):
        page = self._page(report_html.build_demo_html(REF))
        finding = page.locator(".finding").first
        finding.focus()
        page.keyboard.press("Enter")
        self.assertEqual(finding.get_attribute("aria-pressed"), "true")
        self.assertGreater(page.locator(_ACTIVE).count(), 0)
        page.keyboard.press("Space")  # Space toggles the same finding off
        self.assertEqual(finding.get_attribute("aria-pressed"), "false")
        self.assertEqual(page.locator(_ACTIVE).count(), 0)

    # -- beforeprint opens every <details>, afterprint restores ------------
    def test_beforeprint_opens_details_afterprint_restores(self):
        page = self._page(digest_html.build_demo_html(REF))
        details = page.locator("details")
        total = details.count()
        if total == 0:
            self.skipTest("no <details> in this demo")
        self.assertEqual(
            page.locator("details[open]").count(), 0, "demo details start collapsed"
        )
        page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
        self.assertEqual(
            page.locator("details[open]").count(), total, "beforeprint must open all"
        )
        page.evaluate("window.dispatchEvent(new Event('afterprint'))")
        self.assertEqual(
            page.locator("details[open]").count(), 0, "afterprint must restore"
        )

    # -- the no-bleed guarantee, enforced at RUNTIME (both multi views) ----
    def test_multi_patient_highlight_never_bleeds(self):
        for build in (
            report_html.build_demo_multi_html,
            digest_html.build_demo_multi_html,
        ):
            with self.subTest(view=build.__module__):
                page = self._page(build(REF))
                blocks = page.locator(".patient")
                count = blocks.count()
                self.assertGreaterEqual(count, 2, "multi demo needs >=2 patients")
                first = blocks.nth(0)
                first.locator(".finding").first.click(position={"x": 5, "y": 5})
                self.assertGreater(
                    first.locator(_ACTIVE).count(), 0, "click lit nothing in its block"
                )
                for i in range(1, count):
                    self.assertEqual(
                        blocks.nth(i).locator(_ACTIVE).count(),
                        0,
                        "highlight bled into another patient block",
                    )


if __name__ == "__main__":
    unittest.main()
