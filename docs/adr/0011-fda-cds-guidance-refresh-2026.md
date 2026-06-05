# 0011 — FDA CDS guidance refreshed (Jan 2026) + 2026 compliance audit

**Date:** 2026-06-05
**Evidence level:** RESEARCH_ONLY — web-sourced legal/market research, **NOT counsel-verified**
(some primary HHS/FDA pages returned 403 to the fetcher). Re-confirm against primary sources +
counsel before any reliance. Supersedes in part the FDA citation in ADR 0009.
**Type:** Architecture / legal grounding / refresh

## Context
ADR 0009 grounded the librarian rule + allowlist in HIPAA Safe Harbor / Expert Determination and the
FDA Non-Device CDS exclusion, citing FDA's **2022** CDS guidance. A 2026-06-05 compliance/market
audit (full cited write-up off-repo in Drive `health-prototype/audit-2026-06-05/`, RESEARCH_ONLY)
found that guidance — and the surrounding rules — have moved. This ADR records the deltas and the
audit's compliance findings; it does not change any engine behavior.

## Decision — what changed, and what we still hold

**FDA — the Non-Device CDS line (updates ADR 0009 §2):**
- FDA **superseded the 2022 CDS guidance** with a revision issued **Jan 6, 2026** (further superseded
  **Jan 29, 2026**). The **four §520(o)(1)(E) Non-Device criteria still hold**, and the engine's
  "display + cite, never recommend/rank/score" design still maps to them — especially criterion 4
  (the clinician can independently review the basis = our per-item provenance).
- The revision **eases criterion 3 slightly** (enforcement discretion where the single surfaced
  option is the *only* clinically appropriate one) but **raises transparency expectations for
  algorithmic/AI CDS** (document inputs, logic, automation-bias handling). If the engine ever adds
  ML, the **Jan-2025 AI-DSF lifecycle draft** + **Aug-2025 PCCP final guidance** apply; even as a
  non-device, documenting the logic helps defend non-device status.

**HIPAA — the PHI line (reaffirms ADR 0009 §1, with an asterisk):**
- Expert Determination (45 CFR §164.514(b)(1)) + a **consistent per-record date shift** remains the
  right path (Safe Harbor truncates dates to year and breaks the interval math). **Asterisk:**
  date-shifting is an Expert-Determination *technique*, **not** Safe-Harbor-compliant on its own — it
  needs a qualified expert's "very small risk" sign-off; rare long gaps can still re-identify.
- The **2024 reproductive-health Privacy Rule was vacated nationwide (June 2025)** — does not apply.
  The **SUD / 42 CFR Part 2** notice updates **survive** (comply by Feb 16, 2026). A proposed
  **Security Rule overhaul (Jan 2025 NPRM)** would make many "addressable" safeguards mandatory — watch.

**The free-text extractor is the single biggest risk to BOTH vectors** (PHI leak via names/MRNs/dates
in narrative text; *and* implying clinical meaning). Keep it allowlist-only, shifted dates, char
offsets, no raw quotes — the slice-1 design already does this; treat it as the regulated boundary.

**Liability reality (new — not in ADR 0009):** Non-Device status is a *regulatory classification, not
tort immunity*. The **learned-intermediary doctrine** routes risk to the clinician, but a **false
pattern the engine surfaces and a clinician acts on** can still draw the vendor in (negligent-design
theories). "Surface-only" lowers FDA-device and standard-of-care exposure; it does not eliminate tort
risk. Mitigation is UX: surface base rates/denominators (not bare flags), one-click dismiss, never
phrase co-occurrence causally.

## Consequences
- ADR 0009's FDA citation (2022 guidance) is updated here; 0009's structure and decision otherwise stand.
- No engine/behavior change — documentation + direction only; `make check` stays green.
- Until counsel-verified, every legal claim here stays RESEARCH_ONLY.

## Confirmation
- The full cited audit (sources + dates, the 2026 market/white-space read, and the brainstorm) lives
  in Drive `health-prototype/audit-2026-06-05/`.
- **Standing:** primary-source + counsel verification before any real-PHI deployment (unchanged from 0009).
