"""CLI behavior tests for local prototype commands."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from recurrence import VERSION  # noqa: E402


class TestCli(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "recurrence.py", *args],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_version_prints_version_and_exits_cleanly(self):
        result = self.run_cli("--version")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout.strip(), f"Health-Prototype recurrence engine {VERSION}"
        )


if __name__ == "__main__":
    unittest.main()
