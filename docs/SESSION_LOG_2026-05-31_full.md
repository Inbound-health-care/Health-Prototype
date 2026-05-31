# Full Session Log — 2026-05-31

_Complete audit of one (very long) working session, written with the doc strategy
we settled on: capture the WHY not just the what; consolidate; mark superseded
rather than delete; keep it in-repo and versioned. This is the canonical record
of what happened, what was decided, and what's still open._

## Arc of the session (chronological)
1. **Built the recurrence engine** (health-prototype): v0 `detect_recurrence`,
   then v1 opt-in matching (normalize/synonyms/fuzzy), then `detect_gap` +
   `detect_frequency`. 37 tests green. Firewall held: surface/count/cite, never
   interpret. PR #1 opened.
2. **CI + CodeRabbit triage**: GitHub Actions gate, Makefile; applied the good
   review fixes, skipped noise, closed stale auto-PR #2.
3. **Branch-protection saga**: wanted max gating -> hit the private-repo-free-plan
   wall -> upgraded to Team -> repo moved to `Inbound-health-care` org -> that BROKE
   tool/push access (locked to old `lostsoulfs/*`). Recurring blocker all session.
4. **Clinical "caution" question (Alisha)**: engine may surface "3x in 4 weeks +
   dates" but must NEVER label it "caution" — human/policy supplies judgment.
5. **Drive cleanup**: found the "bleed" was ~140 stale APRIL m2m files, not the
   active Master-of-Masters RAG. Salvaged a buried real project (Sovereign Scribe
   / PACT) before trashing. Then RESTORED everything when we realized more was
   valuable than first judged.
6. **Built the Claude harness** (the persistence layer): CLAUDE.md, STATUS.md,
   SessionStart hook, slash commands (/new-phase, /drift-check, /handoff,
   /audit-prompt), Operating Manual, Tools Cheat Sheet, Doc Discipline, Prompt
   Audit, Agent Audit Method. Plus JOURNAL.md.
7. **Tooling + hardware learning**: where Claude Code runs (web/terminal/desktop/
   IDE/phone-remote-control); connectors vs interfaces; tested local LLMs on the
   PC (RTX 5060, 8GB) — found the VRAM bleed (~6.8GB), confirmed Gemma E4B (7.5B
   params, ~4B effective) is the right model, 9B+ halts. S26 phone local-LLM
   options (PocketPal/MLC, NPU). Decoded the phone sampling-settings screens.
8. **m2m corpus audit** (the big one): ~89 of ~200 April files audited across 5
   batches using subagents. Verdict: high-signal capability database, ~85% sound,
   concepts hold even where Gemini invented the labels. Several clusters feed the
   real build (RAG, prompting, agentic-UX/MCP, distillation/BitNet, clinical).
9. **Meta-realization (verified)**: the agent-audit loop I ran IS a documented
   "human-in-the-loop self-improving agent loop." Built the mechanism before
   knowing the vocab.

## Key DECISIONS (the why)
- **Surface-not-interpret firewall** is non-negotiable across engine AND scribe.
- **Judge research by CONCEPT, not literal words** — Gemini's invented terms map
  to real techniques; re-findable is fine for a capability database.
- **Personal/non-tech content is walled off** — ignore in Claude Code unless
  explicitly raised (personal life was bleeding in too much).
- **Optimize the harness, not the model** — the model resets/drifts; lessons must
  live in files the next session reads.
- **Copy/move, don't recreate** (token frugality); **surface and log approach
  changes** (no silent improvements).
- **Doc strategy**: WHY over what; in-repo + versioned; consolidate; mark
  SUPERSEDED rather than delete; /drift-check is the prune mechanism.

## Standing rules now in CLAUDE.md
Firewall; stdlib-only/local/zero-PHI; exact-match default (new matching opt-in);
validate args (raise); answer-keys-first; web-search before new phase; copy-don't-
recreate; frugal reading; surface+log changes; personal-data wall; read STATUS first.

## Corpus audit — where it landed (resume point)
- Audited ~89/200 April files. Ratio steady every batch: ~70% confirmed real /
  ~20% plausible-frontier / ~10% invented-label-but-real-concept.
- HIGH-VALUE clusters for the build: On-Device RAG (Matryoshka/sqlite-vec,
  CONFIRMED), Continual Learning, ReasoningBank/MaTTS (CONFIRMED), constrained
  decoding/PydanticAI, ColBERT/BGE-M3/Self-RAG, distillation + BitNet, AppFunctions/
  agentic-UX (= MCP shape), privacy enclaves, clinical-doc patterns.
- REFERENCE/NOISE: quantum, humanoid robotics, planetary GPU fabric, DePIN,
  green-compute, music gen.
- Web-verified real: ReasoningBank, MaTTS, Matryoshka/EmbeddingGemma, human-in-loop
  self-improving agents. Method's "real?" calls held up -> can trust + verify less.
- NOT yet audited: version-chains (Master Dataset v1-v8, Gemini Batch 2-11 — do as
  ONE thinking-evolution pass each), Academic Exoskeleton ledger chain, a few
  stragglers. ~110 files remain (many redundant chain versions).
- FLAG: a "Batch 6 integrations" file contained "mental health data extraction
  bypassed" — Scott to review/remove if it holds personal/clinical content.

## OPEN LOOPS (carry to next session)
- [ ] **Restore tool/push access on `Inbound-health-care`** (app authorized; needs
      a session provisioned for the new repo path). Until then everything is
      local-commit + downloads only.
- [ ] **Push the unpushed commits** (engine v1+rules, CI, harness, all docs,
      JOURNAL) — they exist only in the old container + Scott's downloads.
- [ ] Finish corpus audit OR jump to synthesis (one "Capability Reference" doc
      organized by: local-LLM setup / health-AI build / reference).
- [ ] Write the "Local LLM Settings — Master Reference" (per-device, per-mode) —
      the recipe the April research was building toward (never existed as a doc).
- [ ] Round-2 Drive prune of confirmed-dead m2m (after synthesis captures keepers).
- [ ] Pick next build increment (router+registry / combined report / new rule /
      free-text extraction).

## Where everything lives
- Code + harness + all docs: local commits + delivered to Scott's downloads.
  Salvage (Sovereign Scribe + m2m_spec_gate.py) backed up in Drive `_learning/`.
  m2m corpus: restored in Drive.

## ~1M token note
Session is near the context limit / pivot point. This log + STATUS.md + CLAUDE.md +
JOURNAL.md are the handoff surface. A fresh session reads those and is oriented.
