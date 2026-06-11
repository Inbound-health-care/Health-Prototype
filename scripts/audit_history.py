#!/usr/bin/env python3
"""Import reviewed evidence artifacts and produce proposal-only retrospectives."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Iterable

if __package__:
    from scripts.audit_evidence import SCHEMA
else:
    from audit_evidence import SCHEMA


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HISTORY = ROOT / "docs" / "evidence-audit-history.ndjson"
SHA = re.compile(r"[0-9a-f]{40}")
VALID_SEVERITIES = {"notice", "warning", "error"}
VALID_STATUSES = {"pass", "flag"}


def validate_artifact(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("artifact must be a JSON object")
    if value.get("schema") != SCHEMA:
        raise ValueError("unsupported artifact schema")
    expected_keys = {
        "schema",
        "pr_number",
        "base_sha",
        "head_sha",
        "generated_at",
        "checks",
        "changed_path_category_counts",
    }
    if set(value) != expected_keys:
        raise ValueError("artifact contains unsupported fields")
    if not isinstance(value.get("pr_number"), int):
        raise ValueError("invalid PR number")
    for key in ("base_sha", "head_sha"):
        item = value.get(key)
        if not isinstance(item, str) or not SHA.fullmatch(item):
            raise ValueError(f"invalid {key}")
    generated_at = value.get("generated_at")
    if not isinstance(generated_at, str):
        raise ValueError("invalid generated_at")
    try:
        datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid generated_at") from exc

    checks = value.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("checks must be a non-empty list")
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("invalid check entry")
        if set(check) != {"id", "severity", "status"}:
            raise ValueError("check contains unsupported fields")
        if not isinstance(check.get("id"), str) or not check["id"].startswith("EVIDENCE_"):
            raise ValueError("invalid check ID")
        if check.get("severity") not in VALID_SEVERITIES:
            raise ValueError("invalid check severity")
        if check.get("status") not in VALID_STATUSES:
            raise ValueError("invalid check status")

    counts = value.get("changed_path_category_counts")
    if not isinstance(counts, dict):
        raise ValueError("invalid changed-path counts")
    if not all(
        isinstance(key, str) and isinstance(count, int) and count >= 0
        for key, count in counts.items()
    ):
        raise ValueError("invalid changed-path count entry")
    return value


def load_history(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    entries: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entries.append(validate_artifact(json.loads(line)))
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"invalid history line {line_number}: {exc}") from exc
    return entries


def import_artifacts(history_path: Path, artifact_paths: Iterable[Path]) -> int:
    existing = load_history(history_path)
    seen = {entry["head_sha"] for entry in existing}
    additions: list[dict[str, object]] = []

    for path in artifact_paths:
        artifact = validate_artifact(json.loads(path.read_text(encoding="utf-8")))
        if artifact["head_sha"] in seen:
            continue
        seen.add(artifact["head_sha"])
        additions.append(artifact)

    if additions:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8", newline="\n") as handle:
            for artifact in additions:
                handle.write(json.dumps(artifact, sort_keys=True, separators=(",", ":")) + "\n")
    return len(additions)


def retrospective(entries: Iterable[dict[str, object]]) -> list[str]:
    unique: dict[str, dict[str, object]] = {}
    for entry in entries:
        unique[str(entry["head_sha"])] = entry
    if len(unique) < 5:
        raise ValueError("retrospective requires at least 5 unique audit entries")

    flags: Counter[str] = Counter()
    for entry in unique.values():
        for check in entry["checks"]:  # type: ignore[index]
            if check["status"] == "flag":
                flags[str(check["id"])] += 1

    if not flags:
        return ["PROPOSAL no check tuning; five-entry history contains no flags"]
    return [
        f"PROPOSAL review check_id={check_id} flagged_runs={count}"
        for check_id, count in sorted(flags.items(), key=lambda item: (-item[1], item[0]))
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    subparsers = parser.add_subparsers(dest="command", required=True)
    import_parser = subparsers.add_parser("import", help="append reviewed artifacts")
    import_parser.add_argument("artifacts", nargs="+", type=Path)
    subparsers.add_parser("retro", help="print tuning proposals after five entries")
    args = parser.parse_args(argv)

    try:
        if args.command == "import":
            added = import_artifacts(args.history, args.artifacts)
            print(f"history import: added={added}")
            return 0
        proposals = retrospective(load_history(args.history))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"audit history error: {exc}", file=sys.stderr)
        return 2

    for proposal in proposals:
        print(proposal)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
