# Research — AI verification, provenance & eval methodology (2026-06-07) — RESEARCH_ONLY

**Status: RESEARCH_ONLY. Untrusted external data.** This records what three Gemini "deep research"
docs claimed and **what survived independent verification**, so the verified parts can inform the
project and the fabricated parts can never be mistaken for truth. Nothing here is project truth
until a test proves it (`DOC_DISCIPLINE.md` §Research gate). The one part that **graduated** to a
real check is the rule-layer property suite — see **ADR 0027**.

## Provenance & method
Three Google-Doc deep-research outputs (Drive), each fact-checked this session with the repo's own
`AGENT_AUDIT_METHOD` pattern — parallel subagents (5, then 4), one per claim-cluster, each grading
CONFIRMED / PARTIAL / UNVERIFIED / LIKELY-FABRICATED with a real source or "not found":
1. "AI Coding Tools: Recent Updates" (`1DyR2n…`)
2. "Generative AI Verification Market Analysis" (`1CMXtm…`)
3. "Verifying AI Systems: A Skeptical Analyst's Report" (`1V0BM8…`)

**Confidence caveat:** the container's egress filter returned HTTP 403 to direct page fetches all
session, so grades rest on **search-result snippets cross-checked across independent sources**, not
full-text reads. Treat every item below as RESEARCH_ONLY pending a primary-source read.

## Inapplicable to THIS engine (the honest first cut)
This engine is **deterministic, pure-stdlib, no-LLM**. Most of the methodology corpus therefore does
not apply, and folding it in would be theater:
- **LLM-as-judge bias, agentic trajectory/outcome eval, quantization/precision differential testing,
  benchmark contamination, OpenTelemetry tracing** — the engine has no model, no agent loop, no
  quantization, no nondeterminism. Nothing to apply them to.
- **Deterministic oracles over LLM judges, fail-closed abstention, "convert prod failures to
  regression tests," the vacuous-green guard** — already the repo's practice (ADR 0016, 0025, 0026;
  `data/sample_records.py` oracle convention). Corroboration, not improvement.
- **The one transferable technique: metamorphic / property-based testing** — applied in ADR 0027.

