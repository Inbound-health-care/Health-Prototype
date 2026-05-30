#!/usr/bin/env python3
"""
recurrence.py — Recurrence Detection Engine (Prototype v0)
==========================================================

Pure-stdlib. Zero external dependencies. Local-only (no network egress).

Given a set of records, surface every case where the same item appears across
multiple dated entries, and cite exactly where each occurrence came from.

This is a LIBRARIAN, not an interpreter. It surfaces, counts, and cites
provenance. It never scores, ranks, diagnoses, or says what a pattern *means*.
That separation is the design principle and the legal firewall in one.

Domain-agnostic by design: a record can be a patient, a pharmacy profile, a
session log — the engine does not care. v0 matches EXACTLY; fuzzy / synonym
matching (e.g. "can't sleep" == "insomnia") is deferred to v1.

  Self-test:  python recurrence.py --self-test
  Demo:       python recurrence.py --demo
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import sys
from collections import Counter
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Surfaced result — sourced, never interpreted
# ---------------------------------------------------------------------------


@dataclass
class RecurrenceHit:
    """One surfaced recurrence.

    Carries provenance only: which record, which item, how many times, and the
    exact dates it appeared on. No severity, no score, no interpretation.

    ``item`` is the label shown for the group. ``variants`` lists the distinct
    *original* surface strings that were combined into this hit — its length is
    1 for an exact (v0) hit, and >1 whenever normalization, a declared synonym,
    or fuzzy matching merged differently-spelled entries. variants is the audit
    trail: it makes every merge visible and checkable, never hidden.
    """

    record_id: str
    item: str
    count: int
    dates: list[str] = field(default_factory=list)
    variants: list[str] = field(default_factory=list)


@dataclass
class GapHit:
    """One surfaced re-emergence: an item returned after a long absence.

    Provenance only: the record, the item, the two bracketing dates, and the gap
    length in days. It reports that the item went quiet and came back — never
    why, and never that this is good or bad.
    """

    record_id: str
    item: str
    gap_days: int
    before_date: str
    after_date: str
    variants: list[str] = field(default_factory=list)


@dataclass
class FrequencyHit:
    """One surfaced burst: an item appeared many times in a short window.

    Provenance only: the record, the item, the count, the window's first/last
    dates, and every date in it. It reports density in time — not severity, not
    'worsening', not any judgment.
    """

    record_id: str
    item: str
    count: int
    window_start: str
    window_end: str
    dates: list[str] = field(default_factory=list)
    variants: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# The functions
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Canonicalize trivial spelling variation: trim, collapse internal
    whitespace, and case-fold. This is text canonicalization, not interpretation
    — it does not change meaning, only presentation."""
    return " ".join(text.split()).casefold()


def _build_synonym_map(synonyms: dict | None, normalize: bool) -> dict:
    """Return an effective {variant -> canonical} map keyed for lookup.

    Keys (and values) are run through the same normalizer as the items so a
    declared synonym matches regardless of case/spacing when ``normalize`` is on.
    """
    if not synonyms:
        return {}
    out: dict[str, str] = {}
    for variant, canonical in synonyms.items():
        key = _normalize(str(variant)) if normalize else str(variant)
        out[key] = _normalize(str(canonical)) if normalize else str(canonical)
    return out


def _canonical_key(item: str, synonym_map: dict, normalize: bool) -> str:
    """Reduce an original item string to its grouping key."""
    key = _normalize(item) if normalize else item
    return synonym_map.get(key, key)


def _pick_label(occ: list[tuple[str, str, int]]) -> str:
    """Choose the display label for a group: the most frequent original surface
    string, ties broken by earliest occurrence (date, then input order). The
    label is always a real string from the data; the full set is in ``variants``.
    """
    counts = Counter(o[1] for o in occ)
    best = max(counts.values())
    candidates = {original for original, n in counts.items() if n == best}
    chosen = min((o for o in occ if o[1] in candidates), key=lambda o: (o[0], o[2]))
    return chosen[1]


def _parse_date(date_str: str) -> datetime.date | None:
    """Parse an ISO 8601 date, or return None if absent/unparseable. The
    date-based rules (gap, frequency) simply skip occurrences they can't date —
    they never guess a date."""
    try:
        return datetime.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def _dated_sorted(occ: list[tuple[str, str, int]]) -> list[tuple[datetime.date, str]]:
    """From a group's occurrences, the datable ones as (date, date_str), sorted
    chronologically. Undated/unparseable occurrences are dropped."""
    dated = [(d, o[0]) for o in occ if (d := _parse_date(o[0])) is not None]
    return sorted(dated, key=lambda x: x[0])


