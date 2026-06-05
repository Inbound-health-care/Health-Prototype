# Counsel-Verification Checklist — HIPAA + FDA (RESEARCH_ONLY)

**Status: RESEARCH_ONLY. This is NOT legal advice.** It records what public regulations / guidance
and reputable legal analysis appear to say, so the project's two load-bearing legal claims can be
checked by qualified counsel before any real-PHI use. Web-sourced (primary FDA.gov / HHS.gov pages
were not directly retrievable in research; verbatim text is from the eCFR/Cornell mirror plus
concurring law-firm summaries) — **counsel must confirm exact wording**. Relates to ADR 0009 (the
two PHI/CDS claims), ADR 0011 (the 2026 audit), ADR 0013 (relative-date de-id composition), and
`SECURITY_AND_TOOL_POLICY.md` §C.1. Created 2026-06-05 to resolve the ADR 0011 "counsel-verify"
open loop (build + checklist doc; the ADR 0009 edits are **deferred** to post-counsel — see below).

## The two claims under test
1. **HIPAA de-identification** (45 CFR 164.514(b)) — an allowlist extractor that surfaces only
   curated clinical concepts, with **dates handled via a consistent per-record date SHIFT**, stays
   within de-identified status.
2. **FDA "Non-Device" CDS** (21st Century Cures Act §520(o)(1)(E) + FDA CDS guidance) — an engine
   that only surfaces/cites patterns and makes **no recommendations** sits below the
   software-as-a-medical-device line.

## Counsel-verification checklist (ordered)
1. **Engage two counsel tracks** (different specialties): (i) FDA regulatory / digital-health device
   counsel for the CDS question; (ii) HIPAA privacy counsel for de-identification. Don't assume one
   firm covers both well.
2. **Lock the verbatim primaries.** Have counsel pull and quote: eCFR **45 CFR 164.514(b)(1)/(b)(2)**
   (Expert Determination + Safe Harbor) and **164.514(e)** (Limited Data Set); the **Jan 29 2026 CDS
   final guidance** (FDA media/191560) and the companion General Wellness update. Replace this repo's
   web-sourced paraphrases with those.
3. **HIPAA — commission a written Expert Determination** for the dataset + the consistent
   per-record date-shift + the allowlist-extracted concepts + the intended recipient/environment.
   Deliverable: a statistician's report documenting methods and the "very small risk" justification,
   retained for audit. Have it address the known weak spot: **rare long gaps / outlier intervals can
   still re-identify** even after shifting (and reused shifts / residual date-like text can leak the
   offset — ADR 0013).
4. **Decide the data posture per use:** de-identified (Expert Determination) vs **Limited Data Set**
   (still PHI; needs a DUA) vs identified treatment-use by the treating provider.
5. **FDA — prepare a Non-Device positioning memo** mapping each engine behavior to the four criteria
   (the librarian-rule **banned-word tests** and the per-item `source_span` provenance are evidence),
   and document what the engine does NOT do (no image/IVD-signal analysis; no recommendation / score /
   rank; basis fully exposed).
6. **Optional FDA interaction, cheapest first:** informal **Q-Sub** feedback (no fee, ~70-day) to
   confirm "not a device"; escalate to a formal **513(g)** Request for Information (~$7,820 standard /
   ~$3,910 small-business FY2026) only if a payer/partner demands a paper trail.
7. **Liability / UX hardening** (with counsel + product): surface base rates / denominators, not bare
   flags; one-click dismiss; never phrase co-occurrence causally; capture clinician agree/disagree;
   label the tool as a reference/librarian with the clinician as decision-maker (reinforces criterion
   4 transparency + the learned-intermediary defense).
8. **Pilot gate:** treat **(3) Expert Determination report + (5) FDA Non-Device memo** as the
   **minimum** cleared before any real PHI touches the system. Q-Sub / 513(g) are confidence boosters,
   not blockers.

## FDA Jan-2026 findings (verified directionally; confirm verbatim with counsel)
- The 2022 CDS guidance was superseded **Jan 6 2026**, itself superseded **Jan 29 2026**. The
  **March 11 2026** item was a **Town Hall**, not a third revision — so "refreshed twice in Jan 2026"
  (ADR 0011) is correct; "three times / a March refresh" would be wrong.
- The **four statutory Non-Device criteria are unchanged** (fixed by statute). 2026 changed FDA's
  *interpretation/enforcement*, mostly loosening: (i) enforcement discretion when software surfaces a
  single clinically appropriate option; (ii) **automation-bias / "time-critical" language moved from
  criterion 3 into criterion 4** (a factor in whether the HCP can independently review the basis, not
  an automatic disqualifier); (iii) **heightened transparency** for algorithmic/AI CDS (disclose
  inputs, logic, how outputs are generated).
- Net: the surface-only, cite-everything design maps well to all four criteria and **maximally to
  criterion 4** (the output *is* the basis). The transparency emphasis is a tailwind, not a threat —
  but if the engine were ever embedded in a time-pressured workflow, criterion 4 could pull even on
  surface-only output.

