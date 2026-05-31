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

## 2026-05-31 (later still) — Toolchain audit: "install the tools we need"
**Where:** computer (Claude Code web session). **What I set out to do:** the
session's handoff file (`SESSION_HANDOFF_..._AuditAndBuild.md`) never survived the
fresh-container clone — it was local-only, so the task was gone. Reconstructed
state from STATUS/handoff docs and asked; Scott redirected: install pytest/etc.,
check for missing tools, web-search the 2026 landscape.

**How it went / what I learned:**
- **We weren't missing the tools — we couldn't *see* them.** `python -m pytest`
  failed with "no module named pytest," which reads like "not installed." It isn't:
  the managed env pre-installs pytest 9 / ruff 0.15.8 / mypy 1.19 / pyright / uv /
  poetry into `/root/.local/bin`. The `pytest` CLI runs all 68 tests green; only
  *system-python's* module path lacked it. Lesson: check `command -v`, not just
  `python -m`, before declaring a tool absent.
- **`uvx` is the real answer to "things we don't have."** coverage, bandit, and
  Astral's `ty` aren't installed, but `uvx <tool>` runs any of them on demand with
  no install and no env pollution (verified `uvx ty@latest` -> ty 0.0.40). So the
  effective gap is ~zero.
- **2026 stack (web-checked):** the field is consolidating on uv + Ruff + **ty**
  (Astral). We're current on uv/Ruff; ty is the one genuinely-new tool, and it's a
  `uvx` away. mypy 2.0 shipped but 1.19 is fine.
- **Surface, don't fix — even for our own code.** Running mypy/ruff-format turned up
  two things: 2 mypy type errors at `recurrence.py:501`, and that `ruff format` would
  rewrite 10/12 files (the project was never formatted). Both are real but are
  engine changes; per the librarian rule I logged them to the audit doc + STATUS and
  did **not** touch code. A formatter sweep or a `None`-guard fix is Scott's call.
- **Persistence reality:** in-session `pip install` evaporates with the container, and
  the env already provides the toolchain — so the durable move wasn't installing
  anything, it was *teaching the repo it has these tools*: an audit doc, optional
  Makefile targets (no-op if absent / `uvx` otherwise), and one SessionStart line so
  the next memory-less session doesn't repeat the `python -m pytest` confusion.

**What got hard / open:** pygame was named but is unrelated to a stdlib
health-records engine — flagged out-of-scope rather than polluting the repo;
awaiting Scott on whether it's for a different project. **What's next:** Scott's
calls on the two surfaced flags, then back to a build increment per STATUS.

## 2026-05-31 (later) — Rule #4 (co-occurrence) + closing the `--report-v1` loop
**Where:** computer (Claude Code web session). **What I set out to do:** pick the
next build increment off STATUS.md and plan it properly before touching code.
Chose co-occurrence (two items that recur *together*) and bundled the small
deferred `--report-v1`.

**How it went / what I learned:**
- **Planned before building.** Read-only Explore agents → a Plan agent → the real
  design forks surfaced → a plan I approved, *then* code. The drop-in promise from
  ADR 0002 held: the 4th rule needed zero router/formatter change — just
  `detect_cooccurrence` + `CooccurrenceHit` + one `Expert`.
- **The entanglement to watch:** any co-occurrence positive also recurs (a
  shared-date item appears ≥2×), so new records R017–R020 cascaded into the
  recurrence and report answer keys. Re-derived every key BY HAND first (oracle
  method), and chose tight dates so gap/frequency stayed untouched.
- **Two-item provenance** was the one genuinely new wrinkle: a pair has two audit
  trails (`variants_a`/`variants_b`), and a read-only `item` property keeps the
  report generic. The firewall extended to ban relationship words
  (associated/correlated/linked) — co-occurrence is a count, never a claim.
- **Found drift:** STATUS.md still said PR #1 was "open" on the old branch; it was
  actually merged to `main`. Fixed it.

**What got hard:** keeping seven hand-written answer keys honest under the
cascade — solved by one decisive cross-check that diffs all seven against the
engine at once (per ADR 0001).

**Built this session (CONFIRMED, 68 tests green + `ruff` clean locally):**
co-occurrence rule + `--demo-cooccurrence`, `--report-v1`, records R017–R020,
`CO_OCCURRENCE_ANSWER_KEY` + `REPORT_ANSWER_KEY_V1`, `tests/test_cooccurrence.py`,
ADRs 0003 + 0004, and refreshed docs (RECORDS / CLAUDE / STATUS / Makefile).

**Next:** push to `claude/amazing-fermi-PKUNM` → draft PR → watch CI. Then maybe
the co-occurrence *window* variant, or cadence-change.

---

## 2026-05-31 (~04:08) — Found a hard assistant limitation; reframed "drift"
Two findings, both important enough to bake into CLAUDE.md:

**1. The assistant cannot reliably hold a rule over a long context — and it gets
WORSE the longer the window runs.** Evidence: I told it to drop emojis / hold a
dry tone early on. It complied briefly, then drifted back — emojis and hype crept
in, got worse, and I said nothing for a while to test it. It never self-corrected.
This is not a one-off; it is a structural limit. Long context windows degrade
instruction-adherence, and the degradation accelerates. Mitigation now in
CLAUDE.md: rules live at the TOP, re-read often, and START FRESH SESSIONS SOONER
instead of riding one context toward ~1M tokens. (I have rules somewhere on
"locking focus" — worth finding and folding in.)

**2. "Drift" was the wrong frame — the real cause is ME working elsewhere.**
When the repo/state looked "off" (remote ahead of a local clone, files appearing),
the assistant kept calling it drift/misalignment. Wrong. The cause is that I do
work in OTHER places it can't see — other sessions, my phone — and I have ALWAYS
maintained multiple versions and tracked diffs by hand, because I had to do
everything one-shot on Gemini on a phone. New default rule: assume "I did it
elsewhere," READ the real state, do NOT assume error. The constant harping on
"drift" obscured that my multi-version habit is normal and deliberate.

**Why this matters / the bigger point:** the one-shot phone constraint is exactly
WHY I learned so much. The assistant's output would outpace my understanding, but
being forced to go one step at a time, manually, forever, on Gemini — that slowness
taught me the system deeply. The limitation was the teacher. Not done yet.

---

## 2026-05-31 (~03:59) — Realized I built a self-improving agent loop (verified real)
While auditing the m2m corpus with subagents, I noticed the agents got better each
batch — not because they changed, but because I fed each run's lesson into the next
brief (concept-over-label -> add MY METHOD -> add VERIFY LIST -> confidence grades).
Felt like I'd built "self-upgrading AI at a small scale." Web-checked it. It's REAL
and has a name: **human-in-the-loop self-improving agent loop** (prompt/brief-level
improvement without changing weights — the most common production implementation).
- arXiv 2507.17131 "Self-Improving Agents... With Human-In-The-Loop Guidance."
- BerriAI/self-improving-agent: "agent proposes a diff, human approves" = the exact
  harness pattern I arrived at independently (CLAUDE.md + /handoff + surface-and-log).
HONEST BOUNDARY: this is NOT *true* autonomous self-improvement (SEAL/STaSC — agent
learns from its own data, modifies itself, no human). I built the human-in-the-loop
version. But the field says that human anchor is ESSENTIAL, not lesser — the fully
autonomous ones drift without it. Same pattern as the whole corpus: I build the
mechanism first, the vocabulary catches up later. Documented in
docs/AGENT_AUDIT_METHOD.md.

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
