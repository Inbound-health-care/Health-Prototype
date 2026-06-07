# 0024 — Governance: JOURNAL.md retired (chat-only) + LICENSE = Apache-2.0

**Date:** 2026-06-07
**Evidence level:** IMPLEMENTED_UNVERIFIED — docs/governance only (no engine change); `make check`
green at commit. Promotes to CONFIRMED_USER_SIDE when Scott confirms the resolution.
**Type:** Governance / repo hygiene
**Resolves:** `docs/AUDIT_2026-06-07.md` Tier 1 #1 (JOURNAL contradiction) and #2 (no LICENSE).

## Context
The 2026-06-07 repo audit flagged two self-contradictory or legally-loose governance gaps:

1. **JOURNAL.md contradiction.** `CLAUDE.md` ("End-session protocol", set 2026-06-06) and
   `.claude/commands/handoff.md` declare the journal **retired — the end-session diary is
   chat-only, "never a committed JOURNAL.md."** But `JOURNAL.md` is git-tracked (32 KB) and was
   still being committed (entry #34, `d71c3e8`, 2026-06-06), and **five** docs cite it as the
   canonical narrative source (`AGENTS.md`, `PROJECT_MAP.md`, `LOAD.md`,
   `docs/COLD_START_HANDOFF.md`, the repo-onboard skill). The rule said one thing; practice and
   the pointers said another.
2. **No LICENSE.** Absent a license file the repo defaults to "all rights reserved," which is
   the wrong implicit posture for a public-facing prototype.

## Decision
**(1) Retire JOURNAL.md (chat-only), keep the file as a frozen archive.** Scott's call
(2026-06-07): align everything to the already-written chat-only protocol rather than re-open
committed-journal writing. The end-session diary lives in **chat only**; sessions close
read-only (CLAUDE.md / handoff.md unchanged — they were already correct). `JOURNAL.md` is **not
deleted** — it is a historical record of the pre-protocol entries — but it carries an ARCHIVED
banner and is **not updated going forward**. The five citing docs are reworded to call it a
"historical narrative archive," not the live canonical narrative.

**(2) License = Apache-2.0.** Scott's call (2026-06-07): Apache-2.0 over MIT. The explicit
patent grant + defensive-termination clause give clearer legal footing for a health-adjacent
tool than MIT's silence on patents (web-confirmed 2026-06-07, RESEARCH_ONLY: Apache-2.0 is the
commonly-recommended choice for patent-sensitive / healthcare domains). Full canonical text in
`LICENSE`; copyright line `Copyright 2026 Inbound-health-care` (holder adjustable). README gains
a short License section.

## Consequences
- One source of truth for the session-diary rule: chat-only, read-only close. No more
  contradiction between the protocol and the doc pointers.
- `JOURNAL.md` stays readable as history without implying it is still maintained.
- The repo now carries an explicit, permissive, patent-aware license instead of implicit ARR.
- No engine/test behavior change.

## Confirmation
- `JOURNAL.md` banner + the five citing-doc edits + `LICENSE` + README section land together.
- `make check` green (governance/docs only; counts unchanged by this ADR).
- Promotes to CONFIRMED_USER_SIDE on Scott's ack.
