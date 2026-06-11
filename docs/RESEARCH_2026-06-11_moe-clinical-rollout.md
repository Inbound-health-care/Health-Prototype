# Research — MoE "six experts" clinical-software map, fact-checked + rolled out (2026-06-11) — RESEARCH_ONLY

**Status: RESEARCH_ONLY. Untrusted external data.** This records a pasted "Mixture-of-Experts
maps onto your three engines" document, **what survived independent web verification**, and the
deterministic, librarian-safe subset that graduates into a staged plan (**ADR 0029**). Nothing here
is project truth until a test proves it (`DOC_DISCIPLINE.md` §Research gate). The pasted doc is the
"six experts" item that STATUS has carried as **PARKED** since 2026-06-07 ("as described it would
break pure-stdlib / determinism / non-interpretation"); this is the full run Scott asked for.

## Provenance & method
One pasted document (origin: an external AI assistant). Fact-checked with the repo's own
`AGENT_AUDIT_METHOD` pattern — three parallel subagents, one per claim-cluster, each grading
REAL-BY-NAME / REAL-BY-CONCEPT / UNVERIFIABLE-or-FABRICATED with a real source or "not found",
judging **by concept, not literal name** (invented names often map to real techniques).

**Confidence caveat:** grades rest on search results + primary-source fetches where egress allowed.
Treat every metric below as RESEARCH_ONLY pending a primary-source read.

## The framing problem (why the doc cannot land as written)
The engine is **deterministic, stdlib-core, local-only, zero-PHI**, and bound by the **librarian
rule** (surface / count / cite — never score, rank, diagnose, or interpret). Four of the six
proposed "experts" break a pillar as written:
- **1B "TRIAGE" risk corrector** — emits continuous **risk scores**. Frontal librarian-rule
  violation. The doc itself concedes "your current engine never outputs risk scores — that's the
  librarian rule." **Cut from the rollout.**
- **2A follow-up extractor** — names **BioBERT** (a neural model). The *symbolic half* (date
  arithmetic on extracted (action, date) pairs) is stdlib-doable; the neural half is not adopted.
- **2B CLINES** — **UMLS normalization** needs licensed external vocabularies and is
  interpretation-adjacent (mapping a phrase to a clinical code). The *assertion/negation* slice
  (deterministic, NegEx-style) is the librarian-safe part.
- **3A drift monitor** — an *ML model-adaptation* technique; a **deterministic engine has no model
  to drift**. Reframed to deterministic input-stats / rule-firing-rate telemetry.

Operator decisions for this rollout (2026-06-11): **hold the librarian + local-only + zero-PHI
pillars; relax no-deps to "optional + graceful-skip" only** (core still runs on bare stdlib; deps
are enhancers that skip cleanly when absent, like the existing Hypothesis / Playwright pattern);
**Stage-3 stays deterministic** (lexicons / date libs, **no ML model**). Net effect: everything we
adopt is deterministic and librarian-safe; the neural/scoring experts are out or deferred.

## Verification verdicts (web, 2026-06-11)

### Holds as written (real, sourced)
- **SparseDoctor — REAL-BY-NAME.** Contrastive-learning-enhanced LoRA-MoE on Qwen3-4B; +2.29% over
  HuatuoGPT-II. arXiv 2509.14269 (Sept 2025).
- **CLINES — REAL-BY-NAME.** Modular agentic pipeline: semantic chunking → attribute assignment
  (assertion, value+unit) → UMLS normalization → date resolution; zero-shot; +0.21–0.38 F1 over
  single-prompt baselines. medRxiv 10.64898/2025.12.01.25341355 (Dec 2025).
- **Drift-Aware Monitor — REAL-BY-NAME.** Edge-cloud concept-drift adaptation; the **21 concurrent
  users / 40.6% MAE reduction vs periodic retraining** figures check out (also 66±37 s adaptation
  latency). Future Internet 2026, 18(3):156 (DOI 10.3390/fi18030156).
- **Concept drift in health ML — REAL-BY-CONCEPT.** Established field (Frontiers in AI surveys 2022;
  PMC literature).
- **ATA AI framework — REAL-BY-CONCEPT.** "Real-world performance validation," "continuous
  monitoring," and "ongoing improvement" appear in ATA's updated AI principles — **self-regulatory
  guidance, not a mandate**.

### Corrected (real concept, claim overstated)
- **MedLingo — downgrade to REAL-BY-CONCEPT.** A project page exists (SEECS) but **no published
  paper** was found. Cite the canonical analogue **Med-MoE** (arXiv 2404.10237) instead of treating
  MedLingo as a shipped, peer-reviewed system.
- **"Sparse MoE at 40–50% activation outperforms dense on clinical tasks" — OVERSTATED.** The
  general MoE-efficiency result is real (comparable quality at lower *active compute*); the
  **clinical-text outperformance is unsourced**, and the doc conflates *activation compute* with
  *parameter count* (sparse MoE usually needs **more** total parameters). Keep only "comparable
  quality at lower active compute."
- **"The AMA now explicitly *requires* audits" — verb wrong: requires → recommends/advocates.** The
  audit language (reaudit on material model / training-data / guideline change, plus ≥annual
  comprehensive review) is real **2026 AMA House of Delegates policy**, but it is professional
  guidance, not a binding mandate. Binding force would come from FDA / CMS / state boards.
- **"Hybrid Neural-Symbolic Follow-Up Instruction Extractor" — REAL-BY-CONCEPT, metrics
  FABRICATED.** Hybrid neuro-symbolic + BioBERT + date arithmetic all exist, but no system by that
  name was found, and **the 0.997 / 0.986 Pair F1 and 0.00-day MAE figures are not sourced**. The
  only real anchors are ~0.538 F1 for vanilla LLMs on radiology follow-up (arXiv 2511.11867) and the
  2,000-note *Checkup2Action* set (a different task, arXiv 2605.11533). Keep the concept; **delete
  the F1 / MAE numbers**.

### Cut (unverifiable / fabricated)
- **"TRIAGE framework" — UNVERIFIABLE.** No framework by that name found. The *idea* (continuous
  risk over dialectical reasoning vs binary collapse) appears in scattered work (e.g., OncoReason,
  arXiv 2510.17532), but there is no "TRIAGE," and it violates the librarian rule regardless. Cut.

## Fabrication ledger (checked → false/garbled — do NOT reuse)
Same failure mode the project keeps catching: **confident precision on soft ground.**
- **"TRIAGE framework"** — named system not found; presented as established.
- **Follow-up extractor "0.997 / 0.986 Pair F1, 0.00-day MAE"** — not in any located source; the
  real comparable is ~0.538 F1 for vanilla LLMs on a *different* follow-up task.
- **"Sparse MoE 40–50% activation outperforms dense on clinical tasks"** — conflates active-compute
  with parameter count; no clinical-text outperformance evidence.
- **"MedLingo" as a shipped, published system** — project page only; no paper.
- **"AMA *requires* audits"** — overstates guidance as a binding mandate.

**Method finding (consistent with `AGENT_AUDIT_METHOD.md`):** the hard/citable claims (arXiv IDs,
DOIs, named published systems — SparseDoctor, CLINES, the drift paper) held up; the soft ground
(unnamed-system metrics, "outperforms," "requires") was inflated or fabricated. Trust in proportion
to citability.

## The deterministic, librarian-safe subset → the rollout
Only the parts that survive verification **and** fit every held pillar are carried into **ADR 0029**:

| Stage | Engine | Adopted (deterministic) | Source concept | Dropped / deferred |
|------|--------|-------------------------|----------------|--------------------|
| 1 | Governance (new) | Append-only, hash-chained **audit trail** of every surface/extract event + deterministic **rule-firing-rate / input-stats monitor** | 3B audit (AMA/ATA, reworded to "recommend"); 3A reframed (no ML) | ML drift-adaptation; "requires" framing |
| 2 | `recurrence.py` | Deterministic **temporal-relation surfacing** (before / after / same-day / within-window, Allen-interval style) + timeline enrichment over already-cited dates | 1A temporal extractor | Risk scoring (1B, cut) |
| 3 | `extract.py` | Deterministic **(action, date) follow-up extraction** (date arithmetic, no model) + **negation/assertion context** (NegEx-style lexicon, optional graceful-skip) | 2A symbolic half; 2B assertion slice | BioBERT; UMLS normalization (deferred — license + interpretation) |

## Sources (RESEARCH_ONLY, web; judge by concept)
- SparseDoctor (contrastive LoRA-MoE). https://arxiv.org/abs/2509.14269
- CLINES (modular clinical extraction). https://www.medrxiv.org/content/10.64898/2025.12.01.25341355v1
- Med-MoE (analogue for "MedLingo"). https://arxiv.org/abs/2404.10237
- Drift-aware edge-cloud monitoring (21 users / 40.6% MAE). https://doi.org/10.3390/fi18030156
- Healthcare concept-drift survey. https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2022.955314/full
- Radiology follow-up detection (~0.538 F1 vanilla LLM). https://arxiv.org/abs/2511.11867
- Checkup2Action (2,000-note set, different task). https://arxiv.org/abs/2605.11533
- BioBERT. https://academic.oup.com/bioinformatics/article/36/4/1234/5566506
- Neuro-symbolic auditable clinical IE. https://www.nature.com/articles/s43856-025-01194-x
- OncoReason (continuous + binary clinical reasoning). https://arxiv.org/abs/2510.17532
- AMA AI principles (audit guidance, 2026). https://www.ama-assn.org/system/files/ama-ai-principles.pdf
- ATA AI principles (validation / monitoring). https://www.americantelemed.org/press-releases/american-telemedicine-association-publishes-new-artificial-intelligence-ai-principles/