## HIPAA date distinction (get this exactly right)
- **Safe Harbor** permits **only the year** for dates tied to an individual (no element finer than
  year), and caps ages at **90+**. Truncating to year breaks the engine's interval math.
- A **consistent date-SHIFT is therefore NOT Safe Harbor.** It is an **Expert-Determination**
  technique (shifted dates may also live in a **Limited Data Set**, which is still PHI under a DUA).
  **Until a written Expert Determination exists for the specific dataset, treat shifted-date data as
  PHI/LDS, not de-identified.**

## BH-roadmap note (RESEARCH_ONLY strategy)
- **Relative-date anchoring (ADR 0013) is the wedge feature** — it is near-prerequisite for a
  single-patient pre-visit pattern digest (all five rules are date-driven; psych prose is relative).
- **Multi-patient handling is a later panel/registry play** (throughput, not signal for one chart).
- The durable edge is the **discipline** (a non-generative librarian can't hallucinate an
  interpretation, so there's nothing to fabricate or to regulate as decision support) **plus
  extraction accuracy** — not the cite feature alone (generative incumbents are adding citations).
  Validate the "what clinicians want pre-visit" hypotheses (adherence gaps, no-shows, PHQ-9/GAD-7
  trends, recurring themes) with target clinicians before betting the roadmap.

## DEFERRED repo-doc fixes (recorded; NOT applied until counsel — Scott's call)
Apply these to the canonical docs only after counsel confirms (kept here so they aren't lost):
- **ADR 0009 §1:** re-label Layer 1 as a Safe-Harbor-*shaped* allowlist for the **17 non-date
  identifiers**; state plainly that the **date-shift sits under Expert Determination / LDS, not Safe
  Harbor**. (ADR 0009's current parenthetical blurs this; ADR 0011's asterisk already corrects it.)
- Sweep any remaining **bare cite to the "2022 CDS guidance" as live** (e.g. in ADR 0009's body) →
  point to the Jan 29 2026 final.
- Add a sentence noting the **criterion 3 → 4 relocation** (automation-bias / time-critical).
- Re-check `SECURITY_AND_TOOL_POLICY.md` §C.1's FDA cite against the Jan-2026 guidance.

## Multi-patient (specced; deferred — see ADR 0013 "Rejected")
When built: split only on an explicit operator-defined delimiter + an explicit per-segment patient
key; **fail closed** (refuse/quarantine a segment with a missing/ambiguous key — never infer identity
from prose); per-segment de-id with a per-patient shift key; provenance-stamp every record. The
dominant documented risk is patient mis-attribution / record bleed.

## Sources (RESEARCH_ONLY, web; judge by concept)
- FDA CDS Software guidance (landing). https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- FDA CDS final guidance PDF (Jan 29 2026; quote verbatim). https://www.fda.gov/media/191560/download
- FDA CDS Final Guidance Town Hall, 03/11/2026 (a town hall, not a revision). https://www.fda.gov/medical-devices/medical-devices-news-and-events/town-hall-clinical-decision-support-software-final-guidance-03112026
- FDA Law Blog (Hyman Phelps), "A Busy Day in the (CDRH) Neighborhood," Jan 2026. https://www.thefdalawblog.com/2026/01/a-busy-day-in-the-cdrh-neighborhood-updates-to-the-cds-and-general-wellness-guidance-documents/
- Cooley, "Automation Bias … FDA Incremental Updates to CDS Guidance," Jan 2026. https://www.cooley.com/news/insight/2026/2026-01-20-automation-bias-and-clinical-practice-fda-makes-incremental-updates-to-clinical-decision-support-software-guidance
- Faegre Drinker, "Key Updates in FDA's 2026 General Wellness and CDS Software Guidance." https://www.faegredrinker.com/en/insights/publications/2026/1/key-updates-in-fdas-2026-general-wellness-and-clinical-decision-support-software-guidance
- HHS OCR, Guidance on De-identification (Safe Harbor + Expert Determination). https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html
- eCFR / Cornell LII, 45 CFR 164.514 (verbatim date rule; methods; LDS). https://www.law.cornell.edu/cfr/text/45/164.514
- FDA 513(g) Requests for Information (procedures/fees). https://www.fda.gov/regulatory-information/search-fda-guidance-documents/fda-and-industry-procedures-section-513g-requests-information-under-federal-food-drug-and-cosmetic
- FDA Q-Submission Program (Pre-Sub mechanics; no fee). https://www.fda.gov/regulatory-information/search-fda-guidance-documents/requests-feedback-and-meetings-medical-device-submissions-q-submission-program
- Winston & Strawn, "AI and the Learned Intermediary Doctrine" (defense, not immunity). https://www.winston.com/print/v2/content/1098391/a-new-intermediary-artificial-intelligence-and-the-learned-intermediary-doctrine.pdf
