# 0009 — Firewall: the legal grounding (HIPAA Safe Harbor + FDA Non-Device CDS)

**Date:** 2026-06-05
**Evidence level:** RESEARCH_ONLY for the legal citations — web sources, **NOT
counsel-verified**; the primary HHS/FDA pages returned 403 to the fetcher, so the
verbatim text must be re-confirmed against the primary documents before anyone relies
on this. The engine-side firewall rules this *formalizes* are already
CONFIRMED_ASSISTANT_SIDE (the BANNED-word tests).
**Type:** Architecture / firewall / legal grounding

## Context
`recurrence.py` calls the firewall "the design principle and the legal firewall in one,"
but the *legal* half was asserted, never written down or cited. Scott asked to ground it
in the actual definitions of what is and isn't allowed, and to build free-text extraction
as an **allowlist of acceptable items** rather than a denylist of bad ones. Two bodies of
law bind a tool that surfaces health data:
- **HIPAA** — what is PHI / when data is de-identified (45 CFR §164.514(b)).
- **FDA Non-Device CDS** — the line between *surfacing* information and *interpreting* it
  (which makes software a regulated device) (FD&C Act §520(o)(1)(E); FDA CDS final
  guidance, refreshed Jan 2026).

This is **not legal advice** — it records what the regulations/guidance say so the
firewall is anchored and checkable; Scott/counsel judge. The full cited write-up lives in
Drive `health-prototype/freetext-design/FIREWALL_legal_grounding.md` (the repo stays lean).

## Decision
Adopt a two-layer firewall, each rule traceable to the definition it satisfies.

**Layer 1 — PHI firewall (HIPAA), allowlist by construction.**
- Extraction surfaces ONLY terms on a curated **allowlist gazetteer** of acceptable
  clinical concepts. The 17 non-date Safe-Harbor identifiers (names, SSN, MRN, contact
  info, account/device IDs, biometrics, photos, the catch-all unique code, …) are
  **structurally un-extractable** — they are not clinical concepts, so never on the list.
- **Dates** are the one Safe-Harbor identifier (#3) the engine genuinely needs (gap /
  cadence / frequency / co-occurrence are date math). Resolution: the rules run on
  **intervals**, which are preserved under a **consistent per-record date shift** (an
  Expert-Determination technique), so de-identify the calendar without breaking the math.
  Default posture = de-identified/shifted; identified treatment-use (treating provider) is
  the documented alternative.
- No raw free-text enters a record — only `concept + (shifted) date + provenance offset`.
  Reinforced by the existing zero-egress / local-only / synthetic-only rules.

**Layer 2 — Interpretation firewall (FDA), surface/cite only.**
- The four Non-Device-CDS criteria: (1) no medical-image / IVD-signal analysis;
  (2) display/analyze medical info; (3) provide **recommendations** to an HCP; (4) let the
  HCP **independently review the basis**. The engine makes **no recommendations at all** —
  it surfaces counts/dates/citations — so it sits at/below the non-device line, with the
  basis fully exposed (criterion 4 maximally met: the output *is* the basis).
- Therefore the librarian rule (never score/rank/diagnose/recommend; no
  caution/risk/severity/worsening language) is the control that keeps the engine off the
  device pathway. The existing BANNED-word tests enforce it; their docstrings will cite the
  criterion each protects.

Rejected: a denylist of "bad" terms (an allowlist is safer — unknown text can't leak);
Safe-Harbor date-truncation to year (breaks the engine); NegEx/ConText assertion
*verdicts* (interpretation — only their cue *lists* are borrowed, as surfaced provenance).

## Consequences
- The firewall is anchored to citable definitions, not assertion — each rule names the
  identifier # / criterion # it enforces (that traceability is the deliverable).
- Gives free-text extraction a clear, low-risk shape (allowlist gazetteer + shifted dates)
  before any code is written.
- The legal citations are web-sourced and must be re-verified against primary HHS/FDA
  sources (and ideally counsel) before any real-PHI use — flagged, not hidden.
- No engine behavior changes here; this is grounding + documentation.

## Confirmation
- **Now:** this ADR + a `SECURITY_AND_TOOL_POLICY.md` note land; the full cited write-up is
  in Drive; `make check` stays green (docs-only). The rule→definition mapping is reviewable
  in `FIREWALL_legal_grounding.md`.
- **On free-text slice 1 (future):** three tests prove it — (a) a note containing a
  name/SSN/MRN yields NO record for those (allowlist holds); (b) absolute dates are
  shifted/relativized with intervals preserved; (c) the BANNED-word tests, now citing their
  FDA criterion, still pass. Only then does the legal grounding move from RESEARCH_ONLY
  toward CONFIRMED.
- **Standing:** primary-source + counsel verification of the HIPAA/FDA claims before any
  real-PHI deployment.
