# Placeholder records — design, field dictionary, and answer key

This document explains **why every record and field in `data/sample_records.py`
exists**. It is the prose companion to that module: the module holds the data
and the answer key; this file holds the reasons. Nothing here is filler — each
record exercises one distinct behavior of `detect_recurrence`, and each field
is justified against a real 2026 health-data standard or deliberately excluded.

All data is invented. **Zero real PHI.**

---

## 1. What this dataset is for

`detect_recurrence` is a *librarian*: it surfaces, counts, and cites items that
recur across dated entries in a record — it never interprets, scores, or
diagnoses. To trust it, we need data whose correct answer is known **before** the
code runs. The author (the oracle) writes the answer key by hand in
`ANSWER_KEY`; `tests/test_sample_records.py` then asserts the engine reproduces
it exactly — no extra hits, no missing hits. If the data and the key ever drift
apart (a typo on either side), the test fails. That is the whole safety model:
two independent statements of the truth that must agree.

---

## 2. Record shape and field dictionary

```python
record = {
    "id": "R001",
    "entries": [
        {"date": "2026-01-10", "item": "poor sleep", "tag": "encounter:telehealth"},
        ...
    ],
}
```

| Field | Required | Reason it exists | Real-world anchor (2026) |
|---|---|---|---|
| `id` | yes | Provenance root — every surfaced hit cites which record it came from. | — |
| `entries[].date` | per entry | The onset/observation date. The engine groups occurrences and cites these dates as provenance. Missing dates are tolerated. | USCDI **"Problems → Onset Date"**: the approximate date a condition began, independent of when it was recorded. |
| `entries[].item` | per entry | The text the recurrence expert scans. Domain-agnostic: a problem, a medication, a lab/test, or a social factor. | USCDI **Problems**; also Medications, Laboratory, and SDOH data classes. |
| `entries[].tag` | optional | A category / encounter type. **Carried but ignored by the v0 recurrence expert** — reserved so a later router/config can dispatch on it without reshaping the data. | USCDI **"Encounter → Encounter Type"**. |

### Fields deliberately **excluded** from v0 (also a reason)

Real longitudinal records carry far more. We leave these out on purpose:

- **Demographics, free-text clinical notes, lab *values*, medication doses** —
  not needed to detect *that* an item recurs, and pulling them in invites
  interpretation, which the spec's firewall forbids in v0.
- **Author / source-system of each entry (full provenance chain)** — useful
  later, but v0 provenance is "which record + which dates," which is enough to
  trace any hit. Adding more now would be unjustified scope.

Excluding them keeps v0 minimal, exact, and verifiable — and keeps the data
shape ready to *gain* these fields later without a rewrite.

---

## 3. The records — one reason each

Run `python recurrence.py --demo` to see the surfaced lines. Default rule:
flag an item appearing in **2+** entries of a record, matched **exactly**.

| Record | Reason it exists | Expected to surface |
|---|---|---|
| **R001** | Baseline 3× recurrence; a one-off item must not flag. | `poor sleep` ×3 |
| **R002** | Two distinct items each recur; both flag independently. | `appetite change` ×2, `fatigue` ×2 |
| **R003** | Nothing recurs — proves zero false positives. | *(nothing)* |
| **R004** | Exactly at threshold (2×); a one-off must not flag. | `back pain` ×2 |
| **R005** | Higher count (4×) proves counting beyond the threshold. | `anxiety` ×4 |
| **R006** | **v0 exact-match limitation** — three synonyms, each once, do not merge. | *(nothing)* |
| **R007** | **Literal matching** — case and trailing-space variants are distinct. | *(nothing)* |
| **R008** | Optional `tag` carried but ignored; item flags across differing tags. | `medication review` ×2 |
| **R009** | An undated occurrence is handled; the hit still surfaces, gap shown as `(undated)`. | `med refill: metformin` ×3 |
| **R010** | Dirty data (null/missing/non-dict entries) skipped without crashing; real signal survives. | `edema` ×2 |
| **R011** | The care-coordination payoff: a duplicated test (same lab ×3). | `lab: A1C` ×3 |
| **R012** | Dense longitudinal record; one item recurs monthly across a year (12×) amid noise. | `blood pressure elevated` ×12 |
| **R013** | Domain-agnostic proof: the item is an SDOH factor, not a symptom. | `housing instability` ×2 |

### Cross-record independence (no dedicated record needed)

`poor sleep` appears in **R001** (×3, flags) and in **R006** (×1, does not flag).
That pair proves recurrence is scoped **within a single record** — the engine
never aggregates an item across different records. Asserted in
`tests/test_sample_records.py::test_no_cross_record_merge`.

---

## 4. v0 limitations demonstrated by this data

These are **known, documented limitations**, not defects. Each has a live
example so the oracle can see exactly where the boundary is:

- **No synonym/semantic matching** (R006): "poor sleep" / "insomnia" /
  "can't sleep" are three different items in v0. Deferred to v1 (fuzzy matching).
- **No normalization** (R007): "Hypertension" ≠ "hypertension" ≠ "hypertension ".
  Case-folding and trimming are v1 candidates.
- **Provenance gaps surface, they don't vanish** (R009): an undated occurrence
  is counted and rendered `(undated)` — a data-quality flag, not interpretation.

---

## 5. How to verify (you and the engine, independently)

```bash
python recurrence.py --demo                       # what the engine surfaces
python -m unittest discover -s tests -t .          # answer key vs engine, exact
```

`tests/test_sample_records.py` reshapes the engine output to
`{record_id: {item: [dates]}}` and asserts it equals `ANSWER_KEY` (dropping the
empty-dict records, which must emit nothing). Read the table in §3, eyeball the
`--demo` output, and the unit test guarantees they can't silently disagree.

---

## 6. Sources (what 2026 records actually carry)

- USCDI **Problems** data class (incl. Onset Date) — ONC Interoperability Standards Platform: https://www.healthit.gov/isp/uscdi-data-class/problems
- USCDI v5 (encounter elements: Encounter Type, Encounter Diagnosis, Encounter Time) — ONC: https://www.healthit.gov/isp/sites/isp/files/2024-07/USCDI-Version-5-July-2024-Final.pdf
- Draft USCDI v7 (Jan 2026) — ONC: https://isp.healthit.gov/sites/default/files/2026-01/Draft-USCDI-Version-7-January-2026.pdf
- Social determinants of health categories in records — *Recording of Social Determinants in Computerized Medical Records*, PMC: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10013680/
- Care-coordination context elements & duplicated-test/journey gaps — *Digital Information Ecosystems in Modern Care Coordination*, JMIR (2024): https://www.jmir.org/2024/1/e60258
