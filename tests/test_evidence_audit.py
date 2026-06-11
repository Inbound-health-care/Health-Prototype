"""Contracts for the advisory pull-request evidence audit."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts.audit_evidence import (
    AuditCheck,
    ChangedPath,
    build_artifact,
    build_checks,
    classify_path,
)


EXPECTED_IDS = {
    "EVIDENCE_TEMPLATE_SECTIONS",
    "EVIDENCE_DEVIATIONS",
    "EVIDENCE_AI_DISCLOSURE",
    "EVIDENCE_RISK_CLASS",
    "EVIDENCE_VERIFICATION",
    "EVIDENCE_PROVENANCE",
    "EVIDENCE_COMPLIANCE_WORDING",
    "EVIDENCE_ADR_CONFIRMATION",
    "EVIDENCE_CANONICAL_DOCS",
    "EVIDENCE_PROJECT_MAP",
    "EVIDENCE_UNLOGGED_FILES",
}


def complete_body() -> str:
    return """## Intent

Add the evidence audit with documented scope.

## Deviations

None.

## AI assistance

- [ ] No AI-assisted code
- [x] AI-assisted code present

Tool/model and human review performed: Codex implementation with human review pending.

## Health/provenance risk

- [x] Docs only
- [x] Tests or harnesses
- [ ] Recurrence or rule logic
- [ ] Data/provenance/citation behavior
- [x] Compliance or safety wording
- [x] Dependency or CI

Risk notes: tooling and governance only.

## Verification

- [x] make check passes, if code or tests changed
- [x] make proptest passes, if rule behavior changed
- [x] Source/provenance boundaries preserved
- [x] Reviewer checked silent-failure risk
- [x] Sensitive-change scan passes
- [x] Relevant generated artifacts were inspected

Commands and results: `python -m unittest` passed.

## Records

