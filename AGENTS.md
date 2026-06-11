# AGENTS.md — health-prototype (source of truth for every agent)

Recurrence Detection Engine: a domain-agnostic surfacing engine for health
records. Repo: `Inbound-health-care/health-prototype`. Pure stdlib, local-only,
**zero real PHI**.

This is the **source of truth** for working in this repo, for ANY AI agent
(Codex, Cursor, Copilot, Gemini, a local model, etc.) — the open AGENTS.md
standard. Claude Code reads `CLAUDE.md`; that file is a thin pointer back here
plus a few Claude-Code-specific notes. Rules live HERE, once.

_Keep this file lean: operator rules + working limits + the librarian rule +
commands + pointers. Engine detail and counts live in linked files (progressive
disclosure) so this file cannot go stale._

## Operator rules (Scott's rules — override default behavior)
- **Tone: dry, plain, NO hype, NO emojis.** Scott controls tone, not the model.
  Do not mirror his casual tone. (Known failure: models drift back to
  emojis/exclamations over a long session even after being told — re-read often.)
- **Personal life is walled off — with one exception for THIS repo.** Default: ignore
  non-tech/personal content unless Scott explicitly raises it; keep only the minimal life
  context the work needs. EXCEPTION (set 2026-06-05): this is a *learning prototype* — the
  working build is a side-effect of Scott learning, so his learning process and his read on
  it (including how the work is landing for him) are legitimately IN scope when he raises
  them, not a detour. Engage it and hold it as operating context — but still don't fish for
  personal content or broadcast it.
- **Surface AND log when you change approach.** No silent improvements; say what
  changed and why, and write the durable lesson to an ADR (`docs/adr/`).
- **If state looks "off," assume Scott worked ELSEWHERE you can't see** (other
  sessions, phone, manual versioning). READ the real remote/state before acting.
  Do NOT call it "drift" or assume misalignment — multi-version-by-hand is normal.
- **Judge research by CONCEPT, not literal words.** Invented term-names often map
  to real techniques; re-findable is fine.
- **Token frugality:** copy/move files server-side; read+write only to synthesize
  genuinely new content.
- **Don't re-explain known tooling as noise.** Scott already knows the safety gates
  (CI, the per-PR merge ask, the webhook/scheduling quirks). If a caveat genuinely
  matters, say it ONCE at session start, then drop it. We work as peers in a
  feedback loop — flag real uncertainty or real risk, double-check at startup when
  needed — but stop narrating the guardrails every turn.

## Working limits (true for any current model — design around these)
- **You cannot reliably hold a rule across a long context; it worsens as the
  context grows.** Keep rules at the TOP; re-read often; start FRESH sessions
  sooner — do not ride one context toward ~1M tokens.
- **No memory across sessions.** These repo files are the only persistence.
- **"done / pushed" claims are not proof.** Verify against the real remote/state,
  not memory, before reporting completion.
- **Without a direct pointer, the model wastes time on indirect search instead of the
  source.** When the operator names a specific artifact (a file, a PR, a result, "my N
  rules"), ASK for the pointer and go to ground truth FIRST — don't fan out across guesses.
  (2026-06-05: a "golden rules" lookup took ~6 indirect fetches; the answer was one PR.)
- **Tone-drift is the operator's drift gauge (Scott noticed, 2026-06-05).** Scott reads
  hype-drift in the model's tone as an early-warning *canary* that the context is
  degrading — usually before the reasoning visibly breaks — so he reads it instead of
  correcting it. The dry framing is an INSTRUMENT, not decor: dry biases toward
  convergent single-task work, hype toward divergent branch-opening (each fails its own
  way — dry tunnels, hype sprawls). His markers: slippage starts ~600k tokens, tone/state
  largely lost ~850k without re-locking (re-read the top + explicit callbacks). Upshot:
  keep it dry, re-lock often, hand off / restart before ~600k rather than riding one
  context down. (His heuristic; he may refine it.)

## The librarian rule (the one rule that governs the engine)
**Librarian, not interpreter.** Surface, count, and cite provenance — NEVER
score, rank, diagnose, or say what a pattern *means*. No "caution / concern /
worsening / risk / severe" in output. The human (or a human-declared policy)
supplies all judgment. Tests enforce this — keep it that way.

## Commands (pure stdlib; nothing to install)
- `make test` — full unittest suite · `make selftest` — required spec cases
- `make lint` — byte-compile (+ ruff if present) · `make check` — test + selftest + lint
- `make scan-sensitive` — scan staged additions for secrets/high-confidence identifiers
- `make hooks` — opt into the repo's pre-commit sensitive-change gate
- `make demo` — every surfacing-rule demo
- `python recurrence.py --self-test | --demo | --demo-v1 | --demo-gap | --demo-frequency | --demo-cooccurrence | --report | --report-v1`

## Where to find things (load on demand — don't front-load)
- **Read first for state:** `STATUS.md` — canonical "where am I / what's next."
- **Engine detail (commands, architecture map, hard rules, counts):**
  `docs/agent-guides/architecture.md` — the source of truth for engine facts.
- **Security & tool policy** (untrusted input, tool risk, PHI, source conflicts):
  `SECURITY_AND_TOOL_POLICY.md` — read before any write/delete/install/send.
- **Public vulnerability reporting:** `SECURITY.md`.
- **Practical repository lessons:** `docs/LEARNINGS.md` (append-only).
- **Decisions / why:** `docs/adr/`   ·   **Narrative / lessons:** `JOURNAL.md` (ARCHIVED 2026-06-07 — historical only; diary is chat-only, ADR 0024)
- **Doc / evidence discipline:** `docs/DOC_DISCIPLINE.md`
- **Repo file map:** `PROJECT_MAP.md`   ·   **Cold start:** `docs/COLD_START_HANDOFF.md`
- **Subagent-audit + code-review method:** `docs/AGENT_AUDIT_METHOD.md`
- **Other project (clinical scribe):** `SOVEREIGN_SCRIBE_SALVAGE.md`

## Load order + startup
1. **`AGENTS.md`** (this file) — rules, working limits, the librarian rule, commands.
2. **`CLAUDE.md`** — only if you are Claude Code (Claude-specific notes).
3. **`STATUS.md`** — current state / next step. CANONICAL if anything conflicts.
4. **`docs/COLD_START_HANDOFF.md`** — fresh-session orientation.

Before any write/delete/install/send: read `SECURITY_AND_TOOL_POLICY.md`. At
startup: emit a load trace using `LOAD_TRACE_TEMPLATE.md`. Then STOP and tell
Scott, in one sentence each: (a) the operator rules you'll hold, (b) current
project state, (c) the next step. Then ask where to start. Do not start work
until he says.

## Scope
This repo only. Don't rebuild the old `pharmacy_tool_v13` (reference lumber).
