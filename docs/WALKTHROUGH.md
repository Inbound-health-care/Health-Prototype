# Health-Prototype — Walk-through

*A local, synthetic-data prototype that surfaces and cites patterns in health records without interpreting them. · 2026-06-16*

## Bottom line

Health-Prototype is a research / learning prototype, not a clinical product and
not a medical device. It runs locally on synthetic data, uses Python standard
library runtime code, and is designed to make no network calls.

Its governing rule is the **librarian rule**: surface, count, group, and cite the
source material; do not score, rank, diagnose, triage, recommend, or state what a
pattern means. The tool can show that an item appeared on specific dates and cite
the source spans. A human decides whether that evidence matters.

Do not use this repository with real patient records, PHI, live clinical exports,
or private operational data.

## 1. What it is

**Plain-language view:** The prototype reads dated health-style records and points
out when explicit items recur, cluster, return after a gap, co-occur, or change
cadence. It behaves like a librarian: it finds relevant source lines and points
back to them, then stops.

**Technical view:** The repository is a deterministic surfacing engine. The base
record shape is:

```python
{
    "id": "R001",
    "entries": [
        {"date": "2026-01-10", "item": "poor sleep", "source_span": [12, 22]},
    ],
}
```

The core contract is that surfaced findings carry provenance: record ID, item or
item pair, dates, counts, and source spans when available. The engine does not
convert that provenance into a clinical conclusion.

## 2. Public boundary

This repository uses healthcare-adjacent language because the prototype is shaped
around health records. That does not make it production healthcare software.

Current public boundary:

- **No real PHI.** Only synthetic records, examples, fixtures, and demos are
  allowed.
- **No clinical use.** The project is not clinically validated and should not be
  used for real patient care.
- **No regulatory determination.** HIPAA and FDA references in the repo are design
  context and research notes, not legal advice and not counsel verification.
- **No runtime model judgment.** Runtime behavior is deterministic and stdlib-only;
  it does not use an LLM to interpret records.
- **No recommendations.** Output is cited evidence, not a decision.

## 3. How it is built

Runtime modules:

- `extract.py` converts free text into canonical records through deterministic
  allowlist extraction with character-offset provenance.
- `recurrence.py` runs the surfacing rules and the combined report router.
- `view_html.py` provides shared HTML-view helpers: theme, highlighting,
  keyboard behavior, print handling, and multi-patient chrome.
- `report_html.py` renders the inspection view.
- `digest_html.py` renders the pre-visit pattern digest view.
- `audit.py` records hash-chained audit events containing digests and counts only.

The dependency direction is kept simple: extraction and views feed or display the
engine; the core engine does not depend on the views.

## 4. How it works

The engine has five deterministic surfacing rules:

| Rule | Function | What it surfaces |
|---|---|---|
| Recurrence | `detect_recurrence` | Same item appears at least `min_count` times. |
| Gap / re-emergence | `detect_gap` | Item returns after more than `gap_days` absent. |
| Frequency / burst | `detect_frequency` | Item appears `min_count`+ times inside `window_days`. |
| Co-occurrence | `detect_cooccurrence` | Two items appear together on the same date, or within an opt-in window. |
| Cadence change | `detect_cadence_change` | An item's spacing between events changes by at least `ratio`. |

`run_report` groups surfaced findings under their record. Records with no
surfaced findings are omitted; omission is not a safety, normality, or priority
statement.

Matching is exact by default. Optional matching layers can normalize strings,
merge caller-declared synonyms, or use stdlib fuzzy matching for lookalikes. When
variants are merged, the output cites the original variants so a reviewer can see
what was grouped.

## 5. What the refusal to interpret means

The refusal to interpret is intentional.

Example: if the extractor allowlist contains `chest pain`, then the sentence
`Denies chest pain` still surfaces `chest pain` as a cited mention. The prototype
is not deciding whether the symptom is present, absent, relevant, urgent, or
clinically meaningful. It is preserving the source evidence for review.

This is why the output avoids judgment terms, ranking, severity language,
causation claims, probability scores, and recommendations.

## 6. Governance and verification

The repository has controls around both software behavior and public handling:

- `AGENTS.md` defines the librarian rule, branch/PR discipline, and operator
  workflow.
- `SECURITY.md` and `SECURITY_AND_TOOL_POLICY.md` define the no-PHI, no-secrets,
  local-only boundary.
- `tools/scan_sensitive_changes.py` scans added diff lines for high-confidence
  secrets and identifier shapes. It is defense-in-depth, not a HIPAA
  de-identification proof.
- `.github/control-policy.json` and `tools/control_audit.py` check that required
  control files and workflow-hardening rules remain present.
- `docs/adr/` records design decisions and their confirmation method.
- `STATUS.md` is the canonical current-state document.

Standard verification command:

```bash
make check
```

That target is expected to cover tests, self-tests, lint/compile checks, and the
repository-control audit according to the current Makefile.

## 7. What it proves and what it does not prove

It demonstrates that a small deterministic pipeline can surface cited evidence
from synthetic health-style records while preserving a non-interpretive boundary.
It also demonstrates a governance pattern: ADRs, evidence levels, tests,
sensitive-change scanning, and repository-control checks.

It does **not** prove:

- clinical validity
- diagnostic accuracy
- medication safety
- HIPAA de-identification
- FDA device or non-device status
- production readiness
- safe operation on real patient data

## 8. Honest limits

- The project is intentionally narrow.
- Strict literal extraction can surface mentions that a human would later dismiss.
- Legal and regulatory notes are research context unless separately counsel-verified.
- Synthetic fixtures do not establish real-world clinical performance.
- Hash-chained audit logs have stated limits; for example, tail truncation requires
  an externally published head value to detect reliably.
- Some repo status counts are point-in-time and should be verified with the current
  test command before being repeated externally.

## Glossary

- **PHI:** Protected Health Information; identifiable patient or health data. This
  repo uses synthetic data only.
- **Librarian rule:** Surface, count, and cite provenance; never interpret.
- **Provenance:** The source trace for a finding, such as dates and character
  spans.
- **Surfacing rule:** A deterministic rule that returns cited findings.
- **Gazetteer / allowlist:** The curated terms the extractor is allowed to emit.
- **ADR:** Architecture Decision Record; a numbered decision log entry.
- **Evidence level:** A tag describing how strongly a claim has been verified.
- **Pure stdlib / local-only:** Runtime code uses Python's built-in library and is
  designed for no network access.
