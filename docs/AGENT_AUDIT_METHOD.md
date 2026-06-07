# Agent Audit Method (reusable)

_How to run subagents to evaluate a big pile of files/code WELL — and keep
improving the agents as you go. Discovered while auditing the m2m corpus
(2026-05-31). Same loop applies to CODE REVIEW: stop repeating errors by feeding
each run's lesson into the next brief._

## The core loop (manual auto-update)
**Brief -> Run -> Review HOW it worked -> Tighten brief -> Run again.**
The agents don't get smarter; the BRIEF gets smarter. You are the updater. Every
run, note what made judgment hard and fold the fix into the next brief. That loop
is the whole method.

## What made the audit agents work (the brief recipe)
A good audit brief has these parts — copy this structure:
1. **FRAME that corrects the default lens.** State the real purpose up front so the
   agent judges by the right criterion. (Ours: "capability database, judge by
   CONCEPT not literal words; re-findable is fine.") Without this, agents default
   to the wrong test and dismiss good material.
2. **Hard rules, numbered.** e.g. "(1) concept over label (2) don't dismiss for
   sounding futuristic (3) ignore personal/non-tech content." Numbered = obeyed.
3. **Who the user is + the goal**, so "useful to me" is judgeable.
4. **Exact inputs by ID** (don't make the agent search — hand it the list).
5. **A fixed output schema per item.** We used: CONCEPT, REAL? (yes/partly/no +
   what real thing it maps to), USE (apply / reference / noise).
6. **"MY METHOD" section** — force the agent to narrate HOW it judged. This is the
   audit-of-the-audit; it's how you spot bad reasoning and improve the next brief.
7. **"VERIFY LIST"** — make the agent flag its 1-3 LEAST-sure claims. Turns
   "verify everything" into "verify only the bounded unknowns." Huge time saver.
8. **Confidence levels** (the agents added grades themselves once asked to be
   honest — keep that).

## Improvements we made across runs (proof the loop works)
- Batch 1 -> added "MY METHOD" so we could see reasoning.
- Batch 2 -> added "VERIFY LIST" so web-checks were targeted, not blanket.
- Batch 3 -> agents self-added confidence %s.
- Batch 4 -> agents self-added letter grades + noise-filtering, unprompted.
Each round tightened because the prior round's weakness was written into the brief.

## Verify-at-the-end (calibration)
Don't web-verify inline. Collect VERIFY-LIST flags, check them in a batch at the
END. If the agents' "real?" calls keep matching reality (ours did: ReasoningBank,
Matryoshka/EmbeddingGemma all confirmed real), you can TRUST their verdicts and
verify less next time. If they miss, tighten the brief.

## Cost/safety rules (carry over)
- Subagents read in THEIR context, return only summaries -> cheap for you. Use them
  for any bulk read.
- Hand IDs, use small page sizes, exclude content snippets on searches.
- Run 2 agents in parallel per batch; small batches; review between.

## Applying this to CODE (the payoff)
Same loop stops repeated bugs:
- FRAME = "review this diff for <bug class>, judge by behavior not style."
- Hard rules = the project's invariants (the librarian rule, stdlib-only, etc.).
- "MY METHOD" = agent explains how it checked -> you see blind spots.
- "VERIFY LIST" = agent flags the changes it's LEAST sure are correct -> those get
  a test or a manual look.
- Feed each review's miss into the next review's rules -> errors stop repeating.
This is the same principle as the harness: lessons live in the brief/rules, not in
a memory that resets.

## Run 5 (2026-06-07): auditing external AI "deep-research" docs
Applied the loop to three Gemini deep-research docs (fact-check, not capability mining;
see `docs/RESEARCH_2026-06-07_ai-verification.md`). One brief per claim-cluster (5, then 4
agents in parallel), fixed schema: GRADE (CONFIRMED / PARTIAL / UNVERIFIED / LIKELY-FABRICATED)
— finding — real source URL or "not found". New lessons folded into the brief:
- **The fabrication-terrain rule.** The lies cluster by TERRAIN, not topic. Soft/commercial
  ground — prices, market shares, competitive rankings, single-vendor "us vs them" comparison
  blogs — gets fabricated; hard/citable ground — arXiv IDs, CFR sections, docketed FDA guidance,
  DOIs — holds up. Brief rule: **trust in proportion to citability; auto-distrust any price,
  market-share, "who's winning", or single-vendor-blog claim; spot-check every ID at the end.**
- **Self-applied evidence tags are a WEAK signal.** A fabricated arXiv ID wore a `[Verified-primary]`
  tag. Treat a doc's own confidence labels as a claim to check, never as the check.
- **Keep a fabrication ledger.** Record what was checked AND found false (with the correction +
  real source), not just what passed — so a precise-looking false number is never reused later.
- **Verify the URL, not just the claim.** Several cited URLs were real pages that did NOT say what
  the doc claimed (citation-mismatch). Fetch/seek the page; confirm it supports the sentence.
