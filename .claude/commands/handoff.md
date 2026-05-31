---
description: End-of-session handoff — update STATUS.md and log what changed so the next (memory-less) Claude inherits it
---

Write the handoff so a FRESH Claude instance (zero memory of this session) can
continue without loss. Do ALL THREE:

1. **Append a `JOURNAL.md` entry (newest on top)** capturing the NARRATIVE of the
   session — this is the part that makes invisible backend work visible:
   - Where I worked (phone / computer, rough %).
   - What I set out to do vs what it became.
   - **What I learned and HOW I found it out** (the dead ends, the question that
     unlocked it — the reasoning, not just the result).
   - **WHY** key decisions were made (the trade-offs).
   - What got hard / frustrating (name it honestly).
   - What I built (CONFIRMED vs ASSISTANT-SIDE), and what's next.
   Keep the voice plain and real. The struggle IS the deliverable here.

2. **Update `STATUS.md`** — current state, open loops, the single next step.
   Accurate: no stale claims, real counts, correct evidence levels.

3. **Log durable changes** — new behavior rule → `CLAUDE.md`; "what happened" →
   STATUS open loops. Don't let an improvement live only in chat — it dies at
   session end. State access/build status plainly (pushed? blocked? PR open?).

Keep STATUS + CLAUDE tight; let JOURNAL be the longer narrative.

Extra notes to capture: $ARGUMENTS
