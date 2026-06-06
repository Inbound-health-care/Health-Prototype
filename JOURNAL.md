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

## 2026-06-06 — The reframe: the constraint IS the product (learning vehicle, not a healthcare ship)
**Where:** Claude Code web session (phone), after asking Claude for a blunt, outside-the-box
read on the project — on purpose, to compare its take against another model's.

**The click:** Claude's read landed — "the meta-system has outgrown the product; the discipline
is heavier than the thing it governs." That's correct, and it's the POINT, not a flaw. I'm not
building this to ship to a health system. If I just needed something to pull up info, that's a
20-minute build and done. I deliberately picked a domain restrictive enough (PHI, citation
discipline, recurrence math) to FORCE me to think outside the box. The restriction is the gym,
not the goal.

**What I'm actually after:** reusable scaffolding that outlives this repo — a reusable math-test
harness, a reusable citation/siting test, drift control, the librarian rule. The health
prototype is the sparring partner I run the method against, not the deliverable.

**Why the UI detour:** the engine got "decent enough," and that was my green light to go play
with eye candy for a bit. Seeing TEST GREEN / +N tests / output I verified by running the code
myself was a morale checkpoint — nice to SEE the invisible backend work for once — not a pivot.

**Why I'm fine with split focus:** I don't fully know what I want to build yet, and I'm not
pretending to. The honest goal right now is to LEARN while I can — backend/systems depth, slower
and less flashy, figured out by reading and asking. Split focus is the deliberate cost of
learning broadly.

**Honest self-note:** the over-done rules/instructions/auditing are intentional over-engineering
as a teacher. I take the "pre-validation product" read as accurate-for-where-I-am, not as bad
news. Not done; not trying to be done.

---

