"""
sample_records.py — placeholder record set for the recurrence engine.
=====================================================================

ZERO real PHI. Every record here is invented. The author is the oracle: the
ANSWER_KEY is written by hand FIRST (what *should* surface), then the engine
runs and must match it exactly — never patch the key toward the code.
tests/test_sample_records.py enforces that agreement.

Full design rationale, field dictionary (grounded in 2026 interoperability
standards), per-record reasons, and the limitations each record demonstrates
live in data/RECORDS.md. This module is the data + the answer key; RECORDS.md
is the prose. Read them together.

Record shape (domain-agnostic):

    record = {
        "id": "R001",
        "entries": [
            {"date": "2026-01-10", "item": "poor sleep", "tag": "..."},
            ...
        ],
    }

  - "date" — ISO 8601, the entry's onset/observation date (USCDI Problems
    "Onset Date"). The engine groups occurrences and cites these for provenance.
  - "item" — the text the recurrence expert scans (a problem, a med, a test,
    an SDOH factor — anything). Default scanned field.
  - "tag" — OPTIONAL category/encounter type (USCDI "Encounter Type"). Carried
    for future routing/config; the v0 recurrence expert ignores it.

Default rule: an item flags when it appears in 2+ entries of one record
(min_count = 2), matched EXACTLY (case-sensitive, no trimming, no synonyms).

  python recurrence.py --demo   # surface recurrences across SAMPLE_RECORDS
"""

from __future__ import annotations

