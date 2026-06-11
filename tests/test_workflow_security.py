"""Static contracts for GitHub workflow security and dev dependency pins."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
USES = re.compile(r"^\s*-?\s*uses:\s*([^\s@]+)@([0-9a-f]{40})\s+#\s+v\d", re.MULTILINE)


class TestWorkflowSecurity(unittest.TestCase):
    def workflow_texts(self) -> dict[str, str]:
        return {path.name: path.read_text(encoding="utf-8") for path in WORKFLOWS.glob("*.yml")}

    def test_all_action_references_are_immutable_and_reviewable(self) -> None:
        for name, text in self.workflow_texts().items():
            uses_lines = [line for line in text.splitlines() if "uses:" in line]
            matches = USES.findall(text)
            with self.subTest(workflow=name):
                self.assertEqual(len(matches), len(uses_lines))

    def test_workflows_are_read_only_and_never_pull_request_target(self) -> None:
        for name, text in self.workflow_texts().items():
            with self.subTest(workflow=name):
                self.assertIn("permissions:\n  contents: read", text)
                self.assertNotIn("pull_request_target", text)

    def test_checkout_does_not_persist_credentials(self) -> None:
        for name, text in self.workflow_texts().items():
            checkout_count = text.count("uses: actions/checkout@")
            with self.subTest(workflow=name):
                self.assertEqual(
                    text.count("persist-credentials: false"), checkout_count
                )

    def test_ci_uses_the_exact_dev_manifest(self) -> None:
        ci = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("pip install hypothesis", ci)
        self.assertNotIn("pip install ruff", ci)
        self.assertIn("pip install --requirement requirements-dev.txt", ci)

    def test_dev_requirements_are_exact(self) -> None:
        requirements = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        lines = [line for line in requirements.splitlines() if line and not line.startswith("#")]
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertRegex(line, r"^[a-z0-9-]+==\d+(?:\.\d+)+$")

    def test_new_gates_are_pull_request_scoped(self) -> None:
        texts = self.workflow_texts()
        self.assertIn("pull_request:", texts["sensitive-scan.yml"])
        self.assertIn("pull_request:", texts["dependency-review.yml"])
        self.assertIn("python tools/scan_sensitive_changes.py --ci", texts["sensitive-scan.yml"])


if __name__ == "__main__":
    unittest.main()