## Corroborated — verification / eval methodology (doc 3)
All confirmed against real sources (the doc's own arXiv IDs were mostly real; the exceptions are in
the ledger):
- **OpenAI retired SWE-bench Verified** as a frontier metric (~Feb 2026), saying high scores reflect
  benchmark exposure, not real-world ability. (openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
- **METR RCT:** experienced open-source devs were ~**19% slower** with early-2025 AI tools (felt
  faster). (arXiv 2507.09089; metr.org) — note a **Feb-2026 follow-up softened this to ~4%** with a
  wider cohort; the doc omits that.
- **ICSE-2026 partial-test study:** 7.2–8.4% of SWE-bench "solved" patches were functionally broken
  on full suites; 3.8–5.2 pp overestimate. (arXiv 2503.15223)
- **SWE-bench Pro** (Scale AI): models near ~70% on Verified scored ~23% on Pro (that cohort).
  (scale.com/blog/swe-bench-pro)
- **LLM-as-judge biases are real and documented:** verbosity & self-preference (arXiv 2410.21819),
  "Bias in the Loop" (Zhao et al., arXiv 2604.16790), post-decision manipulability (Dutta, arXiv
  2606.05384), bias survey (arXiv 2510.12462).
- **Metamorphic / differential testing frameworks are real:** LLMORPH (2603.23611), BACE (2603.28653),
  POET (2603.19333), DIFFCODEGEN (2605.20473), PrecisionDiff (2604.19790); MT survey (2605.13898),
  MT-for-NLP (2511.02108), topological differential testing (2003.00976), EVT-for-diff-fuzzing
  (2511.02927).
- **Agentic-eval framing checks out:** DeepEval trajectory metrics (deepeval.com); Anthropic warns
  against over-grading step sequences (anthropic.com/engineering/demystifying-evals-for-ai-agents);
  OWASP **LLM06: Excessive Agency** (genai.owasp.org/llm-top-10/). The minimal playbook (deterministic
  oracles first; private held-out baselines; judge with a different model family; component tracing;
  prod-failure → regression test) is sound and is essentially the repo's existing stance.

## Corroborated — regulatory (docs 2 & 3)
Feeds the open counsel loop (`COUNSEL_VERIFICATION_CHECKLIST.md`); a dated corroboration subsection
was added there. Counsel-verify gate unchanged.
- **FDA Jan-2026 CDS guidance** re-confirmed (real; enforcement discretion for a single clinically
  appropriate recommendation; reaches generative AI). Keep the checklist's **Jan 6 → Jan 29 2026**
  supersession nuance. (fda.gov/media/191560/download; orrick.com)
- **HIPAA 45 CFR 164.514** Safe Harbor (18 identifiers) + Expert Determination, and **164.502(b)**
  minimum-necessary — accurately stated; date-shift = **Expert Determination, not Safe Harbor**
  (already the checklist's position). (ecfr.gov)
- **FDA 7-step AI credibility framework** — Jan-2025 *draft* guidance "Considerations for the Use of
  AI to Support Regulatory Decision Making for Drug and Biological Products" (distinct from the CDS
  guidance). (Federal Register 2025/01/07, 2024-31542)
- **JAMA Health Forum recall study:** 950 AI devices through Nov 2024; 60 devices / 182 recalls;
  ~43.4% within the first year; 510(k) validation gap. (DOI 10.1001/jamahealthforum.2025.3172)
- **Joint Commission + CHAI "RUAIH"** guidance (Sept 17 2025): local-data validation + blinded
  safety-event reporting. (chai.org) **HTI-1** predictive-CDS transparency (ONC/ASTP, finalized Dec
  2023). **CHAI Applied Model Card** (github.com/coalition-for-health-ai/mc-schema).
- **WA My Health My Data Act** (RCW 19.373) — real, expands beyond HIPAA. **Membership Inference
  Attacks** — real attack class (arXiv 1610.05820).

## Strategy — the bear case (RESEARCH_ONLY; roadmap stays Scott's call)
Doc 2's steelman against the project's own ADR-0011 thesis (a standalone surface-and-cite layer):
1. **Absorption** — verification trends toward a *feature*, not a platform (Snowflake's TruEra
   integration; Abridge built its "Linked Evidence" citing in-house rather than buying an auditor).
2. **Regulatory deflation** — the FDA's 2026 leniency lowers the forcing function for a separate
   audit layer.
3. **Willingness-to-pay-for-friction** — buyers resist paying for a tool whose job is to restrict the
   productivity tool they just bought.
Worth keeping as the disconfirming view; it does not change any code decision here.

## Fabrication ledger (checked → false/garbled — do NOT reuse)
The residue of the same failure mode the project keeps catching: **confident precision on soft
ground.**
- **arXiv `2605.19999`** ("45% contamination overlap") — ID returns nothing; the real paper is
  **2505.08389**; the 45% traces to a different survey. (Tagged `[Verified-primary]` in the doc — the
  tag is a weak signal.)
- **Snowflake/TruEra "$7.86M"** — acquisition real (May 2024); **price was never disclosed**; TruEra
  had raised ~$42M, so the figure is fabricated.
- **F2 "95.25% / 94.75% / 94.25%" on SpreadsheetBench Verified** — real SOTA is **~70%** (Gemini
  70.48%, Kingsoft Qingqiu 69.96%); the 94% competitor scores exist only in F2's own marketing blog.
- **"American Registry of Pathology (AFIP)" as a C2PA alternative** — a 3-way conflation of a
  military lab **closed in 2011**, a medical-textbook nonprofit, and an unrelated deepfake-detection
  site that borrows the AFIP name.
- **Humanity's Last Exam "~35% AI vs ~90% human, 50-pt gap"** — garbled: launch scores were ~3–9%,
  now ~44–46%; there is no measured 90% human baseline (that 90% described the *old* MMLU).
- **Brellium "87% reduction in compliance findings"** — the real 87% is reduction in **chart-review
  time** at one client; a real number on the wrong metric.
- **OpenTelemetry GenAI conventions "stabilized in 2025"** — still **experimental** ("Development").
- **RTCT announcement "May 27 2026"** — actually **Apr 28 2026** (May 27 was the comment-period
  extension).
- **"ConfusedPilot, Aug 9 2024, via MCP"** — it is RAG data-poisoning, Oct/Nov 2024, not an MCP
  exfiltration; the **Google-Calendar agent attack "Jan 2026"** is SafeBreach's Feb/Aug-2025 work.
- **GPT-3 MMLU "~35%"** — actually ~44% few-shot / ~38% zero-shot (the ~35% is the human-rater floor).
- Minor: BACE's acronym mis-expanded; DIFFCODEGEN's "applied asynchronously" embellished;
  PrecisionDiff is bf16/f16 + int16/int8, not "FP16/INT8"; the Opus-4.5 "contamination-resistant
  variant" figure is its SWE-bench **Pro** score.

## Method finding (folded into `AGENT_AUDIT_METHOD.md`)
Across the three docs the fabrication clustered by **terrain, not topic**: soft/commercial ground
(prices, market shares, competitive rankings, single-vendor comparison blogs) was fabricated; hard/
citable ground (arXiv IDs, CFR sections, docketed FDA guidance, DOIs) held up. **Trust in proportion
to citability; auto-distrust prices / market-share / "who's winning" / single-vendor cites;
`[Verified-primary]`-style tags are a weak signal — spot-check every ID.**

## Sources (RESEARCH_ONLY, web; judge by concept)
- OpenAI, "Why we no longer evaluate SWE-bench Verified." https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/
- METR, early-2025 AI dev-productivity RCT. https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ · https://arxiv.org/abs/2507.09089
- "Are 'Solved Issues' in SWE-bench Really Solved Correctly?" (ICSE 2026). https://arxiv.org/abs/2503.15223
- SWE-bench Pro (Scale AI). https://scale.com/blog/swe-bench-pro
- Self-preference bias. https://arxiv.org/abs/2410.21819 · "Bias in the Loop." https://arxiv.org/abs/2604.16790 · Dutta, post-decision manipulability. https://arxiv.org/abs/2606.05384
- LLMORPH https://arxiv.org/abs/2603.23611 · BACE https://arxiv.org/abs/2603.28653 · POET https://arxiv.org/abs/2603.19333 · PrecisionDiff https://arxiv.org/abs/2604.19790 · MT survey https://arxiv.org/abs/2605.13898
- Anthropic, demystifying agent evals. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents · OWASP LLM Top 10. https://genai.owasp.org/llm-top-10/
- FDA CDS final guidance PDF. https://www.fda.gov/media/191560/download · FDA AI-for-regulatory-decisions (Fed Reg). https://www.federalregister.gov/documents/2025/01/07/2024-31542/considerations-for-the-use-of-artificial-intelligence-to-support-regulatory-decision-making-for-drug
- JAMA Health Forum recall study (DOI 10.1001/jamahealthforum.2025.3172). https://jamanetwork.com/journals/jama-health-forum/fullarticle/2837802
- Joint Commission + CHAI guidance. https://www.chai.org/news/joint-commission-and-coalition-for-health-ai-chai-release-initial-guidance · CHAI model-card schema. https://github.com/coalition-for-health-ai/mc-schema
- WA My Health My Data Act (RCW 19.373). https://app.leg.wa.gov/RCW/default.aspx?cite=19.373 · Membership Inference Attacks. https://arxiv.org/abs/1610.05820
