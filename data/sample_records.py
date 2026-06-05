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
    # R017 — REASON: CO-OCCURRENCE baseline. Two items share the SAME date on two
    # distinct dates -> the pairing itself recurs -> co-occurrence flags (count 2).
    # Each item also recurs 2x, so recurrence surfaces both (one record, two
    # lenses); 35-day gaps and no 3-in-30 burst keep gap/frequency silent.
    {
        "id": "R017",
        "entries": [
            {"date": "2026-01-10", "item": "knee pain"},
            {"date": "2026-01-10", "item": "poor sleep"},
            {"date": "2026-02-14", "item": "knee pain"},
            {"date": "2026-02-14", "item": "poor sleep"},
        ],
    },
    # R018 — REASON: pair combinatorics. THREE items co-occur on two shared dates;
    # exercises all three pairs (A-B, A-C, B-C) and deterministic pair ordering.
    {
        "id": "R018",
        "entries": [
            {"date": "2026-03-01", "item": "dizziness"},
            {"date": "2026-03-01", "item": "fatigue"},
            {"date": "2026-03-01", "item": "nausea"},
            {"date": "2026-04-01", "item": "dizziness"},
            {"date": "2026-04-01", "item": "fatigue"},
            {"date": "2026-04-01", "item": "nausea"},
        ],
    },
    # R019 — REASON: negative control. Both items recur, but on DIFFERENT dates --
    # they never share one. Proves co-occurrence is NOT just "both items recur".
    {
        "id": "R019",
        "entries": [
            {"date": "2026-01-05", "item": "cough"},
            {"date": "2026-02-05", "item": "cough"},
            {"date": "2026-01-20", "item": "rash"},
            {"date": "2026-02-20", "item": "rash"},
        ],
    },
    # R020 — REASON: threshold control. Two items share exactly ONE date -> the
    # pairing does NOT recur -> below min_count=2 -> co-occurrence does NOT flag.
    # Dates kept tight (max 69-day gap) so this isolates the co-occurrence
    # threshold without also tripping the gap rule.
    {
        "id": "R020",
        "entries": [
            {"date": "2026-01-12", "item": "edema"},
            {"date": "2026-01-12", "item": "back pain"},
            {"date": "2026-03-18", "item": "edema"},
            {"date": "2026-03-22", "item": "back pain"},
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
    # R017-R020 are the co-occurrence records; each shared-date item also recurs
    # 2x, so recurrence surfaces them here (the co-occurrence oracle is below).
    "R017": {
        "knee pain": ["2026-01-10", "2026-02-14"],
        "poor sleep": ["2026-01-10", "2026-02-14"],
    },
    "R018": {
        "dizziness": ["2026-03-01", "2026-04-01"],
        "fatigue": ["2026-03-01", "2026-04-01"],
        "nausea": ["2026-03-01", "2026-04-01"],
    },
    "R019": {
        "cough": ["2026-01-05", "2026-02-05"],
        "rash": ["2026-01-20", "2026-02-20"],
    },
    "R020": {
        "back pain": ["2026-01-12", "2026-03-22"],
        "edema": ["2026-01-12", "2026-03-18"],
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
    # R017-R020 carry no synonym/case/typo variants, so v1 grouping == v0 here.
    "R017": {
        "knee pain": ["2026-01-10", "2026-02-14"],
        "poor sleep": ["2026-01-10", "2026-02-14"],
    },
    "R018": {
        "dizziness": ["2026-03-01", "2026-04-01"],
        "fatigue": ["2026-03-01", "2026-04-01"],
        "nausea": ["2026-03-01", "2026-04-01"],
    },
    "R019": {
        "cough": ["2026-01-05", "2026-02-05"],
        "rash": ["2026-01-20", "2026-02-20"],
    },
    "R020": {
        "back pain": ["2026-01-12", "2026-03-22"],
        "edema": ["2026-01-12", "2026-03-18"],
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

# CO-OCCURRENCE: two distinct items sharing the SAME date on >= min_count (2)
# distinct dates; the pairing itself must recur. Undated entries are excluded
# (no date to share). Pairs are listed in sorted-item order, dates sorted.
# Across these records: R017 (one pair) and R018 (three pairs). R019 (items
# recur but never share a date) and R020 (share exactly one date) deliberately
# surface NOTHING — the two negative controls that prove co-occurrence is more
# than "both items recur". Format:
#   {record_id: [(item_a, item_b, count, [shared_dates]), ...]}
#
#   python recurrence.py --demo-cooccurrence
CO_OCCURRENCE_ANSWER_KEY: dict = {
    "R017": [
        ("knee pain", "poor sleep", 2, ["2026-01-10", "2026-02-14"]),
    ],
    "R018": [
        ("dizziness", "fatigue", 2, ["2026-03-01", "2026-04-01"]),
        ("dizziness", "nausea", 2, ["2026-03-01", "2026-04-01"]),
        ("fatigue", "nausea", 2, ["2026-03-01", "2026-04-01"]),
    ],
    # R019: both items recur but never share a date -> empty (no entry).
    # R020: items share exactly one date (< min_count 2) -> empty (no entry).
}


# ---------------------------------------------------------------------------
# Combined report — all rules, one per-record view
# ---------------------------------------------------------------------------
#
# run_report() routes all four rules over the SAME records and groups every
# hit by record. The answer key below is the hand-written oracle for that
# combined view: for each record that surfaces anything, the (expert, item)
# findings in EXACT render order — records by id, experts in registry order
# (recurrence, then gap, then frequency, then cooccurrence), hits within a rule
# in that rule's own order. Dates/counts are already oracled by the keys above;
# this key states only WHICH lens surfaced WHICH item, so the views can never
# silently diverge. Composed by hand from the keys above; run_report reproduces it.
# A cooccurrence finding's item is the pair label "item_a + item_b".
#
#   python recurrence.py --report
#
# Records that surface nothing at v0 defaults (R003, R006, R007, R014) are
# ABSENT by design: the report lists what is present, never asserts "clean".
# Records that prove the combined view's worth — one dataset, several lenses:
#   R015 = recurrence + gap                R016 = recurrence + frequency
#   R017 = recurrence x2 + cooccurrence    R018 = recurrence x3 + cooccurrence x3
REPORT_ANSWER_KEY: dict = {
    "R001": [("recurrence", "poor sleep")],
    "R002": [("recurrence", "appetite change"), ("recurrence", "fatigue")],
    "R004": [("recurrence", "back pain")],
    "R005": [("recurrence", "anxiety")],
    "R008": [("recurrence", "medication review")],
    "R009": [("recurrence", "med refill: metformin")],
    "R010": [("recurrence", "edema")],
    "R011": [("recurrence", "lab: A1C")],
    "R012": [("recurrence", "blood pressure elevated")],
    "R013": [("recurrence", "housing instability")],
    "R015": [("recurrence", "depression"), ("gap", "depression")],
    "R016": [
        ("recurrence", "chest pain"),
        ("frequency", "chest pain"),
        ("cadence_change", "chest pain"),
    ],
    "R017": [
        ("recurrence", "knee pain"),
        ("recurrence", "poor sleep"),
        ("cooccurrence", "knee pain + poor sleep"),
    ],
    "R018": [
        ("recurrence", "dizziness"),
        ("recurrence", "fatigue"),
        ("recurrence", "nausea"),
        ("cooccurrence", "dizziness + fatigue"),
        ("cooccurrence", "dizziness + nausea"),
        ("cooccurrence", "fatigue + nausea"),
    ],
    "R019": [("recurrence", "cough"), ("recurrence", "rash")],
    "R020": [("recurrence", "back pain"), ("recurrence", "edema")],
}


# The v1 combined report: run_report with the same opt-in matching as --demo-v1
# (normalize + SYNONYMS + fuzzy_cutoff=0.85). Identical to REPORT_ANSWER_KEY
# EXCEPT the three records that only merge under v1 now surface a recurrence
# line: R006 (synonyms), R007 (normalize), R014 (fuzzy typo). Gap/frequency and
# the co-occurrence records are unchanged (R017-R020 carry no variants). R003
# still surfaces nothing. Written by hand first; run_report must reproduce it.
#
#   python recurrence.py --report-v1
REPORT_ANSWER_KEY_V1: dict = {
    "R001": [("recurrence", "poor sleep")],
    "R002": [("recurrence", "appetite change"), ("recurrence", "fatigue")],
    "R004": [("recurrence", "back pain")],
    "R005": [("recurrence", "anxiety")],
    "R006": [("recurrence", "poor sleep")],          # v1: synonyms merge
    "R007": [("recurrence", "Hypertension")],         # v1: normalize merges case/space
    "R008": [("recurrence", "medication review")],
    "R009": [("recurrence", "med refill: metformin")],
    "R010": [("recurrence", "edema")],
    "R011": [("recurrence", "lab: A1C")],
    "R012": [("recurrence", "blood pressure elevated")],
    "R013": [("recurrence", "housing instability")],
    "R014": [("recurrence", "blood pressure")],        # v1: fuzzy merges the typo
    "R015": [("recurrence", "depression"), ("gap", "depression")],
    "R016": [
        ("recurrence", "chest pain"),
        ("frequency", "chest pain"),
        ("cadence_change", "chest pain"),
    ],
    "R017": [
        ("recurrence", "knee pain"),
        ("recurrence", "poor sleep"),
        ("cooccurrence", "knee pain + poor sleep"),
    ],
    "R018": [
        ("recurrence", "dizziness"),
        ("recurrence", "fatigue"),
        ("recurrence", "nausea"),
        ("cooccurrence", "dizziness + fatigue"),
        ("cooccurrence", "dizziness + nausea"),
        ("cooccurrence", "fatigue + nausea"),
    ],
    "R019": [("recurrence", "cough"), ("recurrence", "rash")],
    "R020": [("recurrence", "back pain"), ("recurrence", "edema")],
}


# ---------------------------------------------------------------------------
# Cadence-change rule (#5) — a dedicated record set + hand-written oracle.
# ---------------------------------------------------------------------------
#
# Kept SEPARATE from SAMPLE_RECORDS so the new rule's MatchesAnswerKey test does
# not ripple the other per-rule keys (recurrence / gap / frequency / report).
# The rule still runs over SAMPLE_RECORDS in --report (where R016's real
# 10d -> 79d shift surfaces); these records isolate the cadence behaviour with
# clean intervals so the oracle can be read by eye.
CADENCE_CHANGE_RECORDS: list[dict] = [
    # RC1 — clean tightening: ~30-day (monthly) spacing then ~7-day (weekly).
    # Intervals [30, 30, 30, 7, 7, 7]; the single change point is the 4th visit
    # (2026-04-01), where the weekly cadence begins.
    {
        "id": "RC1",
        "entries": [
            {"date": "2026-01-01", "item": "insulin"},
            {"date": "2026-01-31", "item": "insulin"},
            {"date": "2026-03-02", "item": "insulin"},
            {"date": "2026-04-01", "item": "insulin"},
            {"date": "2026-04-08", "item": "insulin"},
            {"date": "2026-04-15", "item": "insulin"},
            {"date": "2026-04-22", "item": "insulin"},
        ],
    },
    # RC2 — steady-cadence negative control: ~monthly throughout, no shift.
    {
        "id": "RC2",
        "entries": [
            {"date": "2026-01-05", "item": "checkup"},
            {"date": "2026-02-05", "item": "checkup"},
            {"date": "2026-03-05", "item": "checkup"},
            {"date": "2026-04-05", "item": "checkup"},
            {"date": "2026-05-05", "item": "checkup"},
            {"date": "2026-06-05", "item": "checkup"},
        ],
    },
    # RC3 — too-few control: 3 dated occurrences (< min_occurrences=4) plus an
    # undated one (excluded), so the interval series is never long enough to flag.
    {
        "id": "RC3",
        "entries": [
            {"date": "2026-01-01", "item": "review"},
            {"item": "review"},  # undated -> excluded
            {"date": "2026-02-01", "item": "review"},
            {"date": "2026-05-01", "item": "review"},
        ],
    },
]

# Hand-written oracle for detect_cadence_change(CADENCE_CHANGE_RECORDS). Only RC1
# flags: median interval ~30d -> ~7d (ratio ~4.3) at the 2026-04-01 pivot. RC2
# (steady) and RC3 (too few dated days) surface nothing. Per record the shape is
# (item, before_interval, after_interval, pivot_date, [every dated day]).
CADENCE_CHANGE_ANSWER_KEY: dict = {
    "RC1": [
        (
            "insulin",
            30,
            7,
            "2026-04-01",
            [
                "2026-01-01", "2026-01-31", "2026-03-02", "2026-04-01",
                "2026-04-08", "2026-04-15", "2026-04-22",
            ],
        ),
    ],
    # RC2: steady ~monthly -> no flag. RC3: too few dated days -> no flag.
}


# ---------------------------------------------------------------------------
# Free-text extraction front-end (extract.py, slice 1) — sample note +
# gazetteer + hand-written oracle. Lives here, with every other answer key, so
# the oracle is data written ONCE by hand and the test asserts agreement.
#
# extract.py is a FRONT-END: these records are its expected OUTPUT, then fed to
# the SAME five rules unchanged. Stance A (strict literal): every exact, word-
# bounded, longest-match gazetteer hit on a dated line becomes an entry, with NO
# negation/context judgment ("chest pain" surfaces from "Denies chest pain").
#
# source_span values are CHARACTER OFFSETS INTO THE WHOLE NOTE (end exclusive),
# hand-verified against the literal FREETEXT_SAMPLE_NOTE below (total length 191,
# trailing newline included). The note literal and these offsets are two
# statements of one truth; if either drifts, tests/test_extract.py fails.
# ---------------------------------------------------------------------------
FREETEXT_SAMPLE_NOTE: str = (
    "Patient: EXAMPLE-001\n"
    "\n"
    "2026-01-05 Reports poor sleep x3 weeks. Denies chest pain.\n"
    "2026-02-10 Poor sleep continues. Headache today.\n"
    "2026-03-12 Sleep improved. Notes family history of insomnia.\n"
)

# Curated, domain-agnostic gazetteer for the sample. "poor sleep" and "sleep"
# overlap on purpose, to exercise longest-match (poor sleep wins over sleep).
FREETEXT_GAZETTEER: list[str] = [
    "poor sleep",
    "sleep",
    "chest pain",
    "headache",
    "insomnia",
]

# The hand-written answer key: one record (id from the "Patient:" header) whose
# entries are every gazetteer hit on a dated line, in document order. Items carry
# the gazetteer's canonical spelling (so "Poor sleep" groups with "poor sleep").
FREETEXT_EXPECTED_RECORDS: list[dict] = [
    {
        "id": "EXAMPLE-001",
        "entries": [
            {"date": "2026-01-05", "item": "poor sleep", "source_span": [41, 51]},
            # "chest pain" surfaces despite "Denies" — Stance A carries no cue logic.
            {"date": "2026-01-05", "item": "chest pain", "source_span": [69, 79]},
            {"date": "2026-02-10", "item": "poor sleep", "source_span": [92, 102]},
            {"date": "2026-02-10", "item": "headache", "source_span": [114, 122]},
            {"date": "2026-03-12", "item": "sleep", "source_span": [141, 146]},
            # "insomnia" surfaces despite "family history of" — Stance A.
            {"date": "2026-03-12", "item": "insomnia", "source_span": [181, 189]},
        ],
    },
]

# ---------------------------------------------------------------------------
# Slice 2 (ADR 0012) — matching-mode fixtures (illustrative + minimal; real
# deployments supply their own vetted vocabulary). The synonyms-mode oracle
# reuses the SAME note and the SAME hand-verified spans as strict; only the
# emitted item changes where a synonym applies. Here the literal "insomnia"
# mention (itself a gazetteer term) is remapped to its canonical "poor sleep",
# so the span [181, 189] now emits "poor sleep" and detect_recurrence surfaces
# "poor sleep" 3x instead of 2x. The pairing is directional (variant ->
# canonical), same-concept, and human-vetted (an affix-antonym pairing would be
# refused by extract._validate_synonyms).
# ---------------------------------------------------------------------------
FREETEXT_SYNONYMS: dict = {"insomnia": "poor sleep"}

FREETEXT_EXPECTED_RECORDS_SYNONYMS: list[dict] = [
    {
        "id": "EXAMPLE-001",
        "entries": [
            {"date": "2026-01-05", "item": "poor sleep", "source_span": [41, 51]},
            {"date": "2026-01-05", "item": "chest pain", "source_span": [69, 79]},
            {"date": "2026-02-10", "item": "poor sleep", "source_span": [92, 102]},
            {"date": "2026-02-10", "item": "headache", "source_span": [114, 122]},
            {"date": "2026-03-12", "item": "sleep", "source_span": [141, 146]},
            # "insomnia" -> canonical "poor sleep" (synonyms mode remap).
            {"date": "2026-03-12", "item": "poor sleep", "source_span": [181, 189]},
        ],
    },
]
