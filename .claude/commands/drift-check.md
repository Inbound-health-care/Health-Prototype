---
description: Drift / garbage-collection audit (Scott's METHOD-003) — find stale claims, wrong numbers, source-of-truth conflicts
---

Run a drift-control audit (every ~3–5 build cycles). Surface, don't fix silently:

1. **Stale claims:** statements in docs/STATUS/CLAUDE.md that are no longer true
   (e.g., "37 tests" when the count changed; "pushed" that didn't land).
2. **Wrong numbers / facts:** figures that drifted from their source (the way the
   "PolarQuant 8×" number was wrong). Check anything quantitative against reality.
3. **Source-of-truth conflicts:** two docs that disagree; duplicate files; an old
   version being treated as current.
4. **Evidence-level check:** anything labeled CONFIRMED that's really RESEARCH_ONLY
   or IMPLEMENTED_UNVERIFIED. Re-label, don't overclaim.

Output a short findings list (problem → location → suggested fix). Mark dead
things SUPERSEDED rather than deleting. Ask before any large change.

Scope (optional): $ARGUMENTS
