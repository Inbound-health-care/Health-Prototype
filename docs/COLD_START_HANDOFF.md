# COLD START HANDOFF
_For a fresh session with zero memory. Read this, then STATUS.md, then CLAUDE.md.
Last written 2026-05-31._

## Who you're working with
Scott — psychiatric NP building health AI. Works ~67% on phone (now also a PC
w/ RTX 5060 8GB, a Mac, S26 + S23, iPad incoming). Learns by building first,
naming later. Values brutal honesty over hype. Reads everything.

## Operator rules (NON-NEGOTIABLE — full list in CLAUDE.md "Operator rules")
1. **Dry tone, NO emojis, NO hype.** Scott sets tone, not you. Do not mirror him.
2. **Personal life is walled off.** Ignore non-tech/personal content unless he
   raises it. Keep only minimal life context.
3. **Surface AND log approach changes.** No silent improvements.
4. **If state looks "off," assume Scott did work ELSEWHERE you can't see** (other
   sessions/phone/manual versioning). READ the real state. Do NOT call it "drift."
5. **Judge research by CONCEPT not literal words.** Re-findable is fine.
6. **Token frugality:** copy/move server-side; read+write only to synthesize new.

## Known limitations to design around (found 2026-05-31)
- You **cannot reliably hold rules over a long context**, and it degrades faster
  the longer the window. Re-read CLAUDE.md's top often. Prefer SHORT sessions;
  don't ride one context to ~1M tokens — hand off and restart.
- No cross-session memory; the repo docs are the only persistence.
- `git push` may be blocked by the session repo allowlist even with the app
  authorized; the GitHub API write tool (create_or_update_file) may still work.
- Your "done/pushed" claims are not proof — verify against the remote.

## Project state (trust STATUS.md over this if they differ — STATUS is canonical)
- **health-prototype**: recurrence engine. v0 exact-match + v1 opt-in matching
  (normalize/synonyms/fuzzy) + **4 rules** (recurrence / gap / frequency /
  co-occurrence) + router/expert registry with `--report` (v0 and `--report-v1`).
  **68 tests green**, `ruff` clean, CI on Py 3.10-3.13. Firewall: surface/count/cite,
  NEVER interpret. PRs #1/#3/#4/#7 merged to `main`; branch protection active.
- A **5th** rule is a drop-in: append one `Expert(name, detect_x, format_x)` to
  `EXPERTS` and it joins `--report` automatically.
- A SECOND project exists (separate): **Sovereign Scribe / PACT** — local clinical
  SOAP scribe. Salvaged into `SOVEREIGN_SCRIBE_SALVAGE.md`. Not active in this repo.

## The docs that matter (read in this order)
1. `STATUS.md` — where am I / next step (CANONICAL, newest).
2. `CLAUDE.md` — operator rules + limits + engine rules + architecture.
3. `docs/adr/` — decision log (incl. the assistant's own process changes).
4. `JOURNAL.md` — the WHY / narrative / lessons (incl. limitations found).
5. `docs/SESSION_LOG_2026-05-31_full.md` — full prior-session audit.
6. `docs/AGENT_AUDIT_METHOD.md` — reusable subagent-audit playbook (use for code
   review too: brief -> run -> review HOW -> tighten brief -> repeat).

## Open loops (reconcile with STATUS.md)
- [ ] m2m corpus audit: ~89/200 April files done (~85% sound, concepts hold).
      Finish (version-chains as thinking-evolution) OR synthesize one "Capability
      Reference" (local-LLM / health-AI / reference). Resume detail in SESSION_LOG.
- [ ] Write "Local LLM Settings — Master Reference" (per-device/per-mode) — the
      recipe the April research pointed at but never became a doc.
- [ ] Next build increment: another rule (co-occurrence / cadence) OR free-text
      extraction OR `--report-v1`.

## First move for the fresh session
Confirm you read STATUS.md + CLAUDE.md (one sentence). Hold the operator rules.
Then ask Scott where to start. Do not assume; do not hype; do not emoji.