- ADR added or updated: None
- `STATUS.md` reconciled: yes
- `PROJECT_MAP.md` reconciled: yes
- `docs/LEARNINGS.md` entry needed or added: no
"""


def check_map(checks: list[AuditCheck]) -> dict[str, str]:
    return {check.check_id: check.status for check in checks}


class TestEvidenceAudit(unittest.TestCase):
    def test_check_ids_are_stable_and_complete(self) -> None:
        checks = build_checks(
            complete_body(),
            [ChangedPath("M", "STATUS.md")],
            Path.cwd(),
        )
        self.assertEqual({check.check_id for check in checks}, EXPECTED_IDS)
        self.assertTrue(all(check.status == "pass" for check in checks))

    def test_template_placeholder_and_disclosure_checks(self) -> None:
        cases = {
            "EVIDENCE_TEMPLATE_SECTIONS": complete_body().replace("## Intent", "## Scope"),
            "EVIDENCE_DEVIATIONS": complete_body().replace("None.", "List any deviation"),
            "EVIDENCE_AI_DISCLOSURE": complete_body().replace(
                "- [ ] No AI-assisted code", "- [x] No AI-assisted code"
            ),
            "EVIDENCE_RISK_CLASS": complete_body()
            .replace("- [x] Docs only", "- [ ] Docs only")
            .replace("- [x] Tests or harnesses", "- [ ] Tests or harnesses")
            .replace("- [x] Compliance or safety wording", "- [ ] Compliance or safety wording")
            .replace("- [x] Dependency or CI", "- [ ] Dependency or CI"),
            "EVIDENCE_VERIFICATION": complete_body().replace(
                "Commands and results: `python -m unittest` passed.",
                "Commands and results:",
            ),
        }
        for check_id, body in cases.items():
            with self.subTest(check_id=check_id):
                statuses = check_map(build_checks(body, [], Path.cwd()))
                self.assertEqual(statuses[check_id], "flag")

    def test_path_sensitive_checks(self) -> None:
        provenance_body = complete_body().replace(
            "- [x] Source/provenance boundaries preserved",
            "- [ ] Source/provenance boundaries preserved",
        )
        self.assertEqual(
            check_map(
                build_checks(
                    provenance_body,
                    [ChangedPath("M", "recurrence.py")],
                    Path.cwd(),
                )
            )["EVIDENCE_PROVENANCE"],
            "flag",
        )

        compliance_body = complete_body().replace(
            "- [x] Compliance or safety wording",
            "- [ ] Compliance or safety wording",
        )
        self.assertEqual(
            check_map(
                build_checks(
                    compliance_body,
                    [ChangedPath("M", "SECURITY.md")],
                    Path.cwd(),
                )
            )["EVIDENCE_COMPLIANCE_WORDING"],
            "flag",
        )

    def test_adr_confirmation_is_inspected_without_modifying_source(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            adr = root / "docs" / "adr" / "0030-test.md"
            adr.parent.mkdir(parents=True)
            adr.write_text("# Test\n\n**Status:** RESEARCH_ONLY\n", encoding="utf-8")
            before = adr.read_bytes()
            checks = build_checks(
                complete_body().replace("ADR added or updated: None", "ADR added or updated: 0030"),
                [ChangedPath("A", "docs/adr/0030-test.md")],
                root,
            )
            self.assertEqual(check_map(checks)["EVIDENCE_ADR_CONFIRMATION"], "flag")
            self.assertEqual(adr.read_bytes(), before)

    def test_canonical_project_map_and_unlogged_file_checks(self) -> None:
        pending_status = complete_body().replace(
            "`STATUS.md` reconciled: yes", "`STATUS.md` reconciled: pending"
        )
        checks = build_checks(
            pending_status,
            [ChangedPath("A", "scripts/new_tool.py")],
            Path.cwd(),
        )
        statuses = check_map(checks)
        self.assertEqual(statuses["EVIDENCE_CANONICAL_DOCS"], "flag")
        self.assertEqual(statuses["EVIDENCE_PROJECT_MAP"], "flag")

        unknown = build_checks(
            complete_body(),
            [ChangedPath("A", "misc/value.bin")],
            Path.cwd(),
        )
        self.assertEqual(check_map(unknown)["EVIDENCE_UNLOGGED_FILES"], "flag")

    def test_path_classification(self) -> None:
        cases = {
            "recurrence.py": "clinical-engine",
            "extract.py": "extractor",
            "digest_html.py": "view",
            "data/sample_records.py": "data",
            "tests/test_report.py": "tests",
            ".github/workflows/ci.yml": "workflow",
            "requirements-dev.txt": "dependency",
            "tools/scan.py": "governance",
            "docs/adr/0029-test.md": "documentation",
            "artifact.bin": "other",
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(classify_path(path), expected)

    def test_artifact_is_metadata_only(self) -> None:
        artifact = build_artifact(
            45,
            "a" * 40,
            "b" * 40,
            [AuditCheck("EVIDENCE_TEMPLATE_SECTIONS", "warning", "pass")],
            [ChangedPath("M", "recurrence.py")],
            generated_at="2026-06-11T00:00:00Z",
        )
        encoded = json.dumps(artifact)
        self.assertEqual(artifact["schema"], "health-prototype.evidence-audit.v1")
        self.assertEqual(artifact["changed_path_category_counts"], {"clinical-engine": 1})
        self.assertNotIn("recurrence.py", encoded)
        self.assertNotIn("Add the evidence audit", encoded)

    def test_documented_cli_writes_only_the_requested_artifact(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "audit_evidence.py"
        with TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "synthetic" + "@" + "example.invalid"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Synthetic Test"],
                cwd=root,
                check=True,
            )
            status = root / "STATUS.md"
            status.write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "STATUS.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
            status.write_text("after\n", encoding="utf-8")
            subprocess.run(["git", "add", "STATUS.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "head"], cwd=root, check=True)

            event = root / "event.json"
            event.write_text(
                json.dumps({"pull_request": {"number": 45, "body": complete_body()}}),
                encoding="utf-8",
            )
            artifact_path = root / "artifact.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--base",
                    "HEAD~1",
                    "--head",
                    "HEAD",
                    "--event-file",
                    str(event),
                    "--artifact",
                    str(artifact_path),
                ],
                cwd=root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(status.read_text(encoding="utf-8"), "after\n")
            self.assertTrue(artifact_path.is_file())


if __name__ == "__main__":
    unittest.main()
