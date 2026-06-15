#!/usr/bin/env python3
"""Validate repository engineering controls against .github/control-policy.json.

Stdlib-only by design. This is a conservative structural audit, not a full YAML
interpreter. It checks the workflow patterns this repository relies on:
full-SHA actions, explicit permissions, concurrency, job timeouts, read-only PR
checkout, and required control files/workflows.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / ".github" / "control-policy.json"
WORKFLOW_DIR = ROOT / ".github" / "workflows"

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
ACTION_REF = re.compile(r"(?P<action>[^\s#]+)@(?P<ref>[^\s#]+)")
NAME_LINE = re.compile(r"^name:\s*(?P<name>.+?)\s*$")
USES_LINE = re.compile(r"uses:\s*(?P<uses>[^\s#]+)")
JOB_LINE = re.compile(r"^  (?P<job>[A-Za-z0-9_-]+):\s*(?:#.*)?$")


def active_line(line: str) -> str:
    """Return the line content before comments, preserving indentation.

    This deliberately implements only the workflow subset the audit needs. It is
    not a full YAML tokenizer; it avoids treating comments as active controls.
    """

    if line.lstrip().startswith("#"):
        return ""
    return line.split("#", 1)[0].rstrip()


def active_lines(text: str) -> list[str]:
    return [line for raw in text.splitlines() if (line := active_line(raw))]


def load_policy() -> dict:
    try:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("ERROR required-file .github/control-policy.json: missing", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(policy, dict):
        print("ERROR policy: top-level JSON must be an object", file=sys.stderr)
        raise SystemExit(1)
    return policy


def workflow_files() -> list[Path]:
    if not WORKFLOW_DIR.is_dir():
        return []
    return sorted(
        path
        for path in WORKFLOW_DIR.iterdir()
        if path.is_file() and path.suffix in {".yml", ".yaml"}
    )


def workflow_name(text: str) -> str | None:
    for line in active_lines(text):
        match = NAME_LINE.match(line)
        if match:
            return match.group("name").strip().strip('"\'')
    return None


def has_top_level_key(text: str, key: str) -> bool:
    needle = f"{key}:"
    return any(
        line == needle or line.startswith(f"{needle} ")
        for line in active_lines(text)
    )


def top_level_concurrency_group_ok(text: str) -> bool:
    lines = active_lines(text)
    for index, line in enumerate(lines):
        if line == "concurrency:":
            block: list[str] = []
            for next_line in lines[index + 1 :]:
                if next_line and not next_line.startswith(" "):
                    break
                block.append(next_line)
            joined = "\n".join(block)
            has_group = "group:" in joined and (
                "github.ref" in joined or "github.event.pull_request.number" in joined
            )
            has_cancel = "cancel-in-progress: true" in joined
            return has_group and has_cancel
    return False


def job_blocks(text: str) -> dict[str, str]:
    lines = active_lines(text)
    jobs: dict[str, list[str]] = {}
    current: str | None = None
    in_jobs = False
    for line in lines:
        if line == "jobs:":
            in_jobs = True
            current = None
            continue
        if not in_jobs:
            continue
        if line and not line.startswith(" "):
            break
        match = JOB_LINE.match(line)
        if match:
            current = match.group("job")
            jobs[current] = [line]
            continue
        if current is not None:
            jobs[current].append(line)
    return {job: "\n".join(block) for job, block in jobs.items()}


def action_ref_is_pinned(uses: str) -> bool:
    uses = uses.strip().strip('"\'')
    if uses.startswith("./") or uses.startswith("../"):
        return True
    match = ACTION_REF.search(uses)
    if not match:
        return False
    return bool(FULL_SHA.fullmatch(match.group("ref")))


def checkout_persists_credentials(lines: list[str], index: int) -> bool:
    """Return True when a checkout step lacks active persist-credentials: false."""

    start = active_line(lines[index])
    if not start:
        return True
    start_indent = len(start) - len(start.lstrip())

    for raw in lines[index + 1 :]:
        line = active_line(raw)
        if not line:
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent <= start_indent and stripped.startswith("- "):
            break
        if indent <= 2 and not stripped.startswith(("with:", "env:", "name:", "run:")):
            break
        if stripped == "persist-credentials: false":
            return False
    return True


def has_active_text(text: str, needle: str) -> bool:
    return any(needle in line for line in active_lines(text))


def audit_workflow(path: Path, policy: dict, failures: list[str]) -> str | None:
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    name = workflow_name(text)

    rules = policy.get("workflow_rules", {})
    if rules.get("require_top_level_permissions") and not has_top_level_key(
        text, "permissions"
    ):
        failures.append(f"workflow-permissions {rel}: missing top-level permissions")
    if rules.get("require_top_level_concurrency") and not top_level_concurrency_group_ok(
        text
    ):
        failures.append(
            f"workflow-concurrency {rel}: missing scoped concurrency/cancel-in-progress"
        )
    if rules.get("prohibit_pull_request_target") and has_active_text(
        text, "pull_request_target"
    ):
        failures.append(f"pull-request-target {rel}: pull_request_target is prohibited")
    if rules.get("prohibit_fork_checkout") and has_active_text(
        text, "ref: ${{ github.head_ref }}"
    ):
        failures.append(f"fork-checkout {rel}: fork-head checkout is prohibited")
    if rules.get("prohibit_fork_scan_skip") and has_active_text(
        text, "head.repo.full_name == github.repository"
    ):
        failures.append(f"fork-scan {rel}: fork PR scan skip is prohibited")

    if rules.get("require_job_timeouts"):
        for job, block in job_blocks(text).items():
            if not re.search(
                r"^    timeout-minutes:\s*\d+\s*$", block, flags=re.MULTILINE
            ):
                failures.append(f"job-timeout {rel}: job {job} missing timeout-minutes")

    for index, raw_line in enumerate(lines):
        line = active_line(raw_line)
        if not line:
            continue
        uses_match = USES_LINE.search(line)
        if not uses_match:
            continue
        uses = uses_match.group("uses").strip().strip('"\'')
        if rules.get("require_full_sha_actions") and not action_ref_is_pinned(uses):
            failures.append(f"action-pin {rel}: {uses} is not pinned to a full commit SHA")
        if rules.get("require_checkout_persist_credentials_false"):
            if uses.startswith("actions/checkout@") and checkout_persists_credentials(
                lines, index
            ):
                failures.append(
                    f"checkout-credentials {rel}: checkout must set persist-credentials: false"
                )

    if not name:
        failures.append(f"workflow-name {rel}: missing workflow name")
    return name


def main() -> int:
    policy = load_policy()
    failures: list[str] = []

    for required in policy.get("required_files", []):
        path = ROOT / required
        if not path.is_file() or path.stat().st_size == 0:
            failures.append(f"required-file {required}: missing or empty")

    for instruction in policy.get("instruction_sources", []):
        path = ROOT / instruction
        if not path.is_file() or len(path.read_text(encoding="utf-8").strip()) < 80:
            failures.append(f"instruction-source {instruction}: missing or not substantive")

    workflows = workflow_files()
    names = {name for path in workflows if (name := audit_workflow(path, policy, failures))}
    for required_name in policy.get("required_workflows", []):
        if required_name not in names:
            failures.append(f"required-workflow {required_name}: stable workflow name not found")

    if failures:
        for failure in failures:
            print(f"ERROR {failure}", file=sys.stderr)
        print(f"control-audit: {len(failures)} failure(s)", file=sys.stderr)
        return 1

    scanner_mode = policy.get("scanner_mode", "unknown")
    print(f"control-audit: PASS ({len(workflows)} workflows, scanner={scanner_mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
