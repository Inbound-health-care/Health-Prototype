---
description: End-of-session protocol — check state + drift, close everything, list for Scott to audit, act on his calls; read-only + chat-only diary AFTER the session is fully closed
---

End-session protocol (set by Scott, 2026-06-06). Sessions END this way — work the
steps IN ORDER, do not skip ahead:

1. **Check the current state of EVERYTHING + run a drift check.** Open PRs and their CI;
   the working branch vs `main`; any unmerged/orphaned branches; STATUS open loops;
   uncommitted work. Run the drift sweep (Scott's METHOD-003 / `/drift-check`): stale
   claims, wrong numbers, source-of-truth conflicts, evidence-level overclaims.

2. **Make sure everything is closed — blocking AND non-blocking.** Every open PR merged
   or closed; CI green; no orphaned branches; STATUS + docs reconciled to `main`; nothing
   left dangling. If something genuinely can't close, say why.

3. **List everything you find, for Scott to audit.** One scannable list: PRs (state + CI),
   branches, open loops, drift findings, anything pending. SURFACE — don't decide for him.

4. **Do whatever Scott says.** He reviews the list and directs (merge / close / fix /
   leave). Act on his calls. The per-PR merge ask-gate still applies (CLAUDE.md).

5. **ONLY AFTER the final push/merge (his or yours), switch to READ-ONLY.** No more repo
   writes, commits, or pushes. Then write the session **diary in CHAT only** — never a
   committed `JOURNAL.md` / `*handoff*.md` file. Scott logs his own thoughts as he sees fit.

NOTE — this REPLACES the old "write JOURNAL.md + STATUS + commit + push" handoff. The
reflective diary is now CHAT-ONLY and happens AFTER closure. The session's actual WORK
(code, STATUS/doc reconciliation) is still committed/pushed as part of step 2's closing —
read-only kicks in only once everything is closed. The `Stop` hook
(`.claude/hooks/stop_handoff_guard.py`) stays as a dormant safety net: it fires only on an
uncommitted `*handoff*.md`, which this protocol never creates.

Extra notes to capture: $ARGUMENTS
