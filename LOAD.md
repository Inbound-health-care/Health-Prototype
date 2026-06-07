# LOAD — entry point

_Trigger: when Scott says "load repo settings" (or similar), read THIS file first,
then branch out in the order below. This is the single front door so the
Instructions field can stay tiny._

## Step 1 — read these, in order
1. `AGENTS.md` — SOURCE OF TRUTH: operator rules, working limits, the librarian rule, commands.
2. `CLAUDE.md` — Claude-Code-specific notes (Claude only; points back to AGENTS.md).
3. `STATUS.md` — where am I / next step. CANONICAL if anything conflicts.
4. `docs/COLD_START_HANDOFF.md` — fresh-session orientation.
Before any write/delete/install/send this session, read `SECURITY_AND_TOOL_POLICY.md`.
At startup, emit a load trace using `LOAD_TRACE_TEMPLATE.md`.
Then STOP and tell Scott, in one sentence each: (a) the operator rules you'll
hold, (b) current project state, (c) the next step. Then ask where to start.
Do not start work until he says.

## Step 2 — load MORE only when the task needs it (don't front-load)
- Decisions / "why was X done" -> `docs/adr/`
- Narrative / lessons / limitations -> `JOURNAL.md` (ARCHIVED 2026-06-07 — historical only; the diary is chat-only now, see ADR 0024)
- Full prior-session detail (handoffs + session log) -> Drive: `health-prototype/archive` (off-repo)
- How to run subagent audits / code review -> `docs/AGENT_AUDIT_METHOD.md`
- Tooling / token-frugal patterns -> `docs/TOOLS_CHEAT_SHEET.md`
- The other project (clinical scribe) -> `SOVEREIGN_SCRIBE_SALVAGE.md`
- Data field meanings -> `data/RECORDS.md`
- Security / tool-use / PHI / source-conflict policy -> `SECURITY_AND_TOOL_POLICY.md`
- File map (what's where / what's canonical) -> `PROJECT_MAP.md`
Pull these on demand. Do not read everything up front (wastes context).

## Step 3 — long-context self-check (THE IMPORTANT ONE)
You degrade as the window grows (see AGENTS.md "Working limits"). So:
- Re-read AGENTS.md "Operator rules" before any big step, and any time you are
  unsure of tone/scope. If you notice yourself adding emojis/hype, you have
  already drifted — re-read and correct.
- When the session feels long OR you are about to do something complex, SAY:
  "Context is getting long — want me to re-load LOAD.md / start fresh?" Offer it;
  let Scott decide. Do not silently push through degraded.
- Before claiming done/pushed: verify against the real remote state, not memory.
- If state looks off: assume Scott worked elsewhere; READ state; do not call it
  "drift."

## One-line contract
Trigger -> read 3 files -> report 3 things -> ask. Branch out only as needed.
Watch your own context length and flag it.
