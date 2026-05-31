#!/usr/bin/env bash
# SessionStart hook — runs at the start of every Claude Code session (incl. web).
# Purpose: orient a FRESH, memory-less Claude instance and let it verify its work.
# Keep stdout short + high-signal: this text is injected into Claude's context.
# Always exit 0 (a nonzero exit blocks session start); warn instead of failing.

set -u
echo "=== health-prototype session start ==="

# 1. Orientation: point the fresh instance at the durable docs FIRST.
echo "READ FIRST: STATUS.md (where am I / next), then CLAUDE.md (rules + firewall)."
echo "Core rule: librarian-not-interpreter — surface/count/cite, never interpret."

# 2. Verify the toolchain works (pure stdlib, no install needed).
if command -v python3 >/dev/null 2>&1; then
  echo "python: $(python3 --version 2>&1)"
  if python3 -m unittest discover -s tests -t . >/tmp/_tests.log 2>&1; then
    echo "tests: PASS"
  else
    echo "tests: FAIL — see /tmp/_tests.log (last line: $(tail -1 /tmp/_tests.log))"
  fi
  if python3 recurrence.py --self-test >/tmp/_selftest.log 2>&1; then
    echo "self-test: $(tail -1 /tmp/_selftest.log)"
  fi
else
  echo "WARN: python3 not found."
fi

# 3. Quick commands reminder.
echo "Run: make test | python recurrence.py --self-test | --demo/--demo-v1/--demo-gap/--demo-frequency"
echo "=== end session start ==="
exit 0