# Each record below exists for exactly ONE reason, stated in its comment. No
# record is filler; remove a record only if its reason is also removed.
SAMPLE_RECORDS: list[dict] = [
    # R001 — REASON: baseline 3x recurrence; a one-off item must NOT flag.
    {
        "id": "R001",
        "entries": [
            {"date": "2026-01-05", "item": "poor sleep"},
            {"date": "2026-02-10", "item": "poor sleep"},
            {"date": "2026-03-12", "item": "poor sleep"},
            {"date": "2026-01-20", "item": "headache"},
        ],
    },
    # R002 — REASON: two distinct items each recur; both flag independently.
    {
        "id": "R002",
        "entries": [
            {"date": "2026-01-08", "item": "appetite change"},
            {"date": "2026-02-15", "item": "appetite change"},
            {"date": "2026-02-02", "item": "fatigue"},
            {"date": "2026-03-01", "item": "fatigue"},
        ],
    },
    # R003 — REASON: nothing recurs; clean record proves zero false positives.
    {
        "id": "R003",
        "entries": [
            {"date": "2026-01-10", "item": "cough"},
            {"date": "2026-02-05", "item": "rash"},
            {"date": "2026-03-09", "item": "dizziness"},
        ],
    },
    # R004 — REASON: exactly-at-threshold (2x) recurrence; a one-off must NOT flag.
    {
        "id": "R004",
        "entries": [
            {"date": "2026-01-15", "item": "back pain"},
            {"date": "2026-02-20", "item": "back pain"},
            {"date": "2026-03-25", "item": "nausea"},
        ],
    },
    # R005 — REASON: higher count (4x) proves counting beyond the threshold.
    {
        "id": "R005",
        "entries": [
            {"date": "2026-01-03", "item": "anxiety"},
            {"date": "2026-01-31", "item": "anxiety"},
            {"date": "2026-02-28", "item": "anxiety"},
            {"date": "2026-03-30", "item": "anxiety"},
            {"date": "2026-02-14", "item": "chest tightness"},
        ],
    },
    # R006 — REASON: v0 EXACT-MATCH LIMITATION. Three synonyms for one concept,
    # each once -> engine does NOT flag. This is the v1 fuzzy-match case, shown
    # live as a known limitation, not a bug.
    {
        "id": "R006",
        "entries": [
            {"date": "2026-01-09", "item": "poor sleep"},
            {"date": "2026-02-11", "item": "insomnia"},
            {"date": "2026-03-14", "item": "can't sleep"},
        ],
    },
    # R007 — REASON: matching is LITERAL. Case and trailing whitespace make
    # distinct items -> each appears once -> no flag. Documents that v0 does no
    # normalization (a v1 candidate).
    {
        "id": "R007",
        "entries": [
            {"date": "2026-01-12", "item": "Hypertension"},
            {"date": "2026-02-12", "item": "hypertension"},
            {"date": "2026-03-12", "item": "hypertension "},
        ],
    },
    # R008 — REASON: optional "tag" (encounter type) is carried but IGNORED by
    # the recurrence expert; the item still flags across differing tags.
    {
        "id": "R008",
        "entries": [
            {"date": "2026-01-18", "item": "medication review", "tag": "encounter:telehealth"},
            {"date": "2026-02-22", "item": "medication review", "tag": "encounter:in-person"},
            {"date": "2026-03-05", "item": "blood pressure check", "tag": "encounter:telehealth"},
        ],
    },
    # R009 — REASON: an undated occurrence (missing onset date, common in real
    # records) is handled gracefully; the hit still surfaces and the gap shows
    # as "(undated)" in provenance rather than being hidden.
    {
        "id": "R009",
        "entries": [
            {"date": "2026-01-07", "item": "med refill: metformin"},
            {"item": "med refill: metformin"},  # no date
            {"date": "2026-03-09", "item": "med refill: metformin"},
        ],
    },
    # R010 — REASON: dirty data. None items, missing-field entries, and a
    # non-dict entry are all skipped without crashing, and the real 2x signal
    # still surfaces from the noise.
    {
        "id": "R010",
        "entries": [
            {"date": "2026-01-11", "item": "edema"},
            {"date": "2026-01-15"},                       # no item -> skipped
            {"date": "2026-02-11", "item": None},          # null item -> skipped
            {"date": "2026-02-13", "item": "edema"},
            "ignore-me-not-a-dict",                        # wrong type -> skipped
        ],
    },
    # R011 — REASON: the care-coordination payoff. The same lab ordered 3x is
    # the duplicated-test / failure-to-follow-up signal recurrence surfacing is
    # meant to expose.
    {
        "id": "R011",
        "entries": [
            {"date": "2026-01-06", "item": "lab: A1C"},
            {"date": "2026-02-09", "item": "lab: A1C"},
            {"date": "2026-03-20", "item": "lab: A1C"},
        ],
    },
    # R012 — REASON: dense longitudinal record. One item recurs monthly across a
    # full year (12x) amid one-off noise; proves counting and provenance scale.
    {
        "id": "R012",
        "entries": [
            {"date": "2026-01-04", "item": "blood pressure elevated"},
            {"date": "2026-02-04", "item": "blood pressure elevated"},
            {"date": "2026-03-04", "item": "blood pressure elevated"},
            {"date": "2026-04-04", "item": "blood pressure elevated"},
            {"date": "2026-05-04", "item": "blood pressure elevated"},
            {"date": "2026-06-04", "item": "blood pressure elevated"},
            {"date": "2026-06-20", "item": "knee pain"},
            {"date": "2026-07-04", "item": "blood pressure elevated"},
            {"date": "2026-08-04", "item": "blood pressure elevated"},
            {"date": "2026-09-04", "item": "blood pressure elevated"},
            {"date": "2026-10-04", "item": "blood pressure elevated"},
            {"date": "2026-10-15", "item": "flu shot"},
            {"date": "2026-11-04", "item": "blood pressure elevated"},
            {"date": "2026-12-04", "item": "blood pressure elevated"},
        ],
    },
    # R013 — REASON: domain-agnostic proof. The item is a social determinant of
    # health (not a symptom); recurrence detection works identically.
    {
        "id": "R013",
        "entries": [
            {"date": "2026-01-22", "item": "housing instability"},
            {"date": "2026-02-26", "item": "housing instability"},
            {"date": "2026-03-30", "item": "food insecurity"},
        ],
    },
    # R014 — REASON: v1 fuzzy/typo demo. One concept written three ways (a typo
    # and a casing difference). v0 exact-match surfaces NOTHING; v1 with
    # normalize + fuzzy merges all three. The data is the v0->v1 contrast.
    {
        "id": "R014",
        "entries": [
            {"date": "2026-01-05", "item": "blood pressure"},
            {"date": "2026-02-05", "item": "blood presure"},   # typo
            {"date": "2026-03-05", "item": "Blood Pressure"},  # casing
        ],
    },
    # R015 — REASON: GAP / re-emergence demo. "depression" appears, goes quiet
    # for 243 days, then returns. The recurrence rule sees 3 occurrences; the gap
    # rule additionally surfaces the long absence-then-return. Same record, two
    # lenses.
    {
        "id": "R015",
        "entries": [
            {"date": "2026-01-10", "item": "depression"},
            {"date": "2026-09-10", "item": "depression"},
            {"date": "2026-10-05", "item": "depression"},
        ],
    },
    # R016 — REASON: FREQUENCY / burst demo. "chest pain" clusters 3x within 19
    # days, then an isolated visit 79 days later. The frequency rule surfaces the
    # burst; recurrence sees 4 total; no gap (79 < 90).
    {
        "id": "R016",
        "entries": [
            {"date": "2026-02-01", "item": "chest pain"},
            {"date": "2026-02-10", "item": "chest pain"},
            {"date": "2026-02-20", "item": "chest pain"},
            {"date": "2026-05-10", "item": "chest pain"},
        ],
    },
]

