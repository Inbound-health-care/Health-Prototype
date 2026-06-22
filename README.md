# Health-Prototype

A local, deterministic healthcare-record surfacing prototype.

This repository explores one narrow workflow: given synthetic, dated health-style
records, surface repeated or related mentions and cite exactly where each mention
came from. The project is designed as a **librarian, not an interpreter**: it can
surface, count, group, and cite provenance; it must not score, rank, diagnose,
triage, recommend, or explain what a pattern means.

## Public boundary

This is a research / learning prototype, not a clinical product and not a
medical device. It is not clinically validated, not counsel-verified for HIPAA or
FDA status, and not safe to use with real patient records.

Operational boundaries:

- **Synthetic data only.** Do not add PHI, real patient records, secrets, tokens,
  private clinical details, screenshots of real records, or unsanitized exports.
- **Local-only runtime.** Runtime code is Python standard-library only and is
  designed for no network egress.
- **Deterministic behavior.** The engine applies explicit rules and returns cited
  findings; it does not use an LLM or model judgment at runtime.
- **Human judgment remains outside the engine.** A surfaced item is evidence to
  review, not a conclusion.

## What it does

The prototype can take either canonical records or free-text notes that are
converted into canonical records, then run deterministic surfacing rules over
those records.

```text
Free-text note
    │
    ▼
extract.py            deterministic allowlist extraction + char-offset provenance
    │
    ▼
canonical records     {id, entries: [{date, item, source_span}]}
    │
    ▼
recurrence.py         five surfacing rules, each per record
    │
    ▼
surfaced findings     recurrence · gap · frequency · co-occurrence · cadence change
    │
    ▼
text or HTML report   recurrence.py --report · report_html.py · digest_html.py
```

Every step is deterministic and cites its source. No step interprets clinical
meaning.

## What this system deliberately does not do

It does not:

- diagnose, triage, or assign severity
- infer causation — co-occurrence means "appeared together," never "caused"
- decide whether a finding matters
- rank records or patients
- produce clinical recommendations
- assign a confidence, probability, priority, or risk score
- claim HIPAA de-identification or FDA non-device status

A finding is either surfaced by a deterministic rule or absent under that rule.
Example: the note *"Denies chest pain"* still surfaces `chest pain` if that term
is in the gazetteer. The system cites the exact source span; a human decides
whether the mention is clinically relevant.

## Record shape

```python
record = {
    "id": "R001",
    "entries": [
        {"date": "2026-01-10", "item": "poor sleep"},
        {"date": "2026-02-02", "item": "poor sleep"},
        {"date": "2026-02-20", "item": "appetite change"},
    ],
}
```

## The base function

```python
def detect_recurrence(records: list, field: str = "item", min_count: int = 2) -> list[RecurrenceHit]:
    """Return recurrence hits. Each hit cites the record id, the item, the
    count, and the dates it appeared on. Surfaces only — no interpretation."""
```

Each hit reports the record ID, item, count, and dates. Rendered output line:

```text
Record R001: "poor sleep" recurred 2 times — 2026-01-10, 2026-02-02
```

## Running it

```bash
python recurrence.py --self-test                  # required recurrence spec cases
python recurrence.py --demo                        # recurrence, v0 exact match
python recurrence.py --demo-v1                      # recurrence, opt-in matching layers
python recurrence.py --demo-gap                     # gap / re-emergence rule
python recurrence.py --demo-frequency               # frequency / burst rule
python recurrence.py --demo-cooccurrence            # co-occurrence, same date
python recurrence.py --demo-cooccurrence-window     # co-occurrence within a 7-day window, opt-in
python recurrence.py --demo-cadence-change          # cadence change
python recurrence.py --report                        # combined per-record report
make check                                           # tests + self-test + lint + repo controls
python -m unittest discover -s tests -t .          # full unittest suite
```

