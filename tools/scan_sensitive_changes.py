#!/usr/bin/env python3
"""Scan added Git diff lines for secrets and high-confidence identifiers.

This is a narrow commit gate, not a HIPAA de-identification determination. It
deliberately does not detect names, addresses, URLs, IP addresses, or bare dates.
Findings report only a detector ID, path, and line number; matched values are
never printed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys
from typing import Iterable


SYNTHETIC_SENTINELS = (
    "synthetic.person" + "@" + "example.invalid",
    "000" + "-00-0000",
    "+1-555" + "-010" + "-0000",
    "4242" + " 4242 4242 4242",
    "MRN" + ": SYNTHETIC-000",
    "DOB" + ": 1900-01-01",
)

SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|client[_-]?secret|password|passwd|secret|token)\b"
        r"\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}"
    ),
)

DETECTORS = (
    (
        "private-key",
        re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    ),
    ("email", re.compile(r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("ssn", re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")),
    (
        "phone",
        re.compile(
            r"(?<!\d)(?:\+?1[-. ]?)?\(?[2-9]\d{2}\)?[-. ]\d{3}[-. ]\d{4}(?!\d)"
        ),
    ),
    (
        "mrn",
        re.compile(
            r"(?i)\b(?:mrn|medical record(?: number)?)\s*[:=#-]?\s*"
            r"[A-Z0-9][A-Z0-9-]{3,}\b"
        ),
    ),
    (
        "dob",
        re.compile(
            r"(?i)\b(?:dob|date of birth)\s*[:=#-]?\s*"
            r"(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b"
        ),
    ),
)

CARD_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
PROTECTED_PATHS = (
    re.compile(r"(?:^|/)\.env(?:\.|$)", re.IGNORECASE),
    re.compile(r"(?:^|/)(?:id_rsa|id_ed25519)(?:\.|$)", re.IGNORECASE),
    re.compile(r"\.(?:key|pem|p12|pfx)$", re.IGNORECASE),
    re.compile(r"(?:^|/)(?:credentials|secrets?)\.(?:json|ya?ml|txt)$", re.IGNORECASE),
    re.compile(
        r"(?:^|/)(?:phi|real[-_]?patient|patient[-_]?exports?|private[-_]?records?)(?:/|$)",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True, order=True)
class Finding:
    detector_id: str
    path: str
    line: int


def _is_fixture_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return bool(parts) and parts[0] in {"tests", "data"}


def _without_allowed_sentinels(path: str, line: str) -> str:
    if not _is_fixture_path(path):
        return line
    for sentinel in SYNTHETIC_SENTINELS:
        line = line.replace(sentinel, "<synthetic-sentinel>")
    return line


def _passes_luhn(value: str) -> bool:
    digits = [int(char) for char in value if char.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    parity = len(digits) % 2
    total = 0
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def scan_added_line(path: str, line_number: int, line: str) -> list[Finding]:
    scrubbed = _without_allowed_sentinels(path, line)
    findings: list[Finding] = []

    if any(pattern.search(scrubbed) for pattern in SECRET_PATTERNS):
        findings.append(Finding("secret", path, line_number))
    for detector_id, pattern in DETECTORS:
        if pattern.search(scrubbed):
            findings.append(Finding(detector_id, path, line_number))
    if any(_passes_luhn(match.group(0)) for match in CARD_CANDIDATE.finditer(scrubbed)):
        findings.append(Finding("payment-card", path, line_number))
    return findings


def scan_diff(diff_text: str) -> list[Finding]:
    findings: set[Finding] = set()
    path: str | None = None
    new_line = 0

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("+++ "):
            marker = raw_line[4:]
            path = None if marker == "/dev/null" else marker.removeprefix("b/")
            if path and any(pattern.search(path) for pattern in PROTECTED_PATHS):
                findings.add(Finding("protected-path", path, 0))
            continue

        if raw_line.startswith("@@ "):
            match = re.search(r"\+(\d+)(?:,(\d+))?", raw_line)
            if match:
                new_line = int(match.group(1))
            continue

        if path is None or raw_line.startswith(("diff --git ", "--- ")):
            continue
        if raw_line.startswith("+"):
            findings.update(scan_added_line(path, new_line, raw_line[1:]))
            new_line += 1
        elif raw_line.startswith(" "):
            new_line += 1

    return sorted(findings)


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
        message = result.stderr.strip() or "git command failed"
        raise RuntimeError(message)
    return result.stdout


def _resolve_commit(ref: str) -> str:
    resolved = _run_git(["rev-parse", "--verify", f"{ref}^{{commit}}"]).strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", resolved):
        raise RuntimeError("git returned an invalid commit ID")
    return resolved


def _ci_range() -> tuple[str, str]:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path:
        with open(event_path, encoding="utf-8") as handle:
            event = json.load(handle)
        pull_request = event.get("pull_request", {})
        base_sha = pull_request.get("base", {}).get("sha")
        head_sha = pull_request.get("head", {}).get("sha")
        if base_sha and head_sha:
            return _resolve_commit(base_sha), _resolve_commit(head_sha)

    base_ref = os.environ.get("GITHUB_BASE_REF")
    if not base_ref:
        raise RuntimeError("CI mode requires a pull-request event or GITHUB_BASE_REF")
    return _resolve_commit(f"origin/{base_ref}"), _resolve_commit("HEAD")


def load_diff(mode: str, base: str | None) -> str:
    common = ["diff", "--unified=0", "--no-color", "--diff-filter=ACMR"]
    if mode == "staged":
        return _run_git([*common, "--cached", "--"])
    if mode == "ci":
        base_sha, head_sha = _ci_range()
        return _run_git([*common, f"{base_sha}...{head_sha}", "--"])
    if base is None:
        raise RuntimeError("base mode requires --base REF")
    base_sha = _resolve_commit(base)
    head_sha = _resolve_commit("HEAD")
    return _run_git([*common, f"{base_sha}...{head_sha}", "--"])


def _self_test() -> int:
    blocked = "ghp_" + ("A" * 36)
    diff = "\n".join(
        [
            "diff --git a/example.py b/example.py",
            "--- a/example.py",
            "+++ b/example.py",
            "@@ -0,0 +1 @@",
            "+token = " + blocked,
        ]
    )
    findings = scan_diff(diff)
    if findings != [Finding("secret", "example.py", 1)]:
        print("self-test failed", file=sys.stderr)
        return 1
    print("sensitive-change scanner self-test: OK")
    return 0


def _print_findings(findings: Iterable[Finding]) -> None:
    for finding in findings:
        print(
            f"BLOCK detector={finding.detector_id} "
            f"path={finding.path} line={finding.line}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--staged", action="store_true", help="scan staged changes")
    mode.add_argument("--ci", action="store_true", help="scan the pull-request range")
    mode.add_argument("--base", metavar="REF", help="scan REF...HEAD")
    mode.add_argument("--self-test", action="store_true", help="run an internal smoke test")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    selected_mode = "staged" if args.staged else "ci" if args.ci else "base"
    try:
        findings = scan_diff(load_diff(selected_mode, args.base))
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"sensitive-change scanner error: {exc}", file=sys.stderr)
        return 2

    if findings:
        _print_findings(findings)
        print(
            "Sensitive-change gate blocked the diff. Findings omit matched values.",
            file=sys.stderr,
        )
        return 1

    print("sensitive-change scan: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
