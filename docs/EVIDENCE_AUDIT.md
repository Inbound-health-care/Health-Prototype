# Pull-request evidence audit

The evidence audit compares a pull request's declared scope and verification to
changed-path categories. It does not interpret clinical content, source text, or
the meaning of a health record.

## Run

GitHub Actions runs:

```text
python scripts/audit_evidence.py --base event --head event --event-file "$GITHUB_EVENT_PATH" --artifact artifacts/evidence-audit.json
```

For a local event fixture and explicit refs:

```text
python scripts/audit_evidence.py --base REF --head REF --event-file PATH --artifact PATH
```

The default is advisory and exits zero after producing results. `--strict`
returns nonzero when a check flags; CI does not use strict mode until a later ADR
establishes enough history to justify enforcement.

## Stable check IDs

| ID | Contract |
|---|---|
| `EVIDENCE_TEMPLATE_SECTIONS` | Required PR template sections exist. |
| `EVIDENCE_DEVIATIONS` | The deviations section is completed, including explicit `None`. |
| `EVIDENCE_AI_DISCLOSURE` | Exactly one AI option is selected and assisted work identifies review context. |
| `EVIDENCE_RISK_CLASS` | At least one health/provenance class is selected. |
| `EVIDENCE_VERIFICATION` | Verification includes a concrete command/result statement. |
| `EVIDENCE_PROVENANCE` | Clinical, extractor, view, or data changes confirm provenance boundaries. |
| `EVIDENCE_COMPLIANCE_WORDING` | Compliance-sensitive files declare that classification. |
| `EVIDENCE_ADR_CONFIRMATION` | Changed ADRs have status and confirmation sections and are named in the PR. |
| `EVIDENCE_CANONICAL_DOCS` | Impactful changes record `STATUS.md` reconciliation. |
| `EVIDENCE_PROJECT_MAP` | Added non-test files update and record `PROJECT_MAP.md`. |
| `EVIDENCE_UNLOGGED_FILES` | Changed files all map to a known repository category. |

Checks operate on template structure, checkbox state, changed paths, and ADR
headings. They do not judge whether clinical statements are correct.

## Artifact boundary

The 30-day workflow artifact contains only:

- schema version, PR number, base/head commit IDs, and generation timestamp;
- check IDs, severities, and pass/flag status;
- counts by changed-path category.

It contains no PR-body text, source or record content, changed paths, comments,
or sensitive values. The workflow has `contents: read`, does not comment, does
not commit, and does not push.

## Reviewed history

History is never auto-committed. After five completed audit runs or 30 days,
whichever occurs first, download the metadata artifacts and open a normal
reviewed history PR:

```text
python scripts/audit_history.py import FILE...
```

The importer validates the exact schema, rejects extra fields, deduplicates by
head commit ID, and appends compact NDJSON records to
`docs/evidence-audit-history.ndjson`.

Retrospectives are proposal-only and refuse to run before five unique entries:

```text
python scripts/audit_history.py retro
```

The output identifies repeatedly flagged check IDs for human review. It does not
edit workflow or audit rules.
