#!/usr/bin/env python3
"""
recurrence.py — Recurrence Detection Engine (prototype, VERSION 0.5.0)
=====================================================================

Pure-stdlib. Zero external dependencies. Local-only (no network egress).

Given a set of records, surface every case where the same item appears across
multiple dated entries, and cite exactly where each occurrence came from.

This is a LIBRARIAN, not an interpreter. It surfaces, counts, and cites
provenance. It never scores, ranks, diagnoses, or says what a pattern *means*.
That separation is the design principle and the main risk boundary. It reduces
interpretive and clinical-decision-support risk, but it is not a compliance
determination.

Domain-agnostic by design: a record can be a patient, a pharmacy profile, a
session log — the engine does not care. Matching is EXACT by DEFAULT; the opt-in
v1 layers — normalize, human-declared synonyms, and difflib fuzzy (e.g.
"can't sleep" == "insomnia") — are SHIPPED: pass them to the rules, or run
`--report-v1`, to merge. Defaults never merge, so v0 behavior is unchanged.

  Self-test:  python recurrence.py --self-test
  Demo:       python recurrence.py --demo
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import itertools
import statistics
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

# Engine version — surfaced by `--version`; bump on a user-visible release.
VERSION = "0.5.0"


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


@dataclass
class CooccurrenceHit:
    """One surfaced co-occurrence: two items that appeared on the same dates.

    Provenance only: the record, the two item labels, how many distinct dates
    they shared, and exactly which dates. It reports that two items showed up
    together on N dates — NEVER that one is associated with, linked to, or
    explains the other. Pure counting.

    Two items means two audit trails: ``variants_a`` and ``variants_b`` list the
    distinct original spellings merged into ``item_a`` / ``item_b`` respectively
    (length 1 under v0 exact match, longer when normalize/synonyms/fuzzy merged).
    The pair is ordered so ``item_a`` precedes ``item_b`` by canonical key, making
    both the pair and the hit list deterministic.
    """

    record_id: str
    item_a: str
    item_b: str
    count: int
    dates: list[str] = field(default_factory=list)
    variants_a: list[str] = field(default_factory=list)
    variants_b: list[str] = field(default_factory=list)
    # Window extension (opt-in). window_days == 0 is exact same-date (v0); when
    # > 0, ``pairs`` holds the greedily matched (date_a, date_b, gap_days) one-to-
    # one date pairings within the window, and ``count`` is the number of pairs.
    window_days: int = 0
    pairs: list[tuple[str, str, int]] = field(default_factory=list)

    @property
    def item(self) -> str:
        """Pair label for the combined report (``"item_a + item_b"``).

        The router shapes each finding by ``hit.item``; co-occurrence is the one
        rule whose subject is a pair, so it presents the two labels joined. The
        ``+`` is provenance ("these two co-occurred"), never "these two relate".
        """
        return f"{self.item_a} + {self.item_b}"


@dataclass
class CadenceChangeHit:
    """One surfaced cadence change: an item whose inter-event spacing shifted.

    Provenance only: the record, the item, the typical interval (in days) before
    and after a single located change point, the pivot date the new spacing
    begins, and every dated occurrence. It states that the spacing changed and
    where — never whether faster or slower is good or bad, and never why.
    """

    record_id: str
    item: str
    before_interval: int
    after_interval: int
    pivot_date: str
    dates: list[str] = field(default_factory=list)
    variants: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# The functions
# ---------------------------------------------------------------------------


def _check_fuzzy_cutoff(fuzzy_cutoff: float | None) -> None:
    """Validate the fuzzy cutoff. difflib ratios live in [0, 1]; reject anything
    outside that so a typo'd argument fails loudly instead of silently meaning
    'always merge' or 'never merge'."""
    if fuzzy_cutoff is not None and not 0.0 <= fuzzy_cutoff <= 1.0:
        raise ValueError(f"fuzzy_cutoff must be between 0.0 and 1.0, got {fuzzy_cutoff}")


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
    if min_count < 1:
        raise ValueError(f"min_count must be >= 1, got {min_count}")
    _check_fuzzy_cutoff(fuzzy_cutoff)

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


def format_hit(hit: RecurrenceHit, with_record: bool = True) -> str:
    """Render a hit as a single provenance-cited line.

    Example:
      Record R001: "poor sleep" recurred 2 times — 2026-01-10, 2026-02-02

    An occurrence whose entry carried no date is stored as "" in ``hit.dates``
    and rendered here as "(undated)" — a visible data-quality marker, not an
    interpretation. It flags incomplete provenance rather than hiding it.
    """
    dates = ", ".join(d if d else "(undated)" for d in hit.dates)
    prefix = f"Record {hit.record_id}: " if with_record else ""
    line = f'{prefix}"{hit.item}" recurred {hit.count} times — {dates}'
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
    if gap_days < 0:
        raise ValueError(f"gap_days must be >= 0, got {gap_days}")
    _check_fuzzy_cutoff(fuzzy_cutoff)

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


def format_gap_hit(hit: GapHit, with_record: bool = True) -> str:
    """Render a gap hit as a single provenance-cited line."""
    prefix = f"Record {hit.record_id}: " if with_record else ""
    line = (
        f'{prefix}"{hit.item}" returned after {hit.gap_days} days '
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
    if window_days < 0:
        raise ValueError(f"window_days must be >= 0, got {window_days}")
    if min_count < 1:
        raise ValueError(f"min_count must be >= 1, got {min_count}")
    _check_fuzzy_cutoff(fuzzy_cutoff)

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


def format_frequency_hit(hit: FrequencyHit, with_record: bool = True) -> str:
    """Render a frequency hit as a single provenance-cited line."""
    span = (
        _parse_date(hit.window_end) - _parse_date(hit.window_start)
    ).days
    dates = ", ".join(hit.dates)
    prefix = f"Record {hit.record_id}: " if with_record else ""
    line = (
        f'{prefix}"{hit.item}" appeared {hit.count} times '
        f"within {span} days — {dates}"
    )
    return line + _merge_clause(hit.variants)


# ---------------------------------------------------------------------------
# Fourth rule — co-occurrence (two items on the same dates, or within a window)
# ---------------------------------------------------------------------------


def _match_within_window(
    dates_a: set[str], dates_b: set[str], window_days: int
) -> list[tuple[str, str, int]]:
    """Greedily pair dates from two items that fall within ``window_days``.

    One-to-one: each occurrence-day is used at most once, so a single date near
    several on the other side is not double-counted. Candidates are consumed
    smallest-gap first (ties: earlier date_a, then date_b) for determinism.
    Unparseable dates are skipped — a gap needs two real dates — mirroring the
    other date rules. Returns matched ``(date_a, date_b, gap_days)`` sorted
    chronologically.
    """
    pa = sorted((d, s) for s in dates_a if (d := _parse_date(s)) is not None)
    pb = sorted((d, s) for s in dates_b if (d := _parse_date(s)) is not None)
    candidates: list[tuple[int, datetime.date, str, datetime.date, str]] = []
    for da, sa in pa:
        for db, sb in pb:
            gap = abs((da - db).days)
            if gap <= window_days:
                candidates.append((gap, da, sa, db, sb))
    candidates.sort(key=lambda t: (t[0], t[1], t[3]))
    used_a: set[str] = set()
    used_b: set[str] = set()
    matched: list[tuple[str, str, int]] = []
    for gap, da, sa, db, sb in candidates:
        if sa in used_a or sb in used_b:
            continue
        used_a.add(sa)
        used_b.add(sb)
        matched.append((sa, sb, gap))
    matched.sort(key=lambda t: (t[0], t[1]))
    return matched


def detect_cooccurrence(
    records: list,
    field: str = "item",
    min_count: int = 2,
    window_days: int = 0,
    normalize: bool = False,
    synonyms: dict | None = None,
    fuzzy_cutoff: float | None = None,
) -> list[CooccurrenceHit]:
    """Surface co-occurrences: two distinct items in one record that BOTH appear
    on the same date, on ``min_count`` or more distinct shared dates.

    For each record the engine groups occurrences (sharing the same opt-in
    matching as the other rules), collects each item's set of dated days, and for
    every pair intersects those sets; a pair whose shared-date count reaches
    ``min_count`` emits one :class:`CooccurrenceHit` citing the shared dates.
    Undated occurrences are excluded — there is no date to share. Surfaces only:
    it reports that two items co-occurred N times, never that they are related.

    ``window_days`` is OPT-IN and defaults to 0 = exact same-date (v0 behavior,
    unchanged). When > 0, two items co-occur if their dates fall within
    ``window_days`` of each other; dates are paired greedily one-to-one (smallest
    gap first) so no occurrence is double-counted, and each matched pair + gap is
    cited in ``hit.pairs``.
    """
    if min_count < 1:
        raise ValueError(f"min_count must be >= 1, got {min_count}")
    if window_days < 0:
        raise ValueError(f"window_days must be >= 0, got {window_days}")
    _check_fuzzy_cutoff(fuzzy_cutoff)

    hits: list[CooccurrenceHit] = []
    if not records:
        return hits

    synonym_map = _build_synonym_map(synonyms, normalize)
    for record in records:
        record_id, groups = _record_groups(
            record, field, synonym_map, normalize, fuzzy_cutoff
        )
        # Per item: its set of distinct dated days (undated "" excluded — a date
        # that does not exist cannot be shared), plus the display label and the
        # audit trail of merged spellings.
        dates_by_key: dict[str, set] = {}
        label_by_key: dict[str, str] = {}
        variants_by_key: dict[str, list] = {}
        for key, occ in groups.items():
            dated = {o[0] for o in occ if o[0]}
            if dated:
                dates_by_key[key] = dated
                label_by_key[key] = _pick_label(occ)
                variants_by_key[key] = sorted({o[1] for o in occ})
        # Deterministic: pairs in sorted-key order, each unordered pair once.
        for key_a, key_b in itertools.combinations(sorted(dates_by_key), 2):
            if window_days == 0:
                # v0 exact same-date: intersect the two date sets (unchanged).
                shared = dates_by_key[key_a] & dates_by_key[key_b]
                if len(shared) >= min_count:
                    hits.append(
                        CooccurrenceHit(
                            record_id=record_id,
                            item_a=label_by_key[key_a],
                            item_b=label_by_key[key_b],
                            count=len(shared),
                            dates=sorted(shared),
                            variants_a=variants_by_key[key_a],
                            variants_b=variants_by_key[key_b],
                        )
                    )
            else:
                # Windowed: greedy one-to-one date pairing within window_days, so
                # no occurrence is counted twice. count = number of matched pairs.
                matched = _match_within_window(
                    dates_by_key[key_a], dates_by_key[key_b], window_days
                )
                if len(matched) >= min_count:
                    involved = sorted({s for pair in matched for s in pair[:2]})
                    hits.append(
                        CooccurrenceHit(
                            record_id=record_id,
                            item_a=label_by_key[key_a],
                            item_b=label_by_key[key_b],
                            count=len(matched),
                            dates=involved,
                            variants_a=variants_by_key[key_a],
                            variants_b=variants_by_key[key_b],
                            window_days=window_days,
                            pairs=matched,
                        )
                    )
    return hits


def _pair_merge_clause(hit: CooccurrenceHit) -> str:
    """Cite merged spellings for a PAIR, attributed to each item.

    Reuses the single-item ``_merge_clause`` token per side and labels it with the
    item, so a two-item hit's audit trail stays unambiguous. Empty when neither
    side merged (the v0 exact-match case), so v0 lines stay clean.
    """
    clause = ""
    if len(hit.variants_a) > 1:
        clause += f' "{hit.item_a}"{_merge_clause(hit.variants_a)}'
    if len(hit.variants_b) > 1:
        clause += f' "{hit.item_b}"{_merge_clause(hit.variants_b)}'
    return clause


def format_cooccurrence_hit(hit: CooccurrenceHit, with_record: bool = True) -> str:
    """Render a co-occurrence as a single provenance-cited, pure-count line.

    Example:
      Record R017: "knee pain" + "poor sleep" co-occurred 2 times — 2026-01-10, 2026-02-14

    Strictly a count of shared dates; it never says the two items are associated,
    linked, correlated, or that one explains the other.
    """
    prefix = f"Record {hit.record_id}: " if with_record else ""
    if hit.window_days > 0:
        pairs = ", ".join(f"({a} ~ {b}: {g}d)" for a, b, g in hit.pairs)
        line = (
            f'{prefix}"{hit.item_a}" + "{hit.item_b}" co-occurred '
            f"{hit.count} times within {hit.window_days} days — {pairs}"
        )
    else:
        dates = ", ".join(hit.dates)
        line = (
            f'{prefix}"{hit.item_a}" + "{hit.item_b}" co-occurred '
            f"{hit.count} times — {dates}"
        )
    return line + _pair_merge_clause(hit)


# ---------------------------------------------------------------------------
# Fifth rule — cadence change (an item's inter-event spacing shifted)
# ---------------------------------------------------------------------------


def _pettitt_pivot(values: list[float]) -> int:
    """Locate the single most likely change point in a sequence (Pettitt, 1979).

    Returns the split ``k`` (1 <= k < n) that maximizes Pettitt's rank statistic
    ``|U_k|``, where ``U_k`` sums ``sign(values[i] - values[j])`` over ``i < k``
    and ``j >= k`` — a nonparametric test for a shift in central tendency. Ties
    are broken by the larger before/after median ratio, then the earliest ``k``.
    Pure rank arithmetic: deterministic, no distribution assumption.
    """
    n = len(values)
    best_k, best_key = 1, None
    for k in range(1, n):
        u = 0
        for i in range(k):
            for j in range(k, n):
                diff = values[i] - values[j]
                u += (diff > 0) - (diff < 0)
        before_med = statistics.median(values[:k])
        after_med = statistics.median(values[k:])
        ratio = (
            max(before_med / after_med, after_med / before_med)
            if before_med and after_med
            else 0.0
        )
        key = (abs(u), ratio, -k)  # max |U|, then max ratio, then earliest k
        if best_key is None or key > best_key:
            best_k, best_key = k, key
    return best_k


def detect_cadence_change(
    records: list,
    field: str = "item",
    min_occurrences: int = 4,
    ratio: float = 2.0,
    normalize: bool = False,
    synonyms: dict | None = None,
    fuzzy_cutoff: float | None = None,
) -> list[CadenceChangeHit]:
    """Surface a cadence change: an item whose spacing between dated occurrences
    shifted by ``ratio`` or more across a single change point.

    For each item with at least ``min_occurrences`` distinct dated days, the
    engine takes the consecutive inter-event intervals (days), locates the single
    most likely change point with Pettitt's rank statistic, and compares the
    median interval before vs after; when the larger-over-smaller ratio reaches
    ``ratio`` it emits one :class:`CadenceChangeHit` citing both medians and the
    pivot date the new spacing begins. Undated occurrences are excluded — they
    have no interval. States that the spacing changed and where, never that
    faster or slower means anything. Shares the same opt-in matching as the
    other rules.

    Floor: a change point needs at least 3 distinct dated days (≥2 inter-event
    intervals, one on each side of the pivot). ``min_occurrences`` validates at
    >= 2, but a value below 3 can never fire (default is 4).
    """
    if min_occurrences < 2:
        raise ValueError(f"min_occurrences must be >= 2, got {min_occurrences}")
    if ratio <= 1.0:
        raise ValueError(f"ratio must be > 1.0, got {ratio}")
    _check_fuzzy_cutoff(fuzzy_cutoff)

    hits: list[CadenceChangeHit] = []
    if not records:
        return hits

    synonym_map = _build_synonym_map(synonyms, normalize)
    for record in records:
        record_id, groups = _record_groups(
            record, field, synonym_map, normalize, fuzzy_cutoff
        )
        for key in sorted(groups):
            occ = groups[key]
            # Distinct dated days, chronological (one event per day; undated out).
            days: list[tuple[datetime.date, str]] = []
            for date, date_str in _dated_sorted(occ):
                if not days or date != days[-1][0]:
                    days.append((date, date_str))
            if len(days) < min_occurrences:
                continue
            intervals = [
                (days[i + 1][0] - days[i][0]).days for i in range(len(days) - 1)
            ]
            if len(intervals) < 2:  # need at least one interval on each side
                continue
            k = _pettitt_pivot(intervals)
            before_med = statistics.median(intervals[:k])
            after_med = statistics.median(intervals[k:])
            if before_med <= 0 or after_med <= 0:
                continue
            if max(before_med / after_med, after_med / before_med) < ratio:
                continue
            hits.append(
                CadenceChangeHit(
                    record_id=record_id,
                    item=_pick_label(occ),
                    before_interval=round(before_med),
                    after_interval=round(after_med),
                    pivot_date=days[k][1],
                    dates=[ds for _, ds in days],
                    variants=sorted({o[1] for o in occ}),
                )
            )
    return hits


def format_cadence_change_hit(hit: CadenceChangeHit, with_record: bool = True) -> str:
    """Render a cadence change as a single provenance-cited, neutral line.

    Example:
      Record R021: "insulin" interval changed from ~30d to ~7d at 2026-04-01 — <dates>

    States the interval before and after and the date it changed; never whether
    the change is faster/slower, accelerating, increasing, or a concern.
    """
    dates = ", ".join(hit.dates)
    prefix = f"Record {hit.record_id}: " if with_record else ""
    line = (
        f'{prefix}"{hit.item}" interval changed from ~{hit.before_interval}d '
        f"to ~{hit.after_interval}d at {hit.pivot_date} — {dates}"
    )
    return line + _merge_clause(hit.variants)


# ---------------------------------------------------------------------------
# Router — one dispatch over an expert registry into a per-record report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Expert:
    """One surfacing rule, bound to its name and its detect + format callables.

    ``name`` is a neutral lens label — provenance for which rule surfaced a
    line, never a judgment or a ranking. The router invokes ``detect`` with ONLY
    the shared matching knobs (field/normalize/synonyms/fuzzy_cutoff); each
    rule's own thresholds (min_count/gap_days/window_days) fall through to their
    documented defaults, so the registry stays a single source of truth.
    """

    name: str
    detect: Callable[..., list]
    formatter: Callable[..., str]


# Registry order IS the report's expert order: recurrence (the base lens), then
# gap, then frequency, then co-occurrence, then cadence change — the order the
# rules were built and documented in. Adding a further rule is appending one
# Expert here; the router and the formatter need no other change.
EXPERTS: tuple[Expert, ...] = (
    Expert("recurrence", detect_recurrence, format_hit),
    Expert("gap", detect_gap, format_gap_hit),
    Expert("frequency", detect_frequency, format_frequency_hit),
    Expert("cooccurrence", detect_cooccurrence, format_cooccurrence_hit),
    Expert("cadence_change", detect_cadence_change, format_cadence_change_hit),
)


@dataclass
class Finding:
    """One surfaced line from one expert, kept with its source.

    ``expert`` is the lens name (provenance); ``hit`` is the original
    RecurrenceHit / GapHit / FrequencyHit; ``line`` is its rendered text with
    the redundant record prefix dropped (the report header carries the id).
    """

    expert: str
    hit: object
    line: str


@dataclass
class RecordReport:
    """Everything the experts surfaced for one record, in registry order.

    A record with zero findings is never constructed: the report surfaces only
    what is present — it does not assert that a record is clean.
    """

    record_id: str
    findings: list[Finding] = field(default_factory=list)


def run_report(
    records: list,
    *,
    experts: tuple[Expert, ...] = EXPERTS,
    field: str = "item",
    normalize: bool = False,
    synonyms: dict | None = None,
    fuzzy_cutoff: float | None = None,
) -> list[RecordReport]:
    """Run every expert over the records and assemble a per-record listing.

    Each expert is invoked once over the full record set with only the shared
    matching knobs; rule-specific thresholds keep their defaults. All hits are
    grouped by ``record_id`` and ordered deterministically: records by id,
    experts in registry order, hits within an expert in that rule's own order.

    Records with no findings are OMITTED. Input validation is delegated to each
    ``detect_*`` (which already raises ValueError on bad thresholds), so there
    is no duplicated checking here. Surfaces, counts, cites — never ranks,
    scores, totals, or interprets.
    """
    reports: dict[str, RecordReport] = {}
    for expert in experts:
        hits = expert.detect(
            records,
            field=field,
            normalize=normalize,
            synonyms=synonyms,
            fuzzy_cutoff=fuzzy_cutoff,
        )
        for hit in hits:
            report = reports.setdefault(
                hit.record_id, RecordReport(record_id=hit.record_id)
            )
            report.findings.append(
                Finding(expert.name, hit, expert.formatter(hit, with_record=False))
            )
    return [reports[rid] for rid in sorted(reports)]


def format_report(reports: list[RecordReport]) -> str:
    """Render the combined per-record report as text.

    Per record: a header line, then one line per finding prefixed with its
    expert (lens) name — provenance for which rule surfaced it, never a
    judgment. Records are blank-line separated; an empty report renders as "".
    """
    blocks: list[str] = []
    for report in reports:
        lines = [f"Record {report.record_id}:"]
        lines.extend(f"  [{f.expert}] {f.line}" for f in report.findings)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


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
    except ImportError:
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
    except ImportError:
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
    except ImportError:
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
    except ImportError:
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
    except ImportError:
        SAMPLE_RECORDS = []
    hits = detect_frequency(SAMPLE_RECORDS)
    if not hits:
        print("No bursts surfaced.")
        return 0
    for hit in hits:
        print(format_frequency_hit(hit))
    return 0


def _run_demo_cooccurrence() -> int:
    """Surface co-occurrences (two items on the same dates) across the records."""
    try:
        from data.sample_records import SAMPLE_RECORDS
    except ImportError:
        SAMPLE_RECORDS = []
    hits = detect_cooccurrence(SAMPLE_RECORDS)
    if not hits:
        print("No co-occurrences surfaced.")
        return 0
    for hit in hits:
        print(format_cooccurrence_hit(hit))
    return 0


def _run_demo_cooccurrence_window() -> int:
    """Surface co-occurrences within a 7-day window (opt-in window_days) across
    the records — the same lens as --demo-cooccurrence, but pairing dates that
    fall within 7 days, not only the same day."""
    try:
        from data.sample_records import SAMPLE_RECORDS
    except ImportError:
        SAMPLE_RECORDS = []
    hits = detect_cooccurrence(SAMPLE_RECORDS, window_days=7)
    if not hits:
        print("No windowed co-occurrences surfaced.")
        return 0
    for hit in hits:
        print(format_cooccurrence_hit(hit))
    return 0


def _run_demo_cadence_change() -> int:
    """Surface cadence changes (an item's inter-event spacing shifted) across the
    placeholder records."""
    try:
        from data.sample_records import SAMPLE_RECORDS
    except ImportError:
        SAMPLE_RECORDS = []
    hits = detect_cadence_change(SAMPLE_RECORDS)
    if not hits:
        print("No cadence changes surfaced.")
        return 0
    for hit in hits:
        print(format_cadence_change_hit(hit))
    return 0


def _run_report() -> int:
    """Surface the combined per-record report (all rules, v0 exact match)."""
    try:
        from data.sample_records import SAMPLE_RECORDS
    except ImportError:
        SAMPLE_RECORDS = []
    reports = run_report(SAMPLE_RECORDS)
    if not reports:
        print("No findings surfaced across the records.")
        return 0
    print(format_report(reports))
    return 0


def _run_report_v1() -> int:
    """Combined per-record report with the v1 opt-in layers (normalize + declared
    synonyms + fuzzy) on the same records, so the v0->v1 difference is visible
    across every rule. Merged spellings are cited in each line."""
    try:
        from data.sample_records import SAMPLE_RECORDS, SYNONYMS
    except ImportError:
        print("No records / synonyms in data/sample_records.py.")
        return 0
    reports = run_report(
        SAMPLE_RECORDS, normalize=True, synonyms=SYNONYMS, fuzzy_cutoff=0.85
    )
    if not reports:
        print("No findings surfaced across the records.")
        return 0
    print(format_report(reports))
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
        "--version",
        action="store_true",
        help="Print the engine name and version, then exit",
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
    p.add_argument(
        "--demo-cooccurrence",
        action="store_true",
        help="Surface co-occurrences (two items on the same dates) in data/sample_records.py",
    )
    p.add_argument(
        "--demo-cooccurrence-window",
        action="store_true",
        help="Surface co-occurrences within a 7-day window (opt-in window_days)",
    )
    p.add_argument(
        "--demo-cadence-change",
        action="store_true",
        help="Surface cadence changes (an item's interval shifted) in data/sample_records.py",
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="Combined per-record report across all rules (v0 exact match)",
    )
    p.add_argument(
        "--report-v1",
        action="store_true",
        help="Combined report with v1 opt-in matching (normalize + synonyms + fuzzy)",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.version:
        print(f"Health-Prototype recurrence engine {VERSION}")
        return 0
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
    if args.demo_cooccurrence:
        return _run_demo_cooccurrence()
    if args.demo_cooccurrence_window:
        return _run_demo_cooccurrence_window()
    if args.demo_cadence_change:
        return _run_demo_cadence_change()
    if args.report:
        return _run_report()
    if args.report_v1:
        return _run_report_v1()
    build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