# The hand-written answer key (oracle): for each record, the items that SHOULD
# surface at min_count = 2, mapped to the exact dates the engine cites
# (chronological; an undated occurrence is "" and sorts first). Records with no
# expected hit are listed with an empty dict for completeness.
ANSWER_KEY: dict = {
    "R001": {"poor sleep": ["2026-01-05", "2026-02-10", "2026-03-12"]},
    "R002": {
        "appetite change": ["2026-01-08", "2026-02-15"],
        "fatigue": ["2026-02-02", "2026-03-01"],
    },
    "R003": {},
    "R004": {"back pain": ["2026-01-15", "2026-02-20"]},
    "R005": {"anxiety": ["2026-01-03", "2026-01-31", "2026-02-28", "2026-03-30"]},
    "R006": {},  # exact-match limitation: synonyms do not merge
    "R007": {},  # literal matching: case/whitespace variants do not merge
    "R008": {"medication review": ["2026-01-18", "2026-02-22"]},
    "R009": {"med refill: metformin": ["", "2026-01-07", "2026-03-09"]},
    "R010": {"edema": ["2026-01-11", "2026-02-13"]},
    "R011": {"lab: A1C": ["2026-01-06", "2026-02-09", "2026-03-20"]},
    "R012": {
        "blood pressure elevated": [
            "2026-01-04", "2026-02-04", "2026-03-04", "2026-04-04",
            "2026-05-04", "2026-06-04", "2026-07-04", "2026-08-04",
            "2026-09-04", "2026-10-04", "2026-11-04", "2026-12-04",
        ]
    },
    "R013": {"housing instability": ["2026-01-22", "2026-02-26"]},
    "R014": {},  # v0 exact-match: typo + casing variants do not merge
    "R015": {"depression": ["2026-01-10", "2026-09-10", "2026-10-05"]},
    "R016": {
        "chest pain": ["2026-02-01", "2026-02-10", "2026-02-20", "2026-05-10"]
    },
}


# ---------------------------------------------------------------------------
# v1 layer — opt-in matching (normalize + declared synonyms + fuzzy)
# ---------------------------------------------------------------------------
#
# These are NOT used by default. They demonstrate v1's opt-in matching on the
# SAME records, so the v0 -> v1 difference is visible on one dataset:
#
#   detect_recurrence(SAMPLE_RECORDS, normalize=True, synonyms=SYNONYMS,
#                     fuzzy_cutoff=0.85)
#
# Run it with:  python recurrence.py --demo-v1

