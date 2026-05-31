# Doc Discipline — salvaged from `2026 methods` (Drive)

_Extracted 2026-05-31 so the source Drive files can be trashed. These are the
only practices worth carrying forward; the rest of the old corpus is clutter._
_Evidence level: IMPLEMENTED_UNVERIFIED (adopt, prove over a few sessions)._

## 1. Evidence levels on every claim  (was METHOD-007)
Tag what you/Claude assert by proof strength, so "I researched it" is never
confused with "it works":
- `CONFIRMED_USER_SIDE` — you ran it and saw it work (highest truth)
- `CONFIRMED_ASSISTANT_SIDE` — Claude ran/tested it in its sandbox
- `IMPLEMENTED_UNVERIFIED` — written but not yet proven
- `RESEARCH_ONLY` — from reading/search; not implemented here
- `SUPERSEDED` / `DEPRECATED` — kept only as history
**Why it earns its place:** directly fixes a failure we already hit — "pushed ✅"
reported as done (assistant-side) when it wasn't user-confirmed, and a doc
stamped "LIVE/DEPLOYED" that was only a vision.

## 2. ADR Confirmation field  (was METHOD-005)
Every Architecture Decision Record states not just Context / Decision /
Consequences but **Confirmation: how this is verified.**
- e.g. Decision: "exact-match is the default" → Confirmation:
  `tests/test_fuzzy.py::test_defaults_do_not_merge`.
**Why:** turns decisions into *checked* decisions; no ADR is ceremony.

## 3. Drift control / garbage collection  (was METHOD-003)
Every ~3–5 build cycles, do a quick audit for: stale claims, wrong numbers,
duplicate docs, and source-of-truth conflicts. Mark dead things `SUPERSEDED`
rather than leaving them to mislead.
**Why:** this is exactly the audit that caught the wrong "PolarQuant 8×" number
and the mislabeled vision docs. Make it routine, not accidental.

---
### Research firewall (the rule that governs all three)
A researched method is **not project truth** until: source identified → ADR
accepts it → a test/check proves it → STATUS reflects it. Until then it stays
`RESEARCH_ONLY`. (This is the rule the old Exoskeleton docs violated by calling
themselves "deployed.")