Captured command output lives in [`docs/DEMO_OUTPUT.md`](docs/DEMO_OUTPUT.md).
The synthetic record set and hand-written answer keys live in
[`data/sample_records.py`](data/sample_records.py); field rationale and per-record
fixture reasons live in [`data/RECORDS.md`](data/RECORDS.md).

## Surfacing rules

The engine surfaces patterns through independent rules that read the same grouped
occurrences. Each rule surfaces, counts, and cites; none interprets.

| Rule | Function | What it surfaces |
|---|---|---|
| Recurrence | `detect_recurrence` | Same item appears at least `min_count` times. |
| Gap / re-emergence | `detect_gap` | Item returns after more than `gap_days` absent. |
| Frequency / burst | `detect_frequency` | Item appears `min_count`+ times within `window_days`. |
| Co-occurrence | `detect_cooccurrence` | Two items appear together on the same date, or within an opt-in window. |
| Cadence change | `detect_cadence_change` | An item's spacing between events changes by at least `ratio`. |

One record can surface under several rules. Records that surface nothing are
omitted from combined reports; they are not labeled normal, safe, low-priority,
or resolved.

### Combined report

`run_report` (CLI `--report`) runs all five rules over one record set and groups
every finding under its record, each line tagged with the lens that surfaced it.

```text
Record R015:
  [recurrence] "depression" recurred 3 times — 2026-01-10, 2026-09-10, 2026-10-05
  [gap] "depression" returned after 243 days — last seen 2026-01-10, then 2026-09-10

Record R016:
  [recurrence] "chest pain" recurred 4 times — 2026-02-01, 2026-02-10, 2026-02-20, 2026-05-10
  [frequency] "chest pain" appeared 3 times within 19 days — 2026-02-01, 2026-02-10, 2026-02-20
```

## Matching

The default is exact match. Same meaning in different words is not combined
unless an explicit matching layer is requested.

```python
detect_recurrence(records, normalize=True, synonyms={"insomnia": "poor sleep"}, fuzzy_cutoff=0.85)
```

- `normalize=True` — case-fold, trim, and collapse whitespace.
- `synonyms={variant: canonical}` — merge only caller-declared synonyms.
- `fuzzy_cutoff=0.0–1.0` — merge lookalikes/typos through stdlib `difflib`; off by
  default because it groups without a declared synonym rule.

When different spellings are combined, the output cites the original variants:

```text
Record R006: "poor sleep" recurred 3 times — … [merged: "can't sleep", "insomnia", "poor sleep"]
```

## Governance and verification

The repository carries a public-healthcare boundary, but it does not claim
clinical readiness or regulatory compliance.

- `AGENTS.md` defines the librarian rule and operator workflow.
- `SECURITY.md` and `SECURITY_AND_TOOL_POLICY.md` define the no-PHI / no-secrets /
  local-only boundary.
- `.github/control-policy.json` and `tools/control_audit.py` make required control
  files and workflow hardening checkable.
- `docs/adr/` records decisions and their confirmation method.
- `docs/LEARNINGS.md` records reusable operational lessons.

## License

Licensed under the [Apache License 2.0](LICENSE). See ADR 0024.

## Repo map

- **Rules** — `AGENTS.md`, `CLAUDE.md`, `SECURITY.md`, `SECURITY_AND_TOOL_POLICY.md`.
- **Front door / state** — `LOAD.md`, `STATUS.md`, `PROJECT_MAP.md`.
- **Decisions** — `docs/adr/`, `docs/DOC_DISCIPLINE.md`.
- **Verification** — `make check`, `tools/scan_sensitive_changes.py`,
  `tools/control_audit.py`, `.github/workflows/`.
- **Product prototype** — `recurrence.py`, `extract.py`, `audit.py`,
  `view_html.py`, `report_html.py`, `digest_html.py`.

Plain-language and technical walk-through: [`docs/WALKTHROUGH.md`](docs/WALKTHROUGH.md).