# Declared synonyms (the oracle's data, never inferred by the engine). Maps a
# variant to its canonical concept. Resolves R006's true synonyms — the case no
# string-similarity could catch, because the words share no letters.
SYNONYMS: dict = {
    "insomnia": "poor sleep",
    "can't sleep": "poor sleep",
}

# The v1 answer key: what SHOULD surface with normalize + SYNONYMS +
# fuzzy_cutoff=0.85. Written by hand first; the engine must reproduce it.
# Differences from ANSWER_KEY (v0) are exactly the three new merges:
#   R006 (synonyms), R007 (normalize), R014 (normalize + fuzzy typo).
ANSWER_KEY_V1: dict = {
    "R001": {"poor sleep": ["2026-01-05", "2026-02-10", "2026-03-12"]},
    "R002": {
        "appetite change": ["2026-01-08", "2026-02-15"],
        "fatigue": ["2026-02-02", "2026-03-01"],
    },
    "R003": {},
    "R004": {"back pain": ["2026-01-15", "2026-02-20"]},
    "R005": {"anxiety": ["2026-01-03", "2026-01-31", "2026-02-28", "2026-03-30"]},
    "R006": {"poor sleep": ["2026-01-09", "2026-02-11", "2026-03-14"]},  # synonyms
    "R007": {"Hypertension": ["2026-01-12", "2026-02-12", "2026-03-12"]},  # normalize
    "R008": {"medication review": ["2026-01-18", "2026-02-22"]},
    "R009": {"med refill: metformin": ["", "2026-01-07", "2026-03-09"]},
    "R010": {"edema": ["2026-01-11", "2026-02-13"]},
    "R011": {"lab: A1C": ["2026-01-06", "2026-02-09", "2026-03-20"]},
    "R012": {
        "blood pressure elevated": [
            "2026-01-04", "2026-02-04", "2026-03-04", "2026-04-04",
            "2026-05-04", "2026-06-04", "2026-07-04", "2026-08-04",
            "2026-09-04", "2026-10-04", "2026-11-04", "2026-12-04",
        ]
    },
    "R013": {"housing instability": ["2026-01-22", "2026-02-26"]},
    "R014": {"blood pressure": ["2026-01-05", "2026-02-05", "2026-03-05"]},  # fuzzy
    "R015": {"depression": ["2026-01-10", "2026-09-10", "2026-10-05"]},
    "R016": {
        "chest pain": ["2026-02-01", "2026-02-10", "2026-02-20", "2026-05-10"]
    },
}


# ---------------------------------------------------------------------------
# Second/third rules — gap (re-emergence) and frequency (burst)
# ---------------------------------------------------------------------------
#
# Additional surfacing rules over the SAME records. detect_gap and
# detect_frequency read the same grouped occurrences as recurrence, so one
# dataset is viewed through several lenses. The answer keys below are the
# hand-written expected output at the documented default parameters:
#
#   detect_gap(SAMPLE_RECORDS, gap_days=90)
#   detect_frequency(SAMPLE_RECORDS, window_days=30, min_count=3)
#
#   python recurrence.py --demo-gap
#   python recurrence.py --demo-frequency

# GAP: an item returns after an absence of MORE than gap_days. Across these
# records only R015 qualifies (depression: 243-day quiet stretch). Format:
#   {record_id: [(item, gap_days, before_date, after_date), ...]}
GAP_ANSWER_KEY: dict = {
    "R015": [("depression", 243, "2026-01-10", "2026-09-10")],
}

# FREQUENCY: an item appears min_count+ times within any window_days span. Across
# these records only R016 qualifies (chest pain: 3x within 19 days). Format:
#   {record_id: [(item, count, window_start, window_end, [dates]), ...]}
FREQUENCY_ANSWER_KEY: dict = {
    "R016": [
        (
            "chest pain",
            3,
            "2026-02-01",
            "2026-02-20",
            ["2026-02-01", "2026-02-10", "2026-02-20"],
        )
    ],
}