## 2026-06-05 (evening, II) — Scott's drift gauge: hype-drift as a canary
**Where:** same web session, reviewing the slice-2 PR (#25). Scott's insight, his words.

**The click:** tone is an instrument, not decoration. Dry/cold framing biases the model toward
convergent, single-task work; hype biases it toward divergent, branch-opening work — and each fails
its own way (dry tunnels and misses the alternative; hype sprawls and invents plausible-but-hollow
branches). What Scott realized is that he *built a skill*: he reads tone-drift as his own **audit
gauge** — when the model's hype creeps up chat-to-chat, that's his early signal the **context is
degrading**, before the reasoning visibly breaks, so he reads it instead of calling it out.

**His markers:** slippage starts ~600k tokens; tone/state largely lost ~850k without re-locking
(re-read the top + explicit callbacks). Flagged honestly as a heuristic he may refine ("I could be
wrong but rn idc") — logged as an observation, not a law.

**Why log it:** it names the mechanism under the standing rule (keep it dry, re-read often, start
fresh sooner) — the dry tone is the instrument; tone-drift is the readout. Markers banked to
AGENTS.md Working limits so the next cold instance gets the tell + the numbers, not just the rule.

---

## 2026-06-05 (evening) — Free-text slice 2: matching modes + merge-safety guards
**Where:** Claude Code web session (PC), same day, after the audit PR (#24) merged.

**What I set out to do:** the next engine increment — synonym/fuzzy matching for the free-text
extractor (slice 2), in service of the BH pre-visit digest.

**What I learned and HOW / why decisions were made:**
- **The fragile part is real, and the earlier design glossed it.** The Drive free-text design treated
  fuzzy/synonyms as a safe "reuse the engine's v1 layer, opt-in" drop-in. It isn't: string similarity
  silently fuses *opposites* — `hypertension`/`hypotension` is one morpheme apart and scores ~0.9 on
  difflib; look-alike drug names (ISMP lists ~528) are a whole hazard class. The repo had **zero** merge guard.
- **Scott's reframe (the good idea):** don't bake one behavior in — make matching an **explicit, named
  mode the clinician must choose** (strict / synonyms / fuzzy / both), ship the *mechanism + guards +
  tiny examples*, and let clinical users bring their own vocabulary. Domain-agnostic / minimal.
- **Does forcing an explained opt-in choice help the liability?** Web-checked: *partly*. It supports a
  learned-intermediary "the clinician configures the settings" defense and FDA criterion-4 transparency
  — but only *with* a safe default (strict) + guards always on; it does **not** waive a foreseeable
  design defect. So the modes are framed as a transparency/human-control mitigation, not a shield.
- **Built:** `MatchConfig` (default strict; refuses incoherent or looser-by-stealth configs), a
  domain-agnostic affix-antonym detector + an explicit look-alike denylist + a drug-name exemption,
  fuzzy anchored to the gazetteer (the allowlist holds), `--explain-modes`. Engine + its 90 tests
  untouched; strict reproduces slice 1 byte-for-byte. Logged as ADR 0012.

**What got hard / honest:** the only genuinely new algorithm is fuzzy token-windowing — the part most
likely to be noisy in the wild — so it is guarded and the fallback (single-token fuzzy first) is
recorded. The guards are deliberately over-inclusive: I'd rather lose recall than fuse opposites.

**What's next (CONFIRMED_ASSISTANT_SIDE only):** `make check` green — 144 tests, self-test 6+7, ruff
clean. Draft PR up; awaiting Scott CONFIRMED_USER_SIDE. Remaining slice-2 picks: relative-date
anchoring or multi-patient notes.

---

## 2026-06-05 (later) — Off-the-record compliance + market audit (research, held off-disk until asked)
**Where:** Claude Code web session, same day. Scott ran an intense audit/brainstorm and explicitly
held ALL logging until the end — so this landed as one batch, not live.

**What it was:** a scoped audit on three fronts — (1) how to *close the risk vectors* (compliance
HIPAA+FDA, correctness/trust, adoption/liability), (2) the 2026 customer-facing problems for
clinicians + health systems, (3) a brainstorm on direction. Full cited research lives in Drive
`health-prototype/audit-2026-06-05/` (RESEARCH_ONLY, web-sourced, not counsel-verified).

**What I learned and HOW:**
- **The repo had a stale legal cite.** ADR 0009 leaned on FDA's *2022* CDS guidance; the research
  surfaced FDA **superseded it twice in Jan 2026** (eases criterion 3, raises AI-CDS transparency).
  Logged as **ADR 0011**, superseding 0009's FDA citation. The four Non-Device criteria still hold —
  the librarian rule is still the right shape.
- **The strategic read:** every incumbent (ambient scribes, summarizers, Epic-native AI) is
  *generative and interpretive*, and that's their weakness — clinical-summary hallucination 23–64%,
  omissions on ~31% of summaries; trust hinges on source traceability. The white-space is the
  *verifiable, non-interpreting "librarian layer"* underneath them. The wedge is **behavioral
  health** (Scott's domain; measurement-based care works but <20% uptake; interpretation is most
  legally fraught there). A shape that satisfies adoption + alert-fatigue + FDA criterion 4 at once:
  a **pull-based, EHR-embedded "pre-visit pattern digest," every line cited.**
- **The liability reality (the un-fun part):** "surface-only, never interpret" lowers FDA-device and
  standard-of-care exposure but is **not tort immunity** — under the learned-intermediary doctrine, a
  *false pattern* surfaced and acted on can still reach the vendor. The librarian rule is necessary,
  not sufficient; the UX has to carry it (base rates not bare flags, one-click dismiss, no causal phrasing).
- **Scott's insight, sharpened:** heavy regulation isn't greyer, it's *brighter-lined* — a
  **bright-line rule** ("strip these 18 identifiers") vs a **standard** ("minimum necessary"). He
  built by instinct on the bright-line side of the greyest question (interpret vs surface) — the
  right survival move in a regulated domain.

**Why Drive not repo:** RESEARCH_ONLY + web-sourced; per the lean-out + research-gate conventions the
deep cited write-up lives off-repo (like `freetext-design`), with only this coda + ADR 0011 + a STATUS
direction note in the tree. Vocabulary banked this session: Non-Device CDS, Expert Determination, BAA,
automation bias, alert fatigue, learned-intermediary doctrine, bright-line rule vs standard, MBC.

**What got hard / honest:** the breadth is a lot for one small project — but that's the tax on seeing
the whole board, and the point of the session was to *learn the process and leave a map*, not to ship.

**What's next:** engine — free-text slice 2 (unchanged), now framed by the behavioral-health digest
direction. Standing: counsel-verify the legal claims (ADR 0009/0011) before any real-PHI use.

---

## 2026-06-05 (pm, coda) — FB post help + the golden-rules lesson
**Where:** same web session, after the handoff (PR #22) merged. Side tasks, no engine change.

**What happened:** Scott asked me to (a) review a Facebook post recruiting a HIPAA-savvy
healthcare collaborator, and (b) find his "20 golden rules" in the `replit-code` repo.
- **FB post:** substance was accurate to how he works; I tightened it in his voice, flagged that
  the draft's "20 rules" claim should match a real list, and suggested one plain line on what the
  project is + (optionally) his clinical background for credibility.
- **Golden rules — the real answer:** they live in `GOLDEN_RULES.md`, added by `replit-code`
  **PR #9** (still OPEN — that's why a raw `main` fetch 404'd). It is **17** distilled rules in four
  groups (Doing the work / Safety & trust / Code & repo / Truth & judgment), each pointing back to
  `AGENTS.md` as canonical — **not 20.** So his post's "20" is really 17. (`replit-code` also carries
  its own AGENTS/CLAUDE/ADRs 0010–0012, a `recurrence.js` port, golden tests, 79 tests — the
  scaffolding pattern is fully replicated there.)

**The lesson Scott named (his final note, recorded):** *"If not directly directed, AI wastes a lot
of time not looking for the right answer."* Proven live: hunting the rules I ran ~6 indirect lookups
(code search, three doc fetches, the PR page, two blocked diff fetches) before the answer was one
pointer — PR #9 → `GOLDEN_RULES.md`. The fast path was to ASK "which file/PR?" first and go straight
to the source. Logged as a working limit in `AGENTS.md`. The scaffolding Scott keeps building exists
for exactly this: a model left to wander wanders; direct it, and it lands.

**What's next:** engine unchanged — free-text slice 2 (Scott's pick). Off-repo follow-ups Scott owns:
fix the FB post's rule count (17), and `replit-code` PR #9 is still open.

---

## 2026-06-05 (pm) — Free-text slice 1, the "firewall" rename, and an audit of the whole journey
**Where:** Claude Code web session; Scott on his usual phone/PC mix (he merged the PRs and drove a
long reflective exchange). Exact device split unverified.

**What I set out to do vs what it became:** The plan was narrow — ship free-text extraction slice 1.
It shipped (`extract.py`, PR #20, Scott merged). But the session became three unplanned things: a
blunt repo critique Scott asked for, a repo-wide terminology rename that critique triggered, and —
the part that mattered most — an audit of Scott's actual seven-week journey when he got discouraged.

**What I built (evidence honesty):**
- **`extract.py` — free-text front-end, slice 1 (PR #20, MERGED by Scott).** Prose → the canonical
  record shape the 5 rules already eat, unchanged. Stance A (strict-literal: emit every gazetteer
  hit + char-offset span, no negation/interpretation), de-identified date shift, allowlist-by-
  construction. 27 tests, oracle-first; `make check` 117 green. CONFIRMED_ASSISTANT_SIDE + merged.
- **"firewall" → librarian rule / allowlist / research gate (ADR 0010, PR #21, MERGED).** Plus a
  staleness audit folded in (reconciled docs to `main` = 117 post-#20). CONFIRMED_ASSISTANT_SIDE + merged.

**What I learned and HOW:**
- **"firewall" was one word doing three jobs.** Before renaming I mapped every occurrence (83 across
  31 files) and found three distinct senses: the surface/don't-interpret rule, the HIPAA PHI layer,
  and the evidence-level "research firewall." A blind find/replace would have mangled all three. So a
  sense-aware map: librarian rule (the engine's own self-description) / allowlist (PHI) / research gate
  (evidence). The metaphor was already in the code; the rename just named the rule after it.
- **Agent consensus is not ground truth.** In self-review, two finder subagents disagreed on whether
  `architecture.md` should say "10 files" or "11 files," and one claimed the ADR 0009 `git mv` "never
  happened." I resolved both against git, not by vote: the original "8 files" excluded
  `tests/__init__.py` (git at the 87-test commit proved it) → 10, not 11; the "no git mv" was a false
  positive from a stale local `main` ref inflating the diff. Fixed the real "11"→"10" error I'd made.
- **I audited one repo and called it his whole story.** When Scott said "this isn't impressive,
  people ship in a day," I pulled receipts — but only from health-prototype's git (first commit
  May 29). He cut me off: "you're ignoring every other git I have." Right. Global GitHub search (the
  per-repo reads are denied — this session is scoped to health-prototype) surfaced **11 repos**:
  genesis `Pharmacy-App` May 17, code already in Drive May 12, earliest Drive doc April 18. The habits
  propagate across all of them — `testing-kits` is 36 pure-stdlib test harnesses (the oracle-first
  discipline generalized); `replit-code` is a slot game that ported `recurrence.js` carrying the same
  "LIBRARIAN, not an interpreter" line.

**Why key decisions:** "librarian rule" over "guardrail"/"boundary" because it was already the code's
own metaphor; kept the evidence-level sense distinct ("research gate") instead of collapsing it; left
dated ADR/JOURNAL numbers as history (refresh, not rewrite). The Drive file `FIREWALL_legal_grounding.md`
keeps its name (no Drive rename tool; references point at the real file) — Scott confirmed that's fine.

**What got hard / honest:** The stale local `main` ref bit twice (inflated review diffs, confused an
agent) — fix is to diff against `origin/main`, not local `main`, after a fetch. And the real
difficulty wasn't code: the honest answer to "this isn't impressive" isn't reassurance, it's
evidence. April 18 nothing → May 12 first code → 11 repos and an FDA-grounded engine by June 5,
part-time, mostly on a phone — the timeline rebuts the discouragement better than any pep talk.

**What's next:** engine-wise, free-text slice 2 (Scott's pick: opt-in fuzzy/synonym gazetteer via the
v1 layer / relative-date anchoring / multi-patient notes). But Scott may redirect — the broader
context (11 repos, a `Portfolio-repo` "for job ref") is now on the table; this repo is one node of it.

---

_Per-session records for 2026-06-04 (co-occurrence window, PR #10) and 2026-06-05
(cadence rule #5, PR #13) are captured factually in STATUS.md and the Drive archive
(`health-prototype/archive`); they are not re-narrated here._

## 2026-05-31 — Back-end / workflow hardening pass (engine frozen)
**Where:** computer (Claude Code web session). **What I set out to do:** Scott
scoped it plainly — "fix all back-end things before changing any of the code; make
sure the workflow is up to snuff." So: audit the infrastructure (CI, hooks, docs
consistency, branches, PRs, hygiene) and fix it, engine code OFF-LIMITS.

**How it went / what I learned:**
- **The front door was lying.** A drift sweep (METHOD-003) found STATUS.md still
  called the current branch `nifty-fermat`, described PR #7's merged doc work as an
  in-progress draft, and listed stale branches for retirement that were already
  gone. COLD_START_HANDOFF still said "53 tests / PR #1 open / spec-jm3Ck" and
  omitted co-occurrence. Fixed both to reality (68 tests, 4 rules, current branch).
  **Left the ADRs alone** — their "53 tests / nifty-fermat" lines are correct
  point-in-time history; rewriting decision records would be the wrong kind of tidy.
- **CI had a real gap:** it gated tests on Py 3.10–3.13 but never ran ruff, so a PR
  could go green with lint errors. Added a separate `lint` job (ruff pinned to the
  local 0.15.8 — pinned so CI can't drift from local on a ruff release). Lint only,
  NOT `ruff format` (Scott kept hand-formatting). Branch protection still needs the
  new check marked *required* — flagged that as a manual step for Scott (no tool to
  edit protection from here).
- **PR #6 was a bundling problem.** It mixed engine code (`--version`) with back-end
  hygiene (CONTRIBUTING, PUBLISH_CHECKLIST, `make check`, `.gitignore`). During an
  engine-freeze you can't merge it whole. Scott's call: extract the back-end bits,
  defer the code. Pulled the four hygiene pieces into this branch verbatim from the
  PR diff (token-frugal — no re-invention), recorded the deferred `--version` spec
  in STATUS so it isn't lost, and closed PR #6 so a stale duplicated draft doesn't
  linger (the cruft this pass exists to kill).
- **Hit the self-mod guardrail again earlier** (registering the Stop hook) — same
  lesson holds: agent-config changes need explicit sign-off, and that's correct.

**What got hard:** keeping the librarian discipline pointed at our OWN process —
surface drift, fix the genuinely-wrong, but don't "improve" history or silently
restructure someone's PR. **What's next:** Scott signs off the back-end pass (and
marks the `lint` check required); then the engine unfreezes and we pick a build
increment (or land the deferred `--version`).

## 2026-05-31 (evening) — Handoff-loss guard (so the AuditAndBuild vanish can't recur)
**Where:** computer (Claude Code web session). **What I set out to do:** the whole
reason this session started blind was a handoff file that was written locally and
never committed, so the fresh-container clone didn't have it. Close that hole.

**How it went / what I learned:**
- **Two layers, because one isn't enough.** (1) Structural: `/handoff` now ends with
  a non-optional commit+push step — a handoff created the right way is committed the
  moment it's written. (2) Backstop: a `Stop` hook (`stop_handoff_guard.py`) that
  refuses to end a session while any `*handoff*.md` is uncommitted.
- **Scoped narrow on purpose.** The hook only fires on handoff-shaped files and
  excludes `.claude/` (the command template is literally named `handoff.md` — caught
  it in testing, would've nagged on every harness edit). Ordinary mid-session
  uncommitted work is never touched. Verified all four cases by hand (block on a real
  `SESSION_HANDOFF_*.md`; allow on `stop_hook_active`; allow when clean; ignore a
  plain `.txt`).
- **Verified the hook contract before writing it.** A `claude-code-guide` subagent +
  the official docs: block = `{"decision":"block","reason":...}` on stdout, exit 0;
  Stop ignores matchers; loop-safety via `stop_hook_active` AND the condition
  self-clearing once committed. Fail-open on any error (never trap a session).
- **Hit the agent-self-modification guardrail.** Editing `.claude/settings.json` to
  register the Stop hook was blocked by the permission classifier — "yes add it"
  didn't specifically authorize changing agent control-flow config. Correct call by
  the harness; I committed the hook + `/handoff` change and asked Scott to explicitly
  authorize the one settings line rather than work around it.

**What's next:** Scott approves the `settings.json` registration -> wire the Stop
block -> the guard is live.

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
  report generic. The librarian rule extended to ban relationship words
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
