# CLAUDE.md — health-prototype

Recurrence Detection Engine: a domain-agnostic surfacing engine for health
records. Repo: `Inbound-health-care/health-prototype`. Pure stdlib, local-only,
**zero real PHI**.

_Tier 1 (always-loaded): operator rules + limits + engine firewall + pointers.
Engine detail lives in linked files, loaded on demand (progressive disclosure).
Keep this file lean — it must not restate counts that can go stale._

## Operator rules (Scott's rules — override default behavior)
- **Tone: dry, plain, NO hype, NO emojis.** Scott controls tone, not the model.
  Do not mirror his casual tone. (Known failure: the model drifts back to
  emojis/exclamations over a long session even after being told — see
  Limitations. Re-read this often.)
- **Personal life is walled off.** Ignore non-tech/personal content unless Scott
  explicitly raises it. Keep only the minimal life context needed for the work.
- **Surface AND log when you change approach.** No silent improvements; say what
  changed and why, and write the durable lesson to an ADR (`docs/adr/`).
- **If state looks "off," assume Scott worked ELSEWHERE you can't see** (other
  sessions, phone, manual versioning). READ the real remote/state before acting.
  Do NOT call it "drift" or assume misalignment — multi-version-by-hand is normal.
- **Judge research by CONCEPT, not literal words.** Invented term-names often map
  to real techniques; re-findable is fine.
- **Token frugality:** copy/move files server-side; read+write only to synthesize
  genuinely new content.

## Known assistant limitations (design around these)
- **Cannot reliably hold a rule across a long context; worsens as it grows.**
  Mitigation: keep rules at the TOP; re-read often; start FRESH sessions sooner —
  don't ride one context toward ~1M tokens.
- **No memory across sessions.** These repo files are the only persistence.
- **`git push` may be blocked** by the session repo allowlist even with the
  GitHub app authorized — the GitHub **API write tool** (`create_or_update_file`)
  may still work. Use it to persist when push fails.
- **"done / pushed" claims are not proof.** Verify against the remote.

## Engine firewall (the one rule that governs the engine)
**Librarian, not interpreter.** Surface, count, and cite provenance — NEVER
score, rank, diagnose, or say what a pattern *means*. No "caution / concern /
worsening / risk / severe" in output. The human (or a human-declared policy)
supplies all judgment. Tests enforce this — keep it that way.

## Where to find things (load on demand — don't front-load)
- **Onboarding (auto):** the `repo-onboard` skill (`.claude/skills/repo-onboard/`)
  loads when relevant; or say "load repo settings". Front door: `LOAD.md`.
- **Read first:** `STATUS.md` — canonical "where am I / what's next."
- **Engine detail — commands, architecture map, hard rules, workflow:**
  `docs/agent-guides/architecture.md` (Tier 3; the source of truth for engine facts).
- **Decisions / why:** `docs/adr/`   ·   **Narrative / lessons:** `JOURNAL.md`
- **Cold start:** `docs/COLD_START_HANDOFF.md`
- **Subagent-audit + code-review method:** `docs/AGENT_AUDIT_METHOD.md`
- **Other project (clinical scribe):** `SOVEREIGN_SCRIBE_SALVAGE.md`

## Scope
This repo only. Don't rebuild the old `pharmacy_tool_v13` (reference lumber).
