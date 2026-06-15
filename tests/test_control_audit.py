"""Tests for the repository-control audit gate."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tools import control_audit


GOOD_SHA = "a" * 40
RULES = {
    "workflow_rules": {
        "require_top_level_permissions": True,
        "require_top_level_concurrency": True,
        "require_job_timeouts": True,
        "require_full_sha_actions": True,
        "require_checkout_persist_credentials_false": True,
        "prohibit_pull_request_target": True,
        "prohibit_fork_checkout": True,
        "prohibit_fork_scan_skip": True,
    }
}


class TestControlAudit(unittest.TestCase):
    def audit_text(self, text: str) -> list[str]:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / ".github" / "workflows" / "sample.yml"
            path.parent.mkdir(parents=True)
            path.write_text(text, encoding="utf-8")

            old_root = control_audit.ROOT
            try:
                control_audit.ROOT = root
                failures: list[str] = []
                control_audit.audit_workflow(path, RULES, failures)
                return failures
            finally:
                control_audit.ROOT = old_root

    def test_action_ref_pin_rule(self) -> None:
        self.assertTrue(control_audit.action_ref_is_pinned("actions/checkout@" + GOOD_SHA))
        self.assertTrue(control_audit.action_ref_is_pinned("./.github/actions/local-check"))
        self.assertFalse(control_audit.action_ref_is_pinned("actions/checkout@v6"))
        self.assertFalse(control_audit.action_ref_is_pinned("actions/setup-python@main"))

    def test_checkout_credentials_requires_active_false_not_comment(self) -> None:
        commented_only = [
            "      - uses: actions/checkout@" + GOOD_SHA,
            "        with:",
            "          # persist-credentials: false",
            "      - name: next step",
        ]
        self.assertTrue(control_audit.checkout_persists_credentials(commented_only, 0))

        long_valid_step = ["      - uses: actions/checkout@" + GOOD_SHA, "        with:"]
        long_valid_step.extend(["          fetch-depth: 0"] * 15)
        long_valid_step.append("          persist-credentials: false")
        long_valid_step.append("      - name: next step")
        self.assertFalse(control_audit.checkout_persists_credentials(long_valid_step, 0))

    def test_job_blocks_stop_at_next_top_level_key(self) -> None:
        text = "\n".join(
            [
                "name: Sample",
                "jobs:",
                "  audit:",
                "    runs-on: ubuntu-latest",
                "permissions:",
                "  contents: read",
                "  timeout-minutes: 99",
            ]
        )
        blocks = control_audit.job_blocks(text)
        self.assertEqual(set(blocks), {"audit"})
        self.assertNotIn("permissions", blocks["audit"])
        self.assertNotIn("timeout-minutes: 99", blocks["audit"])

    def test_audit_reports_missing_controls(self) -> None:
        failures = self.audit_text(
            "\n".join(
                [
                    "name: Sample",
                    "on:",
                    "  pull_request:",
                    "jobs:",
                    "  test:",
                    "    runs-on: ubuntu-latest",
                    "    steps:",
                    "      - uses: actions/checkout@v6",
                    "      - uses: actions/setup-python@" + GOOD_SHA,
                ]
            )
        )
        joined = "\n".join(failures)
        self.assertIn("workflow-permissions", joined)
        self.assertIn("workflow-concurrency", joined)
        self.assertIn("job-timeout", joined)
        self.assertIn("action-pin", joined)
        self.assertIn("checkout-credentials", joined)

    def test_comments_do_not_trigger_policy_failures(self) -> None:
        failures = self.audit_text(
            "\n".join(
                [
                    "name: Sample",
                    "# pull_request_target:",
                    "# ref: ${{ github.head_ref }}",
                    "# if: github.event.pull_request.head.repo.full_name == github.repository",
                    "# uses: actions/cache@v4",
                    "on:",
                    "  pull_request:",
                    "permissions:",
                    "  contents: read",
                    "concurrency:",
                    "  group: sample-${{ github.workflow }}-${{ github.ref }}",
                    "  cancel-in-progress: true",
                    "jobs:",
                    "  test:",
                    "    runs-on: ubuntu-latest",
                    "    timeout-minutes: 10",
                    "    steps:",
                    "      - uses: actions/checkout@" + GOOD_SHA,
                    "        with:",
                    "          persist-credentials: false",
                    "      - uses: actions/setup-python@" + GOOD_SHA,
                ]
            )
        )
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
