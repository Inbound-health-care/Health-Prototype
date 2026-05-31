#!/usr/bin/env python3
"""Conservative Git branch cleanup helper.

Default mode is read-only: it reports branch state and suggests safe cleanup
commands without deleting anything. Destructive cleanup requires both
``--delete-merged`` and ``--yes``.
"""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from typing import Iterable

PROTECTED_BRANCHES = {"main", "master", "develop", "development", "dev", "trunk"}


@dataclass(frozen=True)
class Branch:
    name: str
    current: bool = False


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def lines(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if line.strip()]


def current_branch() -> str:
    return git("branch", "--show-current").stdout.strip()


def local_branches() -> list[Branch]:
    result = git("branch", "--format=%(HEAD)|%(refname:short)")
    branches: list[Branch] = []
    for line in lines(result.stdout):
        marker, name = line.split("|", 1)
        branches.append(Branch(name=name, current=marker == "*"))
    return branches


def remote_branches() -> list[str]:
    result = git("branch", "-r", "--format=%(refname:short)", check=False)
    if result.returncode != 0:
        return []
    return [branch for branch in lines(result.stdout) if not branch.endswith("/HEAD")]


def merged_branches(base: str = "HEAD") -> list[str]:
    result = git("branch", "--merged", base, "--format=%(refname:short)")
    current = current_branch()
    return [
        branch
        for branch in lines(result.stdout)
        if branch != current and branch not in PROTECTED_BRANCHES
    ]


def branches_with_gone_upstream() -> list[str]:
    result = git(
        "for-each-ref",
        "--format=%(refname:short)|%(upstream:track)",
        "refs/heads",
    )
    stale: list[str] = []
    for line in lines(result.stdout):
        name, _, tracking = line.partition("|")
        if "gone" in tracking:
            stale.append(name)
    return stale


def print_list(title: str, values: Iterable[str]) -> None:
    values = list(values)
    print(f"\n{title} ({len(values)})")
    if not values:
        print("  none")
        return
    for value in values:
        print(f"  {value}")


def delete_merged(branches: list[str], yes: bool) -> int:
    if not branches:
        print("\nNo merged local branches are eligible for deletion.")
        return 0
    if not yes:
        print("\nDry run only. Re-run with --delete-merged --yes to delete eligible merged branches.")
        for branch in branches:
            print(f"  git branch -d {branch}")
        return 0

    failures = 0
    for branch in branches:
        result = git("branch", "-d", branch, check=False)
        if result.returncode == 0:
            print(f"Deleted {branch}")
        else:
            failures += 1
            print(f"Failed to delete {branch}: {result.stderr.strip()}")
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit local Git branches safely.")
    parser.add_argument(
        "--delete-merged",
        action="store_true",
        help="Delete merged local branches, excluding current/protected branches.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm deletion when used with --delete-merged.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current = current_branch() or "(detached HEAD)"
    locals_ = local_branches()
    remotes = remote_branches()
    merged = merged_branches()
    gone = branches_with_gone_upstream()

    print(f"Current branch: {current}")
    print_list("Local branches", [f"{'* ' if branch.current else '  '}{branch.name}" for branch in locals_])
    print_list("Remote branches", remotes)
    print_list("Merged local branches eligible for deletion", merged)
    print_list("Local branches with gone upstream", gone)

    if args.delete_merged:
        return delete_merged(merged, args.yes)

    print("\nNo changes made. This command is read-only unless --delete-merged --yes is used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
