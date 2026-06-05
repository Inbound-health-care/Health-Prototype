# 0010 — Rename the "firewall" metaphor (librarian rule / allowlist / research gate)

**Date:** 2026-06-05
**Evidence level:** IMPLEMENTED_UNVERIFIED — terminology sweep + staleness audit; no behavior
change. CONFIRMED_ASSISTANT_SIDE (`make check` green — 117 tests / self-test 6+3 / `ruff` clean);
promotes to CONFIRMED_USER_SIDE when Scott runs it.
**Type:** Documentation / terminology

## Context
Scott found "firewall" overwrought, and in this repo the word was doing **three** different
jobs — so one term muddied three ideas:
1. the engine's **surface / count / cite, never interpret** rule;
2. the **legal** two layers in ADR 0009 (a HIPAA PHI allowlist + an FDA interpretation line);
3. the **evidence-level** rule in `docs/DOC_DISCIPLINE.md` ("research firewall" — a researched
   method is not project truth until an oracle proves it).

The engine already describes itself as "a **librarian, not an interpreter**," so the rename
leans on a metaphor that is already here rather than inventing a new one.

## Decision
Retire "firewall" repo-wide. Canonical term map (sense-aware — not a blind find/replace):

| Old ("firewall") sense | New term |
|---|---|
| surface/count/cite, never interpret (the engine's one rule; ADR 0009 Layer 2 / FDA) | **the librarian rule** |
| HIPAA / PHI layer — allowlist by construction (ADR 0009 Layer 1) | **the allowlist** |
| evidence-level rule — RESEARCH_ONLY until proven (`DOC_DISCIPLINE`, `new-phase`) | **the research gate** |
| loose "the legal firewall in one" (recurrence.py / README) | "the design principle and the **legal grounding** in one" |

**Scope:** every in-repo occurrence (~83 across 31 files) — code docstrings/comments
(`recurrence.py`, `extract.py`; no identifiers used the word), the six test-class names, the
control docs, ADR bodies 0002–0009, and the ADR 0009 file itself (`git mv`
`0009-firewall-legal-grounding.md` → `0009-legal-grounding.md`, retitled "Legal grounding: the
allowlist + the librarian rule") with the index + cross-references updated. The dated ADRs keep
their decisions/dates — this is a terminology refresh, not a history rewrite.

**Test-class renames** (behavior identical; the BANNED-word assertions are untouched):
`TestSurfacingFirewall` → `TestSurfacingLibrarianRule`; `TestCooccurrenceFirewall` →
`TestCooccurrenceLibrarianRule`; `TestCadenceChangeFirewall` → `TestCadenceChangeLibrarianRule`;
`TestReportFirewall` → `TestReportLibrarianRule`; `TestAllowlistFirewall` → `TestAllowlist`;
`TestFirewallBannedWords` → `TestLibrarianRuleBannedWords`.

**Folded in — a full staleness audit** (Scott asked for it alongside the rename). Reconciled the
docs to live `main` after PR #20 merged: suite 90 → **117** (engine 90 + extract 27); corrected
slice-1 "draft / not-yet-on-main / awaiting merge" claims (now MERGED); fixed the architecture
file/test counts (8 files/87 → 11 files/117) and the cold-start PR list (stopped at #13 → through
#20). Point-in-time numbers in dated/historical docs (TOOLCHAIN_AUDIT, ADR 0007 "87", ADR 0005
"68", JOURNAL) were left as records, not "fixed."

**One residue (flagged, not hidden):** the off-repo Drive file
`health-prototype/freetext-design/FIREWALL_legal_grounding.md` keeps its name — there is no Drive
rename tool in this environment, and its in-repo references point at the real filename. Renaming
it is a manual follow-up for Scott.

Rejected: "guardrail" and "boundary" (Scott picked "librarian rule"); collapsing the
evidence-level sense into "librarian rule" (it is a different concept — kept distinct as "research
gate"); rewriting the dated ADRs' decisions (only the term changed).

## Consequences
- One word no longer carries three meanings; each control is named for what it does.
- No engine/behavior change — comments, docstrings, test-class names, and docs only.
- ADR 0009's filename changed; future links must use `0009-legal-grounding.md`.

## Confirmation
- `grep -rin firewall .` (excluding `.git`) → only the off-repo Drive filename references remain
  (intentional, flagged above).
- `make check` green — 117 tests, self-test 6+3, `ruff` clean; the librarian rule's BANNED-word
  tests still pass (the control itself is unchanged).
- **Standing:** rename the Drive file `FIREWALL_legal_grounding.md` (manual) to close the residue.