def _fuzzy_clusters(keys: list[str], cutoff: float) -> dict[str, str]:
    """Greedily cluster near-duplicate keys; return {key -> representative}.

    Deterministic: keys are processed in sorted order, each joining the first
    existing cluster whose representative it resembles (difflib ratio >= cutoff)
    or starting a new one. Intended for lookalikes/typos, not transitive chains.
    """
    reps: list[str] = []
    mapping: dict[str, str] = {}
    for key in sorted(keys):
        match = None
        for rep in reps:
            if difflib.SequenceMatcher(None, key, rep).ratio() >= cutoff:
                match = rep
                break
        if match is None:
            reps.append(key)
            match = key
        mapping[key] = match
    return mapping


def _record_groups(
    record,
    field: str,
    synonym_map: dict,
    normalize: bool,
    fuzzy_cutoff: float | None,
) -> tuple[str, dict]:
    """Group one record's entries by canonical item key.

    Returns ``(record_id, groups)`` where ``groups`` maps a canonical key to a
    list of ``(date_str, original, index)`` occurrences, with optional fuzzy
    merging applied. Malformed records yield empty groups rather than raising.
    This is the shared core every surfacing rule reads from, so all rules see
    the same exact/normalize/synonym/fuzzy matching.
    """
    if not isinstance(record, dict):
        return "", {}
    record_id = str(record.get("id", ""))
    entries = record.get("entries")
    if not isinstance(entries, list):
        return record_id, {}

    groups: dict[str, list[tuple[str, str, int]]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        item = entry.get(field)
        # Skip entries with no usable item value (None, "", missing field).
        if item is None or item == "":
            continue
        original = str(item)
        key = _canonical_key(original, synonym_map, normalize)
        date = entry.get("date")
        date_str = "" if date is None else str(date)
        groups.setdefault(key, []).append((date_str, original, index))

    # Optionally fold near-duplicate keys together.
    if fuzzy_cutoff is not None and groups:
        rep_of = _fuzzy_clusters(list(groups), fuzzy_cutoff)
        merged: dict[str, list[tuple[str, str, int]]] = {}
        for key, occ in groups.items():
            merged.setdefault(rep_of[key], []).extend(occ)
        groups = merged

    return record_id, groups


def detect_recurrence(
    records: list,
    field: str = "item",
    min_count: int = 2,
    normalize: bool = False,
    synonyms: dict | None = None,
    fuzzy_cutoff: float | None = None,
) -> list[RecurrenceHit]:
    """Return a list of recurrence hits.

    Scan each record's entries. When the same item appears in ``min_count`` or
    more entries, emit a :class:`RecurrenceHit` citing the record id, the item
    label, the count, the dates (provenance), and the original variants that
    were combined. Surfaces only — no interpretation.

    Matching is layered and all extra layers are OPT-IN; with the defaults this
    is exact v0 behavior:

    - ``normalize=True`` — trim/collapse whitespace and case-fold before
      comparing (so "Hypertension" == "hypertension ").
    - ``synonyms={variant: canonical, ...}`` — merge declared synonyms (so
      "insomnia" == "poor sleep"). The mapping is data you supply, never
      inferred by the engine.
    - ``fuzzy_cutoff=0.0..1.0`` — also merge near-duplicate lookalikes/typos via
      stdlib difflib similarity at/above the cutoff. This is the one layer where
      the engine groups without a declared rule, so it is off by default; every
      merge it makes is still cited in ``variants``.

    Domain-agnostic and defensive: anything malformed (missing entries, a
    non-dict entry, a missing/empty item field, a missing date) is skipped
    rather than raising. Deterministic: hits are ordered by record then label,
    and dates within a hit are sorted (an undated occurrence is "" and sorts
    first).
    """
    hits: list[RecurrenceHit] = []
    if not records:
        return hits

    synonym_map = _build_synonym_map(synonyms, normalize)
    for record in records:
        record_id, groups = _record_groups(
            record, field, synonym_map, normalize, fuzzy_cutoff
        )
        for key in sorted(groups):
            occ = groups[key]
            if len(occ) < min_count:
                continue
            hits.append(
                RecurrenceHit(
                    record_id=record_id,
                    item=_pick_label(occ),
                    count=len(occ),
                    dates=sorted(o[0] for o in occ),
                    variants=sorted({o[1] for o in occ}),
                )
            )

    return hits


def format_hit(hit: RecurrenceHit) -> str:
    """Render a hit as a single provenance-cited line.

    Example:
      Record R001: "poor sleep" recurred 2 times — 2026-01-10, 2026-02-02

    An occurrence whose entry carried no date is stored as "" in ``hit.dates``
    and rendered here as "(undated)" — a visible data-quality marker, not an
    interpretation. It flags incomplete provenance rather than hiding it.
    """
    dates = ", ".join(d if d else "(undated)" for d in hit.dates)
    line = (
        f'Record {hit.record_id}: "{hit.item}" recurred {hit.count} times — {dates}'
    )
    # When more than one original spelling was combined, cite them all so the
    # merge is auditable — the librarian shows its work.
    if len(hit.variants) > 1:
        merged = ", ".join(f'"{v}"' for v in hit.variants)
        line += f" [merged: {merged}]"
    return line


def _merge_clause(variants: list[str]) -> str:
    if len(variants) > 1:
        return " [merged: " + ", ".join(f'"{v}"' for v in variants) + "]"
    return ""


# ---------------------------------------------------------------------------
# Second rule — gap / re-emergence
# ---------------------------------------------------------------------------


def detect_gap(
    records: list,
    field: str = "item",
    gap_days: int = 90,
    normalize: bool = False,
    synonyms: dict | None = None,
    fuzzy_cutoff: float | None = None,
) -> list[GapHit]:
    """Surface re-emergences: an item that appears, goes quiet for more than
    ``gap_days``, then appears again.

    For each item in a record, the engine sorts its dated occurrences and emits
    a :class:`GapHit` for every consecutive pair separated by more than
    ``gap_days`` days, citing the bracketing dates and the gap length. Undated
    occurrences are skipped (a gap needs two real dates). Surfaces only — it
    reports that the item came back, never what that means. Shares the same
    opt-in matching (normalize/synonyms/fuzzy) as recurrence.
    """
    hits: list[GapHit] = []
    if not records:
        return hits

    synonym_map = _build_synonym_map(synonyms, normalize)
    for record in records:
        record_id, groups = _record_groups(
            record, field, synonym_map, normalize, fuzzy_cutoff
        )
        for key in sorted(groups):
            occ = groups[key]
            dated = _dated_sorted(occ)
            label = _pick_label(occ)
            variants = sorted({o[1] for o in occ})
            for (prev_date, prev_str), (next_date, next_str) in zip(dated, dated[1:]):
                delta = (next_date - prev_date).days
                if delta > gap_days:
                    hits.append(
                        GapHit(
                            record_id=record_id,
                            item=label,
                            gap_days=delta,
                            before_date=prev_str,
                            after_date=next_str,
                            variants=variants,
                        )
                    )
    return hits


def format_gap_hit(hit: GapHit) -> str:
    """Render a gap hit as a single provenance-cited line."""
    line = (
        f'Record {hit.record_id}: "{hit.item}" returned after {hit.gap_days} days '
        f"— last seen {hit.before_date}, then {hit.after_date}"
    )
    return line + _merge_clause(hit.variants)


# ---------------------------------------------------------------------------
# Third rule — frequency / burst
# ---------------------------------------------------------------------------


def detect_frequency(
    records: list,
    field: str = "item",
    window_days: int = 30,
    min_count: int = 3,
    normalize: bool = False,
    synonyms: dict | None = None,
    fuzzy_cutoff: float | None = None,
) -> list[FrequencyHit]:
    """Surface bursts: an item that appears ``min_count`` or more times within
    any rolling window of ``window_days`` days.

    For each item, the engine sweeps a window over its sorted dated occurrences
    and finds the densest span; if that span holds ``min_count`` or more
    occurrences it emits one :class:`FrequencyHit` citing the window's dates.
    Undated occurrences are skipped. Surfaces only — it reports density in time,
    never severity. Shares the same opt-in matching as the other rules.
    """
    hits: list[FrequencyHit] = []
    if not records:
        return hits

    synonym_map = _build_synonym_map(synonyms, normalize)
    for record in records:
        record_id, groups = _record_groups(
            record, field, synonym_map, normalize, fuzzy_cutoff
        )
        for key in sorted(groups):
            occ = groups[key]
            dated = _dated_sorted(occ)
            if len(dated) < min_count:
                continue
            # Two-pointer sweep for the densest window (earliest on ties).
            left = 0
            best_count = 0
            best_span = (0, 0)
            for right in range(len(dated)):
                while (dated[right][0] - dated[left][0]).days > window_days:
                    left += 1
                if right - left + 1 > best_count:
                    best_count = right - left + 1
                    best_span = (left, right)
            if best_count >= min_count:
                lo, hi = best_span
                window = dated[lo : hi + 1]
                hits.append(
                    FrequencyHit(
                        record_id=record_id,
                        item=_pick_label(occ),
                        count=best_count,
                        window_start=window[0][1],
                        window_end=window[-1][1],
                        dates=[d[1] for d in window],
                        variants=sorted({o[1] for o in occ}),
                    )
                )
    return hits


def format_frequency_hit(hit: FrequencyHit) -> str:
    """Render a frequency hit as a single provenance-cited line."""
    span = (
        _parse_date(hit.window_end) - _parse_date(hit.window_start)
    ).days
    dates = ", ".join(hit.dates)
    line = (
        f'Record {hit.record_id}: "{hit.item}" appeared {hit.count} times '
        f"within {span} days — {dates}"
    )
    return line + _merge_clause(hit.variants)


# ---------------------------------------------------------------------------
# Self-test — the six required spec cases, asserted toward known answers
# ---------------------------------------------------------------------------


def _self_test_scenarios() -> list[tuple[str, bool]]:
    """Run the six required cases. Return (name, ok) for each.

    Each scenario defines its own input and its externally-known answer; the
    code is patched toward the answer, never the answer toward the code.
    """
    results: list[tuple[str, bool]] = []

    # 1. Item recurs 3 times in one record -> caught, count == 3, all 3 dates.
    hits = detect_recurrence(
        [
            {
                "id": "R001",
                "entries": [
                    {"date": "2026-01-10", "item": "poor sleep"},
                    {"date": "2026-02-02", "item": "poor sleep"},
                    {"date": "2026-03-15", "item": "poor sleep"},
                ],
            }
        ]
    )
    ok = (
        len(hits) == 1
        and hits[0].count == 3
        and hits[0].item == "poor sleep"
        and hits[0].dates == ["2026-01-10", "2026-02-02", "2026-03-15"]
    )
    results.append(("recurs_three_times", ok))

    # 2. Item appears exactly once -> NOT flagged (below min_count).
    hits = detect_recurrence(
        [{"id": "R002", "entries": [{"date": "2026-01-10", "item": "headache"}]}]
    )
    results.append(("single_occurrence_not_flagged", hits == []))

    # 3. Record with nothing recurring -> clean empty result, zero false positives.
    hits = detect_recurrence(
        [
            {
                "id": "R003",
                "entries": [
                    {"date": "2026-01-10", "item": "cough"},
                    {"date": "2026-02-02", "item": "rash"},
                    {"date": "2026-03-15", "item": "fatigue"},
                ],
            }
        ]
    )
    results.append(("nothing_recurring_empty", hits == []))

    # 4. Two different items each recur in one record -> both caught independently.
    hits = detect_recurrence(
        [
            {
                "id": "R004",
                "entries": [
                    {"date": "2026-01-10", "item": "poor sleep"},
                    {"date": "2026-02-02", "item": "poor sleep"},
                    {"date": "2026-02-20", "item": "appetite change"},
                    {"date": "2026-03-01", "item": "appetite change"},
                ],
            }
        ]
    )
    by_item = {h.item: h for h in hits}
    ok = (
        len(hits) == 2
        and by_item.get("poor sleep") is not None
        and by_item["poor sleep"].count == 2
        and by_item.get("appetite change") is not None
        and by_item["appetite change"].count == 2
    )
    results.append(("two_items_each_recur", ok))

    # 5. Empty record / missing field -> handled gracefully, no crash, no false hit.
    try:
        hits = detect_recurrence(
            [
                {"id": "R005", "entries": []},
                {"id": "R006"},
                {"id": "R007", "entries": [{"date": "2026-01-10"}, {"item": None}]},
                {},
            ]
        )
        ok = hits == []
    except Exception:
        ok = False
    results.append(("malformed_handled_gracefully", ok))

    # 6. min_count respected (set to 3 -> a 2x item does NOT flag).
    hits = detect_recurrence(
        [
            {
                "id": "R008",
                "entries": [
                    {"date": "2026-01-10", "item": "poor sleep"},
                    {"date": "2026-02-02", "item": "poor sleep"},
                ],
            }
        ],
        min_count=3,
    )
    results.append(("min_count_respected", hits == []))

    return results


def _run_self_test() -> int:
    """Run the built-in self-test. Return 0 on success, non-zero on failure."""
    results = _self_test_scenarios()
    failures = [name for name, ok in results if not ok]
    if failures:
        print(f"FAILED ({len(failures)}):", file=sys.stderr)
        for name in failures:
            print(f"  - {name}", file=sys.stderr)
        return 1
    print(f"OK: {len(results)} scenarios passed.")
    return 0


# ---------------------------------------------------------------------------
# Demo — runs against the (Scott-supplied) placeholder record set
# ---------------------------------------------------------------------------


def _run_demo() -> int:
    """Surface recurrences in the placeholder record set, if one is present."""
    try:
        from data.sample_records import SAMPLE_RECORDS
    except Exception:
        SAMPLE_RECORDS = []

    if not SAMPLE_RECORDS:
        print(
            "No records yet — awaiting the placeholder record set in "
            "data/sample_records.py (SAMPLE_RECORDS)."
        )
        return 0

    hits = detect_recurrence(SAMPLE_RECORDS)
    if not hits:
        print("No recurrences surfaced across the placeholder records.")
        return 0

    for hit in hits:
        print(format_hit(hit))
    return 0


def _run_demo_v1() -> int:
    """Surface recurrences with the v1 opt-in layers (normalize + declared
    synonyms + fuzzy) on the same placeholder records, so the v0->v1 difference
    is visible. Merged spellings are cited in each line."""
    try:
        from data.sample_records import SAMPLE_RECORDS, SYNONYMS
    except Exception:
        print("No records / synonyms in data/sample_records.py.")
        return 0

    hits = detect_recurrence(
        SAMPLE_RECORDS, normalize=True, synonyms=SYNONYMS, fuzzy_cutoff=0.85
    )
    for hit in hits:
        print(format_hit(hit))
    return 0


def _run_demo_gap() -> int:
    """Surface re-emergences (gap rule) across the placeholder records."""
    try:
        from data.sample_records import SAMPLE_RECORDS
    except Exception:
        SAMPLE_RECORDS = []
    hits = detect_gap(SAMPLE_RECORDS)
    if not hits:
        print("No re-emergences surfaced.")
        return 0
    for hit in hits:
        print(format_gap_hit(hit))
    return 0


def _run_demo_frequency() -> int:
    """Surface bursts (frequency rule) across the placeholder records."""
    try:
        from data.sample_records import SAMPLE_RECORDS
    except Exception:
        SAMPLE_RECORDS = []
    hits = detect_frequency(SAMPLE_RECORDS)
    if not hits:
        print("No bursts surfaced.")
        return 0
    for hit in hits:
        print(format_frequency_hit(hit))
    return 0


# ---------------------------------------------------------------------------
# CLI — local-only, no server, no network
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Recurrence Detection Engine (v0) — surface, count, and cite "
        "recurring items across dated entries. Surfaces only; never interprets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--self-test", action="store_true", help="Run the six built-in spec cases"
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="Surface recurrences in data/sample_records.py (v0 exact match)",
    )
    p.add_argument(
        "--demo-v1",
        action="store_true",
        help="Same records with v1 opt-in matching (normalize + synonyms + fuzzy)",
    )
    p.add_argument(
        "--demo-gap",
        action="store_true",
        help="Surface re-emergences (gap rule) in data/sample_records.py",
    )
    p.add_argument(
        "--demo-frequency",
        action="store_true",
        help="Surface bursts (frequency rule) in data/sample_records.py",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.self_test:
        return _run_self_test()
    if args.demo:
        return _run_demo()
    if args.demo_v1:
        return _run_demo_v1()
    if args.demo_gap:
        return _run_demo_gap()
    if args.demo_frequency:
        return _run_demo_frequency()
    build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
