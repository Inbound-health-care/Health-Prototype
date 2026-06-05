#!/usr/bin/env bash
# SessionStart hook — runs at the start of every Claude Code session (incl. web).
# Purpose: orient a FRESH, memory-less Claude instance and let it verify its work.
# Keep stdout short + high-signal: this text is injected into Claude's context.
# Always exit 0 (a nonzero exit blocks session start); warn instead of failing.

set -u
echo "=== health-prototype session start ==="

# 1. Orientation: point the fresh instance at the durable docs FIRST.
echo "READ FIRST: AGENTS.md (source of truth: rules + firewall), then CLAUDE.md (Claude-specific), then STATUS.md (state)."
echo "Core rule: librarian-not-interpreter — surface/count/cite, never interpret."
echo "Policy: read SECURITY_AND_TOOL_POLICY.md before any write/delete/install/send."
echo "Emit a LOAD TRACE now — template: LOAD_TRACE_TEMPLATE.md."

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

# 3. Dev-tool availability (optional; engine itself is pure stdlib).
#    Prevents the recurring "python -m pytest: no module named pytest" confusion —
#    pytest et al. live on PATH, not on system python. See docs/TOOLCHAIN_AUDIT_*.
_have=""; for t in pytest ruff mypy uv; do command -v "$t" >/dev/null 2>&1 && _have="$_have $t"; done
echo "dev tools present:${_have:- (none)}  | others on-demand via 'uvx <tool>' (coverage/bandit/ty)"

# 4. Quick commands reminder.
echo "Run: make test | python recurrence.py --self-test | --demo/--demo-v1/--demo-gap/--demo-frequency"
echo "More: make tools (what's installed) | make typecheck | make cov | make fmt-check"
echo "=== end session start ==="
exit 0
