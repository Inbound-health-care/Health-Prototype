#!/usr/bin/env python3
"""Stop hook: refuse to end a session while a handoff file is uncommitted.

WHY THIS EXISTS
  A SESSION_HANDOFF_*.md written but never committed is LOST when the ephemeral
  web container is reclaimed — it never reaches the remote. That is exactly how
  one session's task vanished (the handoff was attached as a local file that the
  next fresh clone didn't have). This hook closes that gap.

DESIGN
  - Scope is deliberately NARROW: it only fires on handoff-shaped files
    (name contains "handoff", ends ".md"). Ordinary mid-session uncommitted
    work is never nagged.
  - Loop-safe two ways: it self-clears the moment the handoff is committed (the
    block condition becomes false), and it honors `stop_hook_active` so it blocks
    at most once per continue-cycle.
  - Fail-open: any error (not a git repo, git missing) -> allow stop, never trap.

CONTRACT (Claude Code Stop hook)
  stdin  : JSON with at least {"stop_hook_active": bool, ...}
  block  : print {"decision":"block","reason":"..."} on stdout, exit 0
  allow  : no stdout, exit 0
"""
import json
import subprocess
import sys


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}

    # Loop guard: already continuing because of a prior Stop block -> let it stop.
    if data.get("stop_hook_active"):
        return

    try:
        porcelain = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except Exception:
        return  # not a git repo / git unavailable -> never block

    pending = []
    for line in porcelain.splitlines():
        path = line[3:].strip()          # drop the "XY " status prefix
        if "->" in path:                 # rename entry -> take the new path
            path = path.split("->")[-1].strip()
        if path.startswith(".claude/"):  # harness files named "handoff" are not
            continue                     # session artifacts -> never block on them
        low = path.lower()
        if "handoff" in low and low.endswith(".md"):
            pending.append(path)

    if not pending:
        return

    reason = (
        "Uncommitted handoff file(s): " + ", ".join(pending) + ". "
        "A handoff that is not committed is LOST when the web container is "
        "reclaimed — it never reaches origin (this is how a prior session's task "
        "vanished). Before ending: `git add` the handoff plus STATUS.md / "
        "JOURNAL.md, commit with a clear message, and push to the working branch. "
        "Then end again."
    )
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
