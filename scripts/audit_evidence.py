#!/usr/bin/env python3
"""Advisory pull-request evidence audit with metadata-only output."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable


SCHEMA = "health-prototype.evidence-audit.v1"
REQUIRED_SECTIONS = (
    "Intent",
    "Deviations",
    "AI assistance",
    "Health/provenance risk",
    "Verification",
    "Records",
)
RISK_LABELS = (
    "Docs only",
    "Tests or harnesses",
    "Recurrence or rule logic",
    "Data/provenance/citation behavior",
    "Compliance or safety wording",
    "Dependency or CI",
)
CLINICAL_FILES = {"recurrence.py"}
EXTRACTOR_FILES = {"extract.py"}
VIEW_FILES = {"view_html.py", "report_html.py", "digest_html.py"}
CONTROL_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "LOAD.md",
    "STATUS.md",
    "PROJECT_MAP.md",
    "SECURITY.md",
    "SECURITY_AND_TOOL_POLICY.md",
    "LOAD_TRACE_TEMPLATE.md",
}
COMPLIANCE_FILES = {
    "README.md",
    "SECURITY.md",
    "SECURITY_AND_TOOL_POLICY.md",
    "docs/COUNSEL_VERIFICATION_CHECKLIST.md",
    "docs/adr/0009-legal-grounding.md",
    "docs/adr/0011-fda-cds-guidance-refresh-2026.md",
}
PLACEHOLDERS = (
    "what changed?",
    "why is this the smallest useful change?",
    "tool/model and human review performed:",
    "commands and results:",
    "list any deviation",
)


@dataclass(frozen=True)
class ChangedPath:
    status: str
    path: str


@dataclass(frozen=True)
class AuditCheck:
    check_id: str
    severity: str
    status: str


def classify_path(path: str) -> str:
    if path in CLINICAL_FILES:
        return "clinical-engine"
    if path in EXTRACTOR_FILES:
        return "extractor"
    if path in VIEW_FILES:
        return "view"
    if path.startswith("data/"):
        return "data"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith(".github/workflows/"):
        return "workflow"
    if (
        path == ".github/dependabot.yml"
        or path.startswith("requirements")
        or path.endswith((".lock", "Pipfile"))
    ):
        return "dependency"
    if (
        path in CONTROL_FILES
        or path == ".github/pull_request_template.md"
        or path.startswith((".githooks/", "tools/", "scripts/"))
    ):
        return "governance"
    if path.startswith("docs/") or path.endswith(".md"):
        return "documentation"
    return "other"


def _section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)"
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else ""


def _checked(body: str, label: str) -> bool:
    return bool(
        re.search(
            rf"(?im)^\s*-\s*\[[xX]\]\s*{re.escape(label)}\s*$",
            body,
        )
    )


def _has_substance(text: str) -> bool:
    lowered = text.strip().lower()
    if not lowered:
        return False
    remaining = lowered
    for placeholder in PLACEHOLDERS:
        remaining = remaining.replace(placeholder, "")
    remaining = re.sub(r"[-*`:#\[\]()\s]", "", remaining)
    return bool(remaining)


def _record_value(body: str, label: str) -> str:
    records = _section(body, "Records")
    match = re.search(rf"(?im)^\s*-\s*{re.escape(label)}\s*(.*)$", records)
    return match.group(1).strip() if match else ""


def _check(check_id: str, condition: bool, severity: str = "warning") -> AuditCheck:
    return AuditCheck(check_id, severity, "pass" if condition else "flag")


def build_checks(
    body: str,
    changed_paths: Iterable[ChangedPath],
    root: Path,
) -> list[AuditCheck]:
    changes = list(changed_paths)
    paths = {change.path for change in changes}
    categories = {classify_path(path) for path in paths}

    sections_present = all(_section(body, heading) for heading in REQUIRED_SECTIONS)
    deviations = _section(body, "Deviations")
    no_ai = _checked(body, "No AI-assisted code")
    ai_present = _checked(body, "AI-assisted code present")
    ai_section = _section(body, "AI assistance")
    ai_detail = re.sub(
        r"(?im)^\s*-\s*\[[ xX]\].*$",
        "",
        ai_section,
    )
    risk_selected = any(_checked(body, label) for label in RISK_LABELS)
    verification = _section(body, "Verification")
    provenance_paths = bool(
        categories & {"clinical-engine", "extractor", "view", "data"}
    )
    compliance_paths = any(path in COMPLIANCE_FILES for path in paths)
    adr_paths = [
        path
        for path in paths
        if path.startswith("docs/adr/") and path.endswith(".md") and path != "docs/adr/README.md"
    ]
    adr_files_valid = True
    for path in adr_paths:
        target = root / path
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8")
        if "## Confirmation" not in text or "**Status:**" not in text:
            adr_files_valid = False

    impactful = bool(
        categories
        & {
            "clinical-engine",
            "extractor",
            "view",
            "data",
            "workflow",
            "dependency",
            "governance",
        }
    )
    status_record = _record_value(body, "`STATUS.md` reconciled:")
    project_record = _record_value(body, "`PROJECT_MAP.md` reconciled:")
    added_paths = {change.path for change in changes if change.status.startswith("A")}
    new_mapped_files = {
        path
        for path in added_paths
        if not path.startswith("tests/") and path != "docs/evidence-audit-history.ndjson"
    }
    unknown_paths = [path for path in paths if classify_path(path) == "other"]

    return [
        _check("EVIDENCE_TEMPLATE_SECTIONS", sections_present),
        _check("EVIDENCE_DEVIATIONS", _has_substance(deviations)),
        _check(
            "EVIDENCE_AI_DISCLOSURE",
            no_ai != ai_present and (no_ai or _has_substance(ai_detail)),
        ),
        _check("EVIDENCE_RISK_CLASS", risk_selected),
        _check(
            "EVIDENCE_VERIFICATION",
            _has_substance(verification)
            and ("`" in verification or "passed" in verification.lower()),
        ),
        _check(
            "EVIDENCE_PROVENANCE",
            not provenance_paths or _checked(body, "Source/provenance boundaries preserved"),
        ),
        _check(
            "EVIDENCE_COMPLIANCE_WORDING",
            not compliance_paths or _checked(body, "Compliance or safety wording"),
        ),
        _check(
            "EVIDENCE_ADR_CONFIRMATION",
            (not adr_paths or bool(_record_value(body, "ADR added or updated:")))
            and adr_files_valid,
        ),
        _check(
            "EVIDENCE_CANONICAL_DOCS",
            not impactful or status_record.lower() not in {"", "no", "n/a", "pending"},
        ),
        _check(
            "EVIDENCE_PROJECT_MAP",
            not new_mapped_files
            or (
                "PROJECT_MAP.md" in paths
                and project_record.lower() not in {"", "no", "n/a", "pending"}
            ),
        ),
        _check("EVIDENCE_UNLOGGED_FILES", not unknown_paths, severity="notice"),
    ]


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def resolve_commit(ref: str) -> str:
    resolved = _run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"]).strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", resolved):
        raise RuntimeError("git returned an invalid commit ID")
    return resolved.lower()


def changed_paths(base_sha: str, head_sha: str) -> list[ChangedPath]:
    output = _run_git(["diff", "--name-status", f"{base_sha}...{head_sha}", "--"])
    changes: list[ChangedPath] = []
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        status = fields[0]
        path = fields[-1].replace("\\", "/")
        changes.append(ChangedPath(status, path))
    return changes


def _event_refs(event: dict[str, object]) -> tuple[str, str]:
    pull_request = event.get("pull_request")
    if not isinstance(pull_request, dict):
        raise ValueError("event file does not contain pull_request metadata")
    base = pull_request.get("base")
    head = pull_request.get("head")
    if not isinstance(base, dict) or not isinstance(head, dict):
        raise ValueError("event file does not contain base/head metadata")
    base_sha = base.get("sha")
    head_sha = head.get("sha")
    if not isinstance(base_sha, str) or not isinstance(head_sha, str):
        raise ValueError("event file does not contain base/head commit IDs")
    return base_sha, head_sha


def _event_pr(event: dict[str, object]) -> tuple[int, str]:
    pull_request = event.get("pull_request")
    if not isinstance(pull_request, dict):
        raise ValueError("event file does not contain pull_request metadata")
    number = pull_request.get("number") or event.get("number")
    body = pull_request.get("body") or ""
    if not isinstance(number, int) or not isinstance(body, str):
        raise ValueError("event file contains invalid pull_request metadata")
    return number, body


def build_artifact(
    pr_number: int,
    base_sha: str,
    head_sha: str,
    checks: Iterable[AuditCheck],
    changes: Iterable[ChangedPath],
    generated_at: str | None = None,
) -> dict[str, object]:
    counts = Counter(classify_path(change.path) for change in changes)
    timestamp = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "schema": SCHEMA,
        "pr_number": pr_number,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "generated_at": timestamp,
        "checks": [
            {
                "id": check.check_id,
                "severity": check.severity,
                "status": check.status,
            }
            for check in checks
        ],
        "changed_path_category_counts": dict(sorted(counts.items())),
    }


def _summary(checks: Iterable[AuditCheck]) -> str:
    lines = ["## PR evidence audit", "", "| Check | Status | Severity |", "|---|---|---|"]
    for check in checks:
        lines.append(f"| `{check.check_id}` | {check.status} | {check.severity} |")
    lines.append("")
    lines.append("Advisory only. The artifact contains metadata, not PR or source text.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="base ref or literal 'event'")
    parser.add_argument("--head", required=True, help="head ref or literal 'event'")
    parser.add_argument("--event-file", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--strict", action="store_true", help="fail when any check flags")
    args = parser.parse_args(argv)

    try:
        event = json.loads(args.event_file.read_text(encoding="utf-8"))
        event_base = event_head = None
        if args.base == "event" or args.head == "event":
            event_base, event_head = _event_refs(event)
        base_sha = resolve_commit(event_base if args.base == "event" else args.base)
        head_sha = resolve_commit(event_head if args.head == "event" else args.head)
        pr_number, body = _event_pr(event)
        changes = changed_paths(base_sha, head_sha)
        checks = build_checks(body, changes, Path.cwd())
        artifact = build_artifact(pr_number, base_sha, head_sha, checks, changes)
        args.artifact.parent.mkdir(parents=True, exist_ok=True)
        args.artifact.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"evidence audit error: {exc}", file=sys.stderr)
        return 2

    summary = _summary(checks)
    print(summary, end="")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(summary)

    flagged = any(check.status == "flag" for check in checks)
    return 1 if args.strict and flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
