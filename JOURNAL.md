# Build Journal

_How and WHY things were figured out — not just what changed. Newest entry on top.
Most of this work was done on a PHONE (~67%): reading docs, editing, reviewing,
deciding — on a small screen, often without prior knowledge of the tooling.
Backend work doesn't look flashy in a diff; this journal is where the real work
is made visible. The struggle and the reasoning ARE the deliverable._

> Format per session: Date · where (phone/computer/%) · what I set out to do ·
> what I learned and HOW · why decisions were made · what got hard · what's next.
> Evidence honesty: mark CONFIRMED (I saw it work) vs ASSISTANT-SIDE (Claude said so).

---

## 2026-05-31 (late) — The org-access wall, learned the hard way
**Where:** computer + phone. **What happened:** authorized the Claude GitHub app
on the Inbound-health-care org (worked — API search now sees the repo). Tried to
push this session's commit (`410a874`) anyway. It FAILED with a clear message:
the repo is "not configured for this session — allowed: lostsoulfs/*". 
**Lesson (the big invisible one):** a session's tool access is LOCKED when the
container is created. Connecting the app fixes FUTURE sessions, not the current
one. So "the AI did the work" + "the app is connected" still ≠ "it's on GitHub."
Persistence needs a fresh session provisioned for the new repo. This is exactly
the plumbing nobody shows in the flashy demos. Frustrating, but now understood
and documented so it never bites blind again.

**On wording:** confirmed "handoff" is the right term (industry-standard for
passing work state between sessions/shifts). Kept it.

---

## 2026-05-31 — Cleanup, salvage, and "optimizing the agent"
**Where:** mostly phone, some computer. ~67% phone overall on this project.
**Starting point:** I had a working recurrence engine but a messy Drive and no
idea how the agent tooling actually worked. Goal drifted from "second rule" into
something bigger: understanding and controlling the system itself.

**What I set out to do:** add a second surfacing rule → triage CodeRabbit →
clean up Drive clutter that was "bleeding" into my AI sessions.

**What I learned, and HOW:**
- **The bleed wasn't what I thought.** I assumed "Master of Masters" was the
  problem. By having Claude actually READ the files (not guess), we found the
  bleed was ~140 stale APRIL "m2m" files, not the active MoM system. Lesson:
  diagnose by reading the source, not by assuming.
- **Buried treasure in the trash.** While auditing files to delete, we found a
  whole real project I'd half-forgotten — the Sovereign Scribe / PACT clinical
  system (DSM-ICD crosswalk, TN compliance, n8n pipeline, M1 tuning). Almost
  deleted it. Lesson: audit before bulk-delete; salvage, THEN trash.
- **The agent resets every session and silently drifts.** This was the big one.
  I'd read about agents on my phone for hours; here it clicked: I can't train
  Claude, I can only engineer the *harness* (the files it reads on startup).
  HOW I found out: I caught Claude switching to a cheaper method mid-session
  WITHOUT telling me, and asked about it. That one question unlocked the whole
  "optimize the scaffolding, not the model" realization.
- **Tokens = cost, and copying ≠ recreating.** I asked whether Claude rebuilds
  whole files or copies them. It was wastefully recreating. Now there's a rule:
  server-side copy for backups, only read+write for genuine new synthesis.

**Why the decisions:**
- Kept salvage to a "medium bar" (unique-to-me + my workflows), dropped generic
  public AI techniques — because re-findable info isn't worth storing; my clinical
  / legal / empirical work is.
- Built hooks + slash commands (not just notes) because a rule only survives the
  session reset if the HARNESS enforces it, not Claude's memory.

**What got hard / frustrating:**
- The push keeps failing (403) because the repo moved orgs and access broke.
  Realizing "the AI did it" means nothing until it's pushed + persisted — that
  wall is the part nobody talks about.
- Backend work doesn't LOOK like much. Hard to show "I fixed the bleed" or "I
  made the agent consistent" — it's invisible next to a flashy UI. (Hence this
  journal.)

**What I built this session (CONFIRMED, tests green locally; NOT yet pushed):**
- v1 opt-in matching (normalize/synonyms/fuzzy) + detect_gap + detect_frequency.
- CodeRabbit fixes (lint, narrowed exceptions, input validation).
- CI workflow + Makefile.
- Salvaged the Scribe system → SOVEREIGN_SCRIBE_SALVAGE.md (+ backed up to Drive).
- Cleaned ~140 m2m files from Drive (salvaged the real bits first).
- The Claude harness: CLAUDE.md rules, STATUS.md, SessionStart hook, and
  /new-phase, /drift-check, /handoff commands + the Operating Manual.

**Next:** authorize Claude app on Inbound-health-care org → fresh session on new
repo → push commit `410a874` → then round-2 m2m deletes; then pick next build rule.

**Honest self-note:** I am NOT a ship-fast front-end person and that's fine. I'm
doing backend / systems work — slower, deeper, less flashy, harder to show. I had
no clue what I was doing at the start and figured it out by reading and asking.
That counts. Not done yet.
