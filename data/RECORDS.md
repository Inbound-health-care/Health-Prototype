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
| **R014** | v1 fuzzy/typo demo: one concept written 3 ways (typo + casing). v0 surfaces nothing; v1 merges it. | *(nothing in v0)* |
| **R015** | Gap/re-emergence demo: returns after a 243-day absence (also recurs ×3). | `depression` ×3 |
| **R016** | Frequency/burst demo: 3× within 19 days, then isolated (also recurs ×4). | `chest pain` ×4 |

### Cross-record independence (no dedicated record needed)

`poor sleep` appears in **R001** (×3, flags) and in **R006** (×1, does not flag).
That pair proves recurrence is scoped **within a single record** — the engine
never aggregates an item across different records. Asserted in
`tests/test_sample_records.py::test_no_cross_record_merge`.

---

## 4. v0 boundaries — and how v1 (opt-in) addresses them

The v0 default is **exact match**. These boundaries each have a live example,
and v1's opt-in layers (see §5) now resolve the first three — without changing
the v0 default:

- **No synonym/semantic matching** (R006): "poor sleep" / "insomnia" /
  "can't sleep" are three different items by default → resolved by the declared
  `SYNONYMS` map in v1.
- **No normalization** (R007): "Hypertension" ≠ "hypertension" ≠ "hypertension "
  by default → resolved by `normalize=True` in v1.
- **Typos / near-duplicates** (R014): "blood pressure" ≠ "blood presure" by
  default → resolved by `fuzzy_cutoff` in v1.
- **Provenance gaps surface, they don't vanish** (R009): an undated occurrence
  is counted and rendered `(undated)` — a data-quality flag, not interpretation.
  (This is intended behavior at every version, not a limitation.)

---

## 5. v1 opt-in matching (normalize + declared synonyms + fuzzy)

v1 adds three matching layers to `detect_recurrence`. **All are opt-in** — the
defaults are still exact v0 matching, so nothing in §3's v0 answer key changes.
`SYNONYMS` and `ANSWER_KEY_V1` in `data/sample_records.py` demonstrate them on
the *same* records, so the v0→v1 difference is visible on one dataset:

```python
detect_recurrence(SAMPLE_RECORDS, normalize=True, synonyms=SYNONYMS, fuzzy_cutoff=0.85)
```
```bash
python recurrence.py --demo-v1
```

| Layer | Param | What it merges | Who decides equivalence |
|---|---|---|---|
| Normalize | `normalize=True` | case + whitespace ("Hypertension" = "hypertension ") | a fixed text rule, no judgment |
| Synonyms | `synonyms={…}` | declared synonyms ("insomnia" = "poor sleep") | **you / the oracle**, as data |
| Fuzzy | `fuzzy_cutoff=0.85` | lookalikes/typos ("blood presure" ≈ "blood pressure") | the engine, via stdlib difflib |

**Why a declared map for synonyms, not just fuzzy?** The spec's own example —
"insomnia" = "can't sleep" — shares no letters, so *no* string-similarity score
can unite them (their difflib ratio is far below any usable cutoff). Only a
declared dictionary can, and keeping it as *data you supply* means the engine is
applying your rule, not inferring meaning. Fuzzy is the one layer where the
engine groups on its own, so it is off by default.

### The firewall holds: every merge is cited

When v1 combines differently-spelled entries, the hit's `variants` lists every
original surface string, and `format_hit` appends them:

```text
Record R006: "poor sleep" recurred 3 times — 2026-01-09, 2026-02-11, 2026-03-14 [merged: "can't sleep", "insomnia", "poor sleep"]
```

The engine still only surfaces, counts, and cites — it now also **shows which
spellings it treated as the same**, so a human can audit (and overrule) any
merge. It never says what the recurrence *means*.

### v1 answer key

`ANSWER_KEY_V1` is the hand-written expected output under the call above. It
differs from the v0 key (§3) in exactly three records — the three new merges:
**R006** (synonyms), **R007** (normalize), **R014** (normalize + fuzzy typo).
`tests/test_fuzzy.py` asserts the engine reproduces it exactly, and that the
defaults still reproduce the v0 key (no regression).

---

## 6. How to verify (you and the engine, independently)

```bash
python recurrence.py --demo                        # recurrence, v0 exact match
python recurrence.py --demo-v1                      # recurrence, v1 opt-in matching
python recurrence.py --demo-gap                     # gap / re-emergence rule
python recurrence.py --demo-frequency               # frequency / burst rule
python -m unittest discover -s tests -t .           # all answer keys vs engine, exact
```

Each rule has a hand-written answer key and a test that asserts the engine
reproduces it exactly: `test_sample_records.py` → `ANSWER_KEY` (recurrence v0);
`test_fuzzy.py` → `ANSWER_KEY_V1` (and no regression of the v0 key);
`test_gap.py` → `GAP_ANSWER_KEY`; `test_frequency.py` → `FREQUENCY_ANSWER_KEY`.
Read the tables in §3, §5, and §7, eyeball the `--demo*` outputs, and the unit
tests guarantee they can't silently disagree.

---

## 7. Additional surfacing rules — gap and frequency

Recurrence answers "has this come up repeatedly?" Two more rules read the *same*
grouped occurrences (so they inherit the same exact/normalize/synonym/fuzzy
matching) and ask different questions. One dataset, several lenses — the same
record can surface under more than one rule.

| Rule | Function | Surfaces | Default params | Answer key |
|---|---|---|---|---|
| Gap / re-emergence | `detect_gap` | an item that **returns after a long absence** (> `gap_days`), citing the bracketing dates and gap length | `gap_days=90` | `GAP_ANSWER_KEY` |
| Frequency / burst | `detect_frequency` | an item appearing **`min_count`+ times within any `window_days` span**, citing the window's dates | `window_days=30, min_count=3` | `FREQUENCY_ANSWER_KEY` |

At the default parameters, across these records:

- **Gap** surfaces only **R015**: `depression` went quiet for 243 days, then
  returned (`2026-01-10` → `2026-09-10`). R016's largest gap is 79 days, below
  the 90-day threshold, so it does not surface.
- **Frequency** surfaces only **R016**: `chest pain` appeared 3× within 19 days
  (`2026-02-01` … `2026-02-20`). R015's occurrences never cluster 3× in 30 days.

Both rules stay strictly descriptive — they report *that* an item returned or
clustered, with dates, and never why or whether it matters. Undated occurrences
are skipped (a date-based rule never guesses a date), and merged spellings are
cited in `variants` exactly as in recurrence.

---

## 8. Sources (what 2026 records actually carry)

- USCDI **Problems** data class (incl. Onset Date) — ONC Interoperability Standards Platform: https://www.healthit.gov/isp/uscdi-data-class/problems
- USCDI v5 (encounter elements: Encounter Type, Encounter Diagnosis, Encounter Time) — ONC: https://www.healthit.gov/isp/sites/isp/files/2024-07/USCDI-Version-5-July-2024-Final.pdf
- Draft USCDI v7 (Jan 2026) — ONC: https://isp.healthit.gov/sites/default/files/2026-01/Draft-USCDI-Version-7-January-2026.pdf
- Social determinants of health categories in records — *Recording of Social Determinants in Computerized Medical Records*, PMC: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10013680/
- Care-coordination context elements & duplicated-test/journey gaps — *Digital Information Ecosystems in Modern Care Coordination*, JMIR (2024): https://www.jmir.org/2024/1/e60258
