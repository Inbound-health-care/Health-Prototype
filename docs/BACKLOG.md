# Backlog — Health-Prototype

A running parking lot for deferred work, known gaps, and decisions that are the operator's to make,
so the working tree stays clean and nothing gets lost. Not a roadmap or a promise. Add items as
`- [ ] <item> — <why deferred / owner / status>`.

This is a thin index of what is **open**. The authoritative narrative lives in
[`STATUS.md`](../STATUS.md) (front door) and [`docs/adr/`](adr/) (the decision trail); the running
log is [`docs/LEARNINGS.md`](LEARNINGS.md) and [`JOURNAL.md`](../JOURNAL.md). Detail is not
duplicated here — this is the "what's left" view.

## Deferred build (designed, not yet built)

- [ ] **ADR-0029 Stage 2 — temporal-relation surfacing** (`recurrence.py`): an **opt-in** lens
  surfacing BEFORE / AFTER / SAME_DAY / WITHIN_WINDOW(days) over adjacent dated pairs
  (`build_timeline` / `format_timeline` + `--demo-timeline` + an opt-in `--report-timeline`), so the
  default `--report` stays clean. Design is **fixed** (ADR-0029 Stage-2 addendum: non-interpretive
  same-day tie-break, undated surfaced separately, banned-words gate, sequence-not-causation caveat,
  engine rules + oracles byte-unchanged). Build deferred to a fresh session (oracle-first).
- [ ] **ADR-0029 Stage 3 — deterministic follow-up + assertion context** (`extract.py`):
  deterministic `(action, date)` follow-up surfacing + NegEx-style assertion context. UMLS
  normalization explicitly deferred.

## Pending user-side confirmation

- [ ] **ADR-0030 audit trail — CONFIRMED_USER_SIDE.** The governance audit trail (`audit.py`) is
  CONFIRMED_ASSISTANT_SIDE; flips to CONFIRMED_USER_SIDE when Scott runs `python audit.py --demo` on
  his device.

## Operator decisions (Scott's call)

- [ ] **Counsel-verify the legal claims before any real-PHI use** (ADR-0011 / ADR-0009). The
  HIPAA/FDA grounding is RESEARCH_ONLY; the written path is `docs/COUNSEL_VERIFICATION_CHECKLIST.md`.
  Re-confirm vs primary HHS/FDA + counsel; the date-shift is Expert Determination, not Safe Harbor.
- [ ] **Behavioral-health pre-visit-digest roadmap direction** — whether the BH-digest wedge
  reshapes the roadmap (strategic read in `docs/audit-2026-06-05/`). Scott's decision.
- [ ] **Optional: make the CI `html` validity gate blocking** — it reports today but is not a
  branch-protection required check; promote it if you want it to gate merges. (Adds coverage; your
  call.)

## Cross-repo / org

- [ ] **Dedicated logging repo (org-wide idea).** Scott wants a single repo just for logs/history
  later, to keep prototype repos clean. Out of scope here; logged so it isn't lost.
