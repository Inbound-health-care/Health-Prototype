"""
test_cli.py — the command-line interface.

Covers the ``--version`` flag (exact output string + clean exit) and the
no-argument path (prints help, exits 0). These are in-process tests: they
patch ``sys.argv`` and capture stdout rather than spawning a subprocess, so
they match the rest of the suite (everything imports and calls directly).

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recurrence import VERSION, main  # noqa: E402


def _run_cli(*argv):
    """Run ``main()`` in-process with the given args; return ``(rc, stdout)``."""
    out = io.StringIO()
    saved = sys.argv
    sys.argv = ["recurrence.py", *argv]
    try:
        with contextlib.redirect_stdout(out):
            rc = main()
    finally:
        sys.argv = saved
    return rc, out.getvalue()


class TestVersionFlag(unittest.TestCase):
    # The public contract string. Bumping VERSION should update this line
    # deliberately — it is a tripwire, not an accident.
    EXPECTED = "Health-Prototype recurrence engine 0.5.0"

    def test_prints_exact_contract_line(self):
        rc, out = _run_cli("--version")
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), self.EXPECTED)

    def test_is_wired_to_VERSION_constant(self):
        _, out = _run_cli("--version")
        self.assertEqual(out.strip(), f"Health-Prototype recurrence engine {VERSION}")


class TestNoArguments(unittest.TestCase):
    def test_prints_help_and_returns_zero(self):
        rc, out = _run_cli()
        self.assertEqual(rc, 0)
        self.assertIn("usage:", out.lower())


if __name__ == "__main__":
    unittest.main()
