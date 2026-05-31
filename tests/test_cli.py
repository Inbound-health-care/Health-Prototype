"""CLI behavior tests for local prototype commands."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
        self.assertRegex(result.stdout.strip(), r"^Health-Prototype recurrence engine \d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
