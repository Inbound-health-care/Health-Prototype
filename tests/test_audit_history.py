"""Contracts for reviewed evidence-audit history and retrospectives."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.audit_evidence import AuditCheck, ChangedPath, build_artifact
from scripts.audit_history import (
    import_artifacts,
    load_history,
    retrospective,
    validate_artifact,
)


def artifact(index: int, status: str = "pass") -> dict[str, object]:
    return build_artifact(
        index,
        f"{index:040x}",
        f"{index + 100:040x}",
        [AuditCheck("EVIDENCE_TEMPLATE_SECTIONS", "warning", status)],
        [ChangedPath("M", "STATUS.md")],
        generated_at=f"2026-06-{index:02d}T00:00:00Z",
    )


class TestAuditHistory(unittest.TestCase):
    def test_schema_validation_rejects_extra_or_invalid_fields(self) -> None:
        value = artifact(1)
        self.assertIs(validate_artifact(value), value)

        extra = dict(value)
        extra["pr_body"] = "not allowed"
        with self.assertRaises(ValueError):
            validate_artifact(extra)

        invalid = dict(value)
        invalid["head_sha"] = "short"
        with self.assertRaises(ValueError):
            validate_artifact(invalid)

    def test_import_is_append_only_and_deduplicates_head_sha(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            history = root / "history.ndjson"
            first = root / "first.json"
            duplicate = root / "duplicate.json"
            second = root / "second.json"
            first.write_text(json.dumps(artifact(1)), encoding="utf-8")
            duplicate.write_text(json.dumps(artifact(1)), encoding="utf-8")
            second.write_text(json.dumps(artifact(2)), encoding="utf-8")

            self.assertEqual(import_artifacts(history, [first]), 1)
            original = history.read_bytes()
            self.assertEqual(import_artifacts(history, [duplicate]), 0)
            self.assertEqual(history.read_bytes(), original)
            self.assertEqual(import_artifacts(history, [second]), 1)
            self.assertTrue(history.read_bytes().startswith(original))
            self.assertEqual(len(load_history(history)), 2)

    def test_retrospective_refuses_fewer_than_five_unique_entries(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 5 unique"):
            retrospective([artifact(index) for index in range(1, 5)])

    def test_retrospective_only_proposes_check_review(self) -> None:
        entries = [artifact(index, "flag" if index in {1, 3} else "pass") for index in range(1, 6)]
        self.assertEqual(
            retrospective(entries),
            ["PROPOSAL review check_id=EVIDENCE_TEMPLATE_SECTIONS flagged_runs=2"],
        )

    def test_retrospective_deduplicates_entries(self) -> None:
        entries = [artifact(index) for index in range(1, 6)]
        entries.append(artifact(1, "flag"))
        self.assertEqual(
            retrospective(entries),
            ["PROPOSAL review check_id=EVIDENCE_TEMPLATE_SECTIONS flagged_runs=1"],
        )


if __name__ == "__main__":
    unittest.main()
