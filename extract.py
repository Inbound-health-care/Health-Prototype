#!/usr/bin/env python3
"""
extract.py — Free-text extraction FRONT-END (deterministic; slice 2: match modes)
=================================================================================

Pure-stdlib. Zero external dependencies. Local-only (no network egress).

Turns dated-line prose notes into the recurrence engine's canonical record shape
{id, entries:[{date, item, source_span}]} — which recurrence.py's five surfacing
rules then consume UNCHANGED. Extraction is a front door to the librarian; it is
NOT part of the librarian. The engine and its tests are untouched, and the
dependency runs one way: extract.py imports recurrence.py, never the reverse.

Stance A — strict literal (chosen by the operator; see ADR 0008): emit every
exact, word-bounded, longest-match gazetteer hit on a dated line, with its
character-offset provenance. NO cue logic, NO presence/absence/ownership
judgment: "chest pain" is emitted from "Denies chest pain" — the librarian rule in action.
Filtering a mention is the human's job, done on the cited provenance.

Matching modes (slice 2; see ADR 0012). Matching is fragile in clinical text, so
how loosely a stretch of text counts as a gazetteer concept is an EXPLICIT,
opt-in choice (a `MatchConfig`), never a hidden default:
  - strict   : exact, case-insensitive, whole-word, longest-match (the safe default).
  - synonyms : strict + a curated {variant -> canonical} map the caller supplies.
  - fuzzy    : strict + difflib near-match against gazetteer terms, above a caller
               cutoff, GUARDED (affix-antonym detector + look-alike denylist +
               optional drug-name exemption).
  - both     : synonyms + fuzzy together (guards still apply).
The guards are always on in fuzzy/both; strict is always available as the default.
This is a transparency / human-control aid, not a guarantee — see `--explain-modes`.

The two PHI controls, by construction (see ADR 0009 — NOT legal advice):
  - Allowlist (HIPAA Safe Harbor): only curated gazetteer concepts can surface,
    so names / SSNs / MRNs and the other identifiers are structurally
    un-extractable. The "Patient:" header value becomes the record id and is
    never gazetteer-scanned. Fuzzy matches are anchored to the gazetteer too, so
    only allowlisted concepts ever surface.
  - Dates de-identified by a consistent per-record shift (an Expert-Determination
    technique): every date moves by the same offset, so intervals are preserved
    and the engine's date math survives while the calendar is obscured. The
    default shift is 0 (unshifted).

Relative-date anchoring (slice 1; opt-in — see ADR 0013): OFF by default, so
default output is byte-for-byte the explicit-date behavior. When the caller sets
resolve_relative=True (with an explicit reference_date anchor), a line whose
LEADING token is a relative ("3 weeks ago", "since 2026-02-01"), partial
("March 2026"), or frequency ("q2wk") expression is recognized; explicitly-
anchored relatives resolve, everything else is surfaced UNRESOLVED/undated but
cited — never guessed. Recurring expressions are tagged as frequency, never given
an invented date.

Deferred to later slices (researched, intentionally not built): multi-patient
notes; mid-line (non-leading) temporal expressions; partial-date normalization.

  Self-test:      python extract.py --self-test
  Demo:           python extract.py --demo [--match-mode {strict,synonyms,fuzzy,both}]
  Explain modes:  python extract.py --explain-modes
"""

from __future__ import annotations

import argparse
import calendar
import datetime
import difflib
import re
import sys
from collections import Counter
from dataclasses import dataclass

from recurrence import _check_fuzzy_cutoff, _normalize, detect_recurrence

# Front-end version — independent of the engine's VERSION. Bump on a
# user-visible change to extraction behavior.
VERSION = "0.4.0"


# ---------------------------------------------------------------------------
# Validation — fail loudly up front (house style, cf. _check_fuzzy_cutoff).
# ---------------------------------------------------------------------------


def _validate_gazetteer(gazetteer: list[str]) -> None:
    """A usable gazetteer is a non-empty list of non-empty strings."""
    if not gazetteer:
        raise ValueError("gazetteer must be a non-empty list of terms")
    for term in gazetteer:
        if not isinstance(term, str) or term == "":
            raise ValueError(
                f"gazetteer terms must be non-empty strings, got {term!r}"
            )


def _validate_shift(date_shift_days: int) -> None:
    """The date shift is an integer day offset (bool is rejected explicitly so a
    stray True/False cannot silently shift by one day)."""
    if isinstance(date_shift_days, bool) or not isinstance(date_shift_days, int):
        raise ValueError(f"date_shift_days must be an int, got {date_shift_days!r}")


# ---------------------------------------------------------------------------
# Merge-safety guards (slice 2 — the fragile part). Matching loosely in clinical
# text can silently fuse OPPOSITE concepts: affix antonyms differ by one morpheme
# yet score high on string similarity ("hypertension" vs "hypotension"); and
# look-alike/sound-alike (LASA) drug names are a whole catalogued hazard class.
# These guards block such merges. They are domain-agnostic mechanisms (string
# morphology + an explicit denylist), NOT a clinical vocabulary — callers supply
# the real terms. This is MERGE safety; it does not contradict ADR 0009's
# "allowlist over denylist" for PHI (that governs what text may surface at all).
# ---------------------------------------------------------------------------

# Prefix pairs where swapping the prefix flips meaning (same remainder).
_PREFIX_ANTONYM_PAIRS = (("hyper", "hypo"), ("tachy", "brady"))
# Prefixes that negate when prepended to an existing word (un-, non-, a-, ...).
_NEGATION_PREFIXES = ("non", "un", "im", "in", "ir", "il", "dis", "an", "a")


def _is_affix_antonym(a: str, b: str) -> bool:
    """True if ``a`` and ``b`` are a meaning-flipping affix variant of each other
    (so a fuzzy near-match between them must be refused). Deliberately
    over-inclusive: blocking a borderline pair only costs recall (recoverable),
    while a wrong merge is a false pattern (the ADR 0011 liability). Inputs are
    expected normalized (casefolded)."""
    for p, q in _PREFIX_ANTONYM_PAIRS:
        if a.startswith(p) and b.startswith(q) and a[len(p):] == b[len(q):]:
            return True
        if a.startswith(q) and b.startswith(p) and a[len(q):] == b[len(p):]:
            return True
    for pre in _NEGATION_PREFIXES:
        if a == pre + b or b == pre + a:
            return True
    return False


# Illustrative ONLY — one look-alike/sound-alike (LASA) pair. Real deployments
# extend this from the ISMP List of Confused Drug Names (~528 pairs) and any
# site-specific confusables. Stored as normalized (casefolded) unordered pairs.
DEFAULT_ANTI_PAIRINGS: frozenset = frozenset({frozenset({"bupropion", "buspirone"})})


def _violates_anti_pairing(a: str, b: str, anti_pairings: frozenset) -> bool:
    """True if merging normalized terms ``a`` and ``b`` is forbidden: an
    affix-antonym, or an explicit denylisted pair."""
    if a == b:
        return False
    if _is_affix_antonym(a, b):
        return True
    return frozenset({a, b}) in anti_pairings


def _validate_synonyms(synonyms: dict) -> None:
    """A synonym map is {variant: canonical} of non-empty strings. A pairing that
    is itself an affix-antonym is refused (you cannot declare stable -> unstable)."""
    if not isinstance(synonyms, dict):
        raise ValueError("synonyms must be a dict of {variant: canonical}")
    for variant, canonical in synonyms.items():
        if (
            not isinstance(variant, str)
            or variant == ""
            or not isinstance(canonical, str)
            or canonical == ""
        ):
            raise ValueError(
                f"synonym entries must be non-empty strings, got {variant!r}: {canonical!r}"
            )
        if _is_affix_antonym(_normalize(variant), _normalize(canonical)):
            raise ValueError(
                f"refusing affix-antonym synonym (meaning-flipping): "
                f"{variant!r} -> {canonical!r}"
            )


# ---------------------------------------------------------------------------
# MatchConfig — the explicit, must-be-chosen matching policy (slice 2). The
# default is strict; anything looser must be selected, and the inputs a mode
# needs are required while mismatched inputs are rejected (you cannot smuggle
# synonyms past a strict config). House style: fail loudly.
# ---------------------------------------------------------------------------

_MODES = ("strict", "synonyms", "fuzzy", "both")


@dataclass
class MatchConfig:
    mode: str = "strict"
    synonyms: dict | None = None
    fuzzy_cutoff: float | None = None
    anti_pairings: frozenset = DEFAULT_ANTI_PAIRINGS
    no_fuzzy_terms: frozenset = frozenset()

    def __post_init__(self) -> None:
        if self.mode not in _MODES:
            raise ValueError(f"mode must be one of {_MODES}, got {self.mode!r}")
        wants_syn = self.mode in ("synonyms", "both")
        wants_fuzzy = self.mode in ("fuzzy", "both")
        if wants_syn:
            if not self.synonyms:
                raise ValueError(f"mode {self.mode!r} requires a non-empty synonyms map")
            _validate_synonyms(self.synonyms)
        elif self.synonyms:
            raise ValueError(
                f"synonyms given but mode is {self.mode!r}; "
                f"choose mode 'synonyms' or 'both'"
            )
        if wants_fuzzy:
            if self.fuzzy_cutoff is None:
                raise ValueError(f"mode {self.mode!r} requires fuzzy_cutoff (0.0-1.0)")
            _check_fuzzy_cutoff(self.fuzzy_cutoff)
        elif self.fuzzy_cutoff is not None:
            raise ValueError(
                f"fuzzy_cutoff given but mode is {self.mode!r}; "
                f"choose mode 'fuzzy' or 'both'"
            )


# ---------------------------------------------------------------------------
# Date extraction — explicit dates (always on). Relative/partial/frequency
# expressions are a separate, opt-in pass below (ADR 0013); the explicit parser
# here is unchanged and remains the default.
# ---------------------------------------------------------------------------

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

# Each pattern anchors at the START of a line (after optional whitespace) and
# captures exactly one explicit date token: ISO 8601, US M/D/YYYY, or Mon D YYYY.
_ISO_RE = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})(?![0-9])")
_US_RE = re.compile(r"^\s*(\d{1,2}/\d{1,2}/\d{4})(?![0-9])")
_MONNAME_RE = re.compile(r"^\s*([A-Za-z]{3,9})\s+(\d{1,2})\s+(\d{4})(?![0-9])")


def _parse_leading_date(line: str) -> tuple[datetime.date, int] | None:
    """If ``line`` begins with a recognized explicit date, return
    ``(date, content_offset)`` where content_offset is the index just past the
    date token. Otherwise None. Never raises: an unparseable or out-of-range
    date means "this is not a dated line" (house style: skip, never guess)."""
    m = _ISO_RE.match(line)
    if m:
        try:
            return datetime.date.fromisoformat(m.group(1)), m.end()
        except ValueError:
            return None
    m = _US_RE.match(line)
    if m:
        try:
            return datetime.datetime.strptime(m.group(1), "%m/%d/%Y").date(), m.end()
        except ValueError:
            return None
    m = _MONNAME_RE.match(line)
    if m:
        month = _MONTHS.get(m.group(1).casefold())
        if month is None:
            return None
        try:
            return datetime.date(int(m.group(3)), month, int(m.group(2))), m.end()
        except ValueError:
            return None
    return None


def parse_dated_lines(note: str) -> list[tuple[int, datetime.date, int]]:
    """Each line that BEGINS with an explicit date as
    ``(line_start, date, content_start)`` in WHOLE-NOTE character offsets, where
    content_start is the offset just past the date token. Lines without a leading
    date are skipped (no entries attach to them); nothing is ever raised."""
    out: list[tuple[int, datetime.date, int]] = []
    offset = 0
    for line in note.splitlines(keepends=True):
        parsed = _parse_leading_date(line)
        if parsed is not None:
            date, content_rel = parsed
            out.append((offset, date, offset + content_rel))
        offset += len(line)
    return out


def shift_date(d: datetime.date, days: int) -> datetime.date:
    """Apply the per-record date shift (ADR 0009 de-identification). ``days == 0``
    is the identity; any constant shift preserves every interval between dates."""
    return d + datetime.timedelta(days=days)


# ---------------------------------------------------------------------------
# Relative-date anchoring (slice 1; OPT-IN, conservative — see ADR 0013).
# OFF by default, so default output is byte-for-byte the explicit-date behavior.
# When enabled, a line whose LEADING token is a relative / partial / frequency
# expression is recognized and the gazetteer hits on that line are annotated. The
# arithmetic is trivial; the literature shows the hard part is anchor SELECTION,
# so we resolve ONLY explicitly-anchored cases and otherwise surface the phrase
# UNRESOLVED (date="") — never guess. Recurring expressions ("q2wk") are tagged as
# frequency, never expanded into invented event dates. The anchor is an explicit
# caller-supplied reference_date (encounter/document date); resolved dates are
# date-shifted with everything else, so a constant per-record shift preserves all
# intervals (ADR 0009).
# ---------------------------------------------------------------------------

_REL_UNITS = {
    "day": "days", "days": "days", "week": "weeks", "weeks": "weeks",
    "month": "months", "months": "months", "year": "years", "years": "years",
}

# "<N> <unit> ago|prior|earlier"  and  "(for the past|past) <N> <unit>".
_REL_AGO_RE = re.compile(
    r"^\s*(\d{1,4})\s+(day|days|week|weeks|month|months|year|years)"
    r"\s+(?:ago|prior|earlier)\b",
    re.IGNORECASE,
)
_REL_PAST_RE = re.compile(
    r"^\s*(?:for\s+the\s+past|past)\s+(\d{1,4})"
    r"\s+(day|days|week|weeks|month|months|year|years)\b",
    re.IGNORECASE,
)
_REL_SINCE_RE = re.compile(r"^\s*since\s+", re.IGNORECASE)
# Leading frequency token (minimal, extensible): qNwk/qNh/qNd, bid/tid/qid/qd,
# once|twice daily, daily, every N <unit>. Frequency is NOT a dated event.
_FREQ_RE = re.compile(
    r"^\s*(?:q\d{1,2}\s?(?:hrs|hr|h|wks|wk|w|mo|months|month|weeks|week|days|day|d)"
    r"|qhs|qid|tid|bid|qd"
    r"|once\s+daily|twice\s+daily|daily"
    r"|every\s+\d{1,3}\s+(?:day|days|week|weeks|month|months))\b",
    re.IGNORECASE,
)
# Partial explicit date: "<MonthName> <Year>" (no day) -> month granularity.
_PARTIAL_MONYEAR_RE = re.compile(r"^\s*([A-Za-z]{3,9})\s+(\d{4})(?![0-9])")


def _shift_months(d: datetime.date, months: int) -> datetime.date:
    """``d`` shifted by ``months`` (may be negative), clamping the day to the
    target month's length (Mar 31 - 1 month -> Feb 28). Pure stdlib; never raises."""
    index = d.month - 1 + months
    year = d.year + index // 12
    month = index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def _resolve_offset(n: int, unit: str, anchor: datetime.date) -> datetime.date:
    """``anchor`` minus ``n`` units (unit normalized via _REL_UNITS)."""
    kind = _REL_UNITS[unit.casefold()]
    if kind == "days":
        return anchor - datetime.timedelta(days=n)
    if kind == "weeks":
        return anchor - datetime.timedelta(weeks=n)
    if kind == "months":
        return _shift_months(anchor, -n)
    return _shift_months(anchor, -12 * n)  # years


def _validate_relative(resolve_relative: bool, reference_date) -> None:
    """resolve_relative is a bool; reference_date is a date or None. An anchor with
    the feature off is rejected (explicit, must-be-chosen — cf. MatchConfig)."""
    if not isinstance(resolve_relative, bool):
        raise ValueError(f"resolve_relative must be a bool, got {resolve_relative!r}")
    if reference_date is not None and not isinstance(reference_date, datetime.date):
        raise ValueError(
            f"reference_date must be a datetime.date or None, got {reference_date!r}"
        )
    if reference_date is not None and not resolve_relative:
        raise ValueError(
            "reference_date given but resolve_relative is False; pass resolve_relative=True"
        )


def _parse_leading_relative(
    line: str, reference_date: datetime.date | None
) -> tuple[str, datetime.date | None, int, int] | None:
    """Recognize a LEADING relative/partial/frequency token (consulted only when
    resolve_relative is on and the line has no leading explicit date). Returns
    ``(kind, date_or_None, phrase_start, content_offset)`` where the phrase occupies
    ``line[phrase_start:content_offset]`` and gazetteer content begins at
    content_offset; or None. ``kind`` in 'relative' | 'partial' | 'frequency' |
    'unresolved'. Never raises (house style: skip, never guess)."""
    ws = len(line) - len(line.lstrip())
    # "since <explicit date>" — absolute, needs no anchor.
    m = _REL_SINCE_RE.match(line)
    if m:
        parsed = _parse_leading_date(line[m.end():])
        if parsed is not None:
            inner_date, inner_off = parsed
            return ("relative", inner_date, ws, m.end() + inner_off)
    # "<N> <unit> ago|prior|earlier" / "(for the past|past) <N> <unit>".
    for rx in (_REL_AGO_RE, _REL_PAST_RE):
        m = rx.match(line)
        if m:
            if reference_date is None:
                return ("unresolved", None, ws, m.end())
            resolved = _resolve_offset(int(m.group(1)), m.group(2), reference_date)
            return ("relative", resolved, ws, m.end())
    # Leading frequency token — surfaced, never dated.
    m = _FREQ_RE.match(line)
    if m:
        return ("frequency", None, ws, m.end())
    # Partial "<MonthName> <Year>" — only for a real month name.
    m = _PARTIAL_MONYEAR_RE.match(line)
    if m and _MONTHS.get(m.group(1).casefold()) is not None:
        return ("partial", None, ws, m.end())
    return None


def _walk_temporal_lines(
    note: str, reference_date: datetime.date | None, resolve_relative: bool
):
    """Yield ``(line_start, kind, date_or_None, phrase_start, content_start)`` in
    WHOLE-NOTE offsets for each line with a recognized leading temporal token.
    'explicit' lines mirror parse_dated_lines exactly (phrase_start is None);
    relative/partial/frequency/unresolved lines are yielded only when
    resolve_relative is True."""
    offset = 0
    for line in note.splitlines(keepends=True):
        parsed = _parse_leading_date(line)
        if parsed is not None:
            date, content_rel = parsed
            yield (offset, "explicit", date, None, offset + content_rel)
        elif resolve_relative:
            rel = _parse_leading_relative(line, reference_date)
            if rel is not None:
                kind, date, phrase_rel, content_rel = rel
                yield (offset, kind, date, offset + phrase_rel, offset + content_rel)
        offset += len(line)


# ---------------------------------------------------------------------------
# Gazetteer matching — exact by default; synonyms and/or guarded fuzzy are opt-in
# via MatchConfig. All matches are anchored to the gazetteer (only curated
# concepts ever surface), case-insensitive, word-bounded, longest-match.
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[0-9A-Za-z]+")


def _fuzzy_candidates(
    low: str, gazetteer: list[str], config: MatchConfig
) -> list[tuple[int, int, str, int, float]]:
    """Near-match candidates: each gazetteer term compared (difflib ratio) against
    token-windows of ``low`` (already casefolded), sized to the term's token
    count +/- 1. A candidate is kept when ratio >= cutoff AND the pairing is not
    guard-blocked. Terms in ``no_fuzzy_terms`` skip fuzzy entirely (drug-name
    exemption). Returns ``(start, end, emit_term, is_fuzzy=1, ratio)``."""
    toks = [(m.start(), m.end()) for m in _WORD_RE.finditer(low)]
    out: list[tuple[int, int, str, int, float]] = []
    cutoff = config.fuzzy_cutoff
    for term in gazetteer:
        if term in config.no_fuzzy_terms:
            continue
        term_norm = _normalize(term)
        n = max(1, len(term_norm.split()))
        for size in sorted({max(1, n - 1), n, n + 1}):
            if size > len(toks):
                continue
            for i in range(0, len(toks) - size + 1):
                start = toks[i][0]
                end = toks[i + size - 1][1]
                window = low[start:end]
                if window == term_norm:
                    continue  # an exact hit; handled by the exact pass
                ratio = difflib.SequenceMatcher(None, window, term_norm).ratio()
                if ratio >= cutoff and not _violates_anti_pairing(
                    window, term_norm, config.anti_pairings
                ):
                    out.append((start, end, term, 1, ratio))
    return out


def find_gazetteer_hits(
    text: str, gazetteer: list[str], *, config: MatchConfig | None = None
) -> list[tuple[int, int, str]]:
    """All gazetteer matches in ``text`` as ``(start, end, term)``, offsets into
    ``text`` with ``end`` exclusive, sorted by start. Matching is case-insensitive,
    word-bounded (a term never matches inside a larger word), longest-match-wins
    and non-overlapping; among equal-length spans an exact/synonym hit beats a
    fuzzy one. The returned ``term`` is the gazetteer's canonical spelling (or a
    synonym's canonical), NOT the surface casing, so the same concept groups
    across dates under the engine's exact match.

    ``config`` (default strict) selects the matching mode; see MatchConfig.
    """
    config = config or MatchConfig()
    low = text.casefold()

    # Surface form (normalized) -> emitted canonical term. Gazetteer terms map to
    # themselves; declared synonyms override, so a synonym variant emits its
    # canonical. Matching the normalized surface over the casefolded text keeps
    # offsets valid (ASCII slice). Each candidate carries (is_fuzzy, ratio) for
    # the tie-break.
    emit_for: dict[str, str] = {}
    for term in gazetteer:
        emit_for[_normalize(term)] = term
    if config.mode in ("synonyms", "both"):
        for variant, canonical in config.synonyms.items():
            emit_for[_normalize(variant)] = canonical

    candidates: list[tuple[int, int, str, int, float]] = []
    for surface_norm, emit in emit_for.items():
        pattern = re.compile(
            r"(?<![0-9A-Za-z])" + re.escape(surface_norm) + r"(?![0-9A-Za-z])"
        )
        for m in pattern.finditer(low):
            candidates.append((m.start(), m.end(), emit, 0, 1.0))

    if config.mode in ("fuzzy", "both"):
        candidates.extend(_fuzzy_candidates(low, gazetteer, config))

    # Longest-match-wins; then exact/synonym (is_fuzzy=0) over fuzzy; then higher
    # ratio; then start, then term — fully deterministic. Keep non-overlapping.
    candidates.sort(key=lambda c: (-(c[1] - c[0]), c[3], -c[4], c[0], c[2]))
    accepted: list[tuple[int, int, str, int, float]] = []
    for start, end, emit, is_fuzzy, ratio in candidates:
        if any(start < a_end and a_start < end for a_start, a_end, *_ in accepted):
            continue
        accepted.append((start, end, emit, is_fuzzy, ratio))
    accepted.sort(key=lambda c: c[0])
    return [(s, e, emit) for s, e, emit, _is_fuzzy, _ratio in accepted]


# ---------------------------------------------------------------------------
# Identity (record id) — the "Patient:" header value, taken verbatim and never
# gazetteer-scanned (the allowlist, ADR 0009).
# ---------------------------------------------------------------------------

_PATIENT_RE = re.compile(r"\s*Patient:\s*(.+?)\s*$")


def parse_patient_id(note: str) -> str | None:
    """The record id from a ``Patient: <value>`` header line (first one wins),
    stripped and taken VERBATIM. Returns None if absent. The value is never
    gazetteer-matched, so an identifier on the header line cannot become an
    entry."""
    for line in note.splitlines():
        m = _PATIENT_RE.match(line)
        if m:
            return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Extraction — prose -> canonical entries / records.
# ---------------------------------------------------------------------------


def extract_entries(
    note: str,
    gazetteer: list[str],
    *,
    date_shift_days: int = 0,
    config: MatchConfig | None = None,
    resolve_relative: bool = False,
    reference_date: datetime.date | None = None,
) -> list[dict]:
    """The flat list of ``{date, item, source_span}`` entries for ``note`` (no
    record wrapper). One entry per gazetteer hit on a dated line, in document
    order. ``config`` (default strict) selects the matching mode. Dates are
    shifted by ``date_shift_days`` (default 0) then rendered ISO; ``source_span``
    is a ``[start, end]`` character offset into the note (end exclusive) and is
    NEVER shifted.

    Relative-date anchoring is OPT-IN (``resolve_relative``; ADR 0013) and OFF by
    default. When on, a line whose leading token is a relative/partial/frequency
    expression also yields entries; those carry three additive provenance fields —
    ``date_kind`` ('relative'|'partial'|'frequency'|'unresolved'), ``date_phrase``
    (the literal temporal text) and ``date_span`` (its [start, end] offsets).
    Resolved relatives anchor to the line's explicit date if present, else
    ``reference_date``; an anchorless relative is left unresolved (``date=""``).
    Explicit-date entries are unaffected (no extra fields), so the default output
    is byte-for-byte unchanged."""
    _validate_gazetteer(gazetteer)
    _validate_shift(date_shift_days)
    _validate_relative(resolve_relative, reference_date)
    config = config or MatchConfig()
    entries: list[dict] = []
    for _line_start, kind, date, phrase_start, content_start in _walk_temporal_lines(
        note, reference_date, resolve_relative
    ):
        # Match only over the line's content (past the temporal token, up to the
        # newline), so the token itself can never be matched and a term cannot
        # cross a line boundary.
        newline = note.find("\n", content_start)
        line_end = len(note) if newline == -1 else newline
        content = note[content_start:line_end]
        shifted = (
            shift_date(date, date_shift_days).isoformat() if date is not None else ""
        )
        for rel_start, rel_end, term in find_gazetteer_hits(
            content, gazetteer, config=config
        ):
            entry = {
                "date": shifted,
                "item": term,
                "source_span": [content_start + rel_start, content_start + rel_end],
            }
            if kind != "explicit":
                entry["date_kind"] = kind
                entry["date_phrase"] = note[phrase_start:content_start]
                entry["date_span"] = [phrase_start, content_start]
            entries.append(entry)
    return entries


def extract_records(
    note: str,
    gazetteer: list[str],
    *,
    date_shift_days: int = 0,
    record_id_prefix: str = "",
    config: MatchConfig | None = None,
    resolve_relative: bool = False,
    reference_date: datetime.date | None = None,
) -> list[dict]:
    """Turn one prose note into canonical records (slice 1: exactly one record,
    keyed by the ``Patient:`` header). Returns ``[]`` when there is no header.
    The list return type leaves multi-patient notes a non-breaking future slice.

    The output is the shape recurrence.py's rules already consume; ``source_span``
    is an additive optional field the rules ignore (the ``tag`` precedent).
    ``resolve_relative`` / ``reference_date`` enable opt-in relative-date anchoring
    (ADR 0013; see extract_entries)."""
    _validate_gazetteer(gazetteer)
    _validate_shift(date_shift_days)
    _validate_relative(resolve_relative, reference_date)
    config = config or MatchConfig()
    rid = parse_patient_id(note)
    if rid is None:
        return []
    entries = extract_entries(
        note,
        gazetteer,
        date_shift_days=date_shift_days,
        config=config,
        resolve_relative=resolve_relative,
        reference_date=reference_date,
    )
    return [{"id": f"{record_id_prefix}{rid}", "entries": entries}]


# ---------------------------------------------------------------------------
# Multi-patient extraction (slice 3; FAIL-CLOSED on identity — see ADR 0016).
# One input may hold several patients. We split ONLY on an explicit, operator-
# supplied delimiter and accept a segment ONLY when its identity is unambiguous;
# a segment with no key, with two or more DISTINCT keys, or whose key collides
# with another segment is QUARANTINED (refused), never merged or guessed. This is
# the deterministic analogue of "abstain under uncertainty": when attribution is
# unclear, refuse rather than risk patient mis-attribution / record bleed (the
# dominant documented risk). recurrence.run_report already groups by record_id and
# every rule is per-record, so N correctly-keyed records Just Work; the only new
# job is producing them safely. extract_records (single-note) is left untouched.
# ---------------------------------------------------------------------------

# Fixed, neutral provenance tokens (librarian rule): a refusal reason is never an
# interpretation. missing_key = no Patient: header; ambiguous_key = >=2 distinct
# headers in one segment; duplicate_key = a key shared across segments (ALL
# colliding segments are refused, never merged); missing_shift = require_shift is
# on and no per-patient shift was supplied (de-identification would be partial).
_QUARANTINE_REASONS = ("missing_key", "ambiguous_key", "duplicate_key", "missing_shift")


@dataclass
class QuarantinedSegment:
    """One refused segment, stamped with NEUTRAL provenance only (librarian rule).

    ``index`` is the 0-based segment ordinal; ``reason`` is one of
    ``_QUARANTINE_REASONS``; ``char_offset`` is the segment's start offset in the
    whole note; ``detail`` is a neutral, non-interpretive note (a count or which
    key collided) and must stay free of interpretive/banned words."""

    index: int
    reason: str
    char_offset: int = 0
    detail: str = ""


@dataclass
class MultiExtractResult:
    """The outcome of a multi-patient split. ``records`` are the accepted canonical
    records (each a normal {id, entries} plus an additive ``provenance`` block the
    engine ignores); ``quarantined`` lists the refused segments in segment order.
    Bad DATA never raises (fail-closed = quarantine); only bad CONFIG raises."""

    records: list[dict]
    quarantined: list[QuarantinedSegment]


def _validate_delimiter(delimiter: str) -> None:
    """The segment delimiter must be an explicit, non-empty, non-whitespace string
    — segment boundaries are never guessed (fail loudly on bad config)."""
    if not isinstance(delimiter, str) or delimiter.strip() == "":
        raise ValueError(
            f"delimiter must be a non-empty, non-whitespace string, got {delimiter!r}"
        )


def parse_patient_ids(segment: str, *, base_offset: int = 0) -> list[tuple[str, int]]:
    """Every ``Patient: <value>`` header in ``segment`` as ``(value, value_start)``
    in document order, where ``value_start`` is the WHOLE-NOTE char offset of the
    value (add ``base_offset`` to the in-segment position). Values are stripped and
    taken VERBATIM, never gazetteer-scanned (the allowlist, ADR 0009). Distinct
    detection is the caller's job; this returns EVERY header so a segment with two
    different headers can be recognized as ambiguous. ``parse_patient_id`` (first
    wins) is left untouched for the single-note path."""
    out: list[tuple[str, int]] = []
    offset = 0
    for line in segment.splitlines(keepends=True):
        m = _PATIENT_RE.match(line)
        if m:
            out.append((m.group(1), base_offset + offset + m.start(1)))
        offset += len(line)
    return out


def _segment_note(note: str, delimiter: str) -> list[tuple[int, str]]:
    """Split ``note`` on the literal ``delimiter`` into ``(start_offset, text)``
    pairs, where ``start_offset`` is the segment's char offset in the whole note
    (so per-segment spans can be rebased to whole-note offsets). The delimiter
    text is NOT part of any segment. The preamble before the first delimiter is
    segment 0 — never special-cased to attach to the first patient."""
    segments: list[tuple[int, str]] = []
    pos = 0
    while True:
        hit = note.find(delimiter, pos)
        if hit == -1:
            segments.append((pos, note[pos:]))
            break
        segments.append((pos, note[pos:hit]))
        pos = hit + len(delimiter)
    return segments


def extract_records_multi(
    note: str,
    gazetteer: list[str],
    *,
    delimiter: str,
    shift_by_id: dict[str, int] | None = None,
    require_shift: bool = False,
    record_id_prefix: str = "",
    config: MatchConfig | None = None,
    resolve_relative: bool = False,
    reference_date: datetime.date | None = None,
) -> MultiExtractResult:
    """Split a multi-patient note on an EXPLICIT ``delimiter`` and extract one
    canonical record per segment, FAIL-CLOSED on identity (ADR 0016).

    A segment is accepted ONLY when it carries exactly one DISTINCT ``Patient:``
    header value AND that key does not collide with another segment; otherwise it
    is quarantined (``missing_key`` / ``ambiguous_key`` / ``duplicate_key``),
    never merged or guessed — identity is never inferred from prose. ``shift_by_id``
    maps a RAW patient key (pre-prefix) to its per-patient de-identifying day
    offset (a consistent per-patient shift preserves intervals while obscuring the
    calendar, ADR 0009); when ``require_shift`` is True an accepted key with no
    shift is quarantined (``missing_shift``) so de-identification can never be
    partial; when False (default) a missing shift is 0 (the single-note convention).

    Each accepted record carries an additive ``provenance`` block (segment index +
    whole-note spans) the engine ignores (the ``tag``/``source_span`` precedent).
    ``source_span``/``date_span`` are rebased to WHOLE-NOTE offsets, so they recover
    their text against ``note`` exactly as the single-note path does.

    Bad DATA never raises (fail-closed = quarantine); only bad CONFIG raises
    (empty/whitespace delimiter; non-dict ``shift_by_id`` or a bad shift value;
    non-bool ``require_shift``)."""
    _validate_gazetteer(gazetteer)
    _validate_delimiter(delimiter)
    _validate_relative(resolve_relative, reference_date)
    if not isinstance(require_shift, bool):
        raise ValueError(f"require_shift must be a bool, got {require_shift!r}")
    if shift_by_id is not None:
        if not isinstance(shift_by_id, dict):
            raise ValueError(f"shift_by_id must be a dict, got {shift_by_id!r}")
        for value in shift_by_id.values():
            _validate_shift(value)
    shifts = shift_by_id or {}
    config = config or MatchConfig()

    # Pass 1: classify each segment. Candidates (exactly one distinct key) are
    # collected as (index, start, text, key, key_span) so a cross-segment duplicate
    # key can be detected before anything is accepted.
    candidates: list[tuple[int, int, str, str, list[int]]] = []
    quarantined: list[QuarantinedSegment] = []
    for index, (start, text) in enumerate(_segment_note(note, delimiter)):
        headers = parse_patient_ids(text, base_offset=start)
        distinct = {value for value, _ in headers}
        if not distinct:
            quarantined.append(
                QuarantinedSegment(index, "missing_key", start, "no Patient: header")
            )
        elif len(distinct) >= 2:
            quarantined.append(
                QuarantinedSegment(
                    index, "ambiguous_key", start, f"{len(distinct)} distinct headers"
                )
            )
        else:
            value, value_start = headers[0]
            key_span = [value_start, value_start + len(value)]
            candidates.append((index, start, text, value, key_span))

    # Pass 2: a key shared by >1 candidate is a collision — quarantine ALL colliding
    # segments (run_report groups by record_id, so a shared id would merge two
    # patients = the bleed we refuse). Then apply the per-patient shift policy.
    key_counts = Counter(key for _, _, _, key, _ in candidates)
    records: list[dict] = []
    for index, start, text, key, key_span in candidates:
        if key_counts[key] > 1:
            quarantined.append(
                QuarantinedSegment(index, "duplicate_key", start, "key shared across segments")
            )
            continue
        if require_shift and key not in shifts:
            quarantined.append(
                QuarantinedSegment(index, "missing_shift", start, "no per-patient shift supplied")
            )
            continue
        seg_entries = extract_entries(
            text,
            gazetteer,
            date_shift_days=shifts.get(key, 0),
            config=config,
            resolve_relative=resolve_relative,
            reference_date=reference_date,
        )
        for entry in seg_entries:  # rebase spans to whole-note offsets
            s, e = entry["source_span"]
            entry["source_span"] = [s + start, e + start]
            if "date_span" in entry:
                ds, de = entry["date_span"]
                entry["date_span"] = [ds + start, de + start]
        records.append(
            {
                "id": f"{record_id_prefix}{key}",
                "entries": seg_entries,
                "provenance": {
                    "segment_index": index,
                    "segment_span": [start, start + len(text)],
                    "patient_key_span": key_span,
                },
            }
        )

    quarantined.sort(key=lambda q: q.index)
    return MultiExtractResult(records=records, quarantined=quarantined)


def format_entry(entry: dict) -> str:
    """Render one entry as a neutral provenance line for ``--demo``. Surfaces the
    date (or, for opt-in relative entries, the cited temporal phrase + kind), the
    literal item, and the source span; it interprets nothing."""
    span = entry.get("source_span")
    where = f"@{span}" if span is not None else ""
    date = entry.get("date", "")
    kind = entry.get("date_kind")
    if kind:
        prefix = f"{date} " if date else ""
        date_field = f'{prefix}[{kind}: "{entry.get("date_phrase", "")}"]'
    else:
        date_field = date
    return f'{date_field}  "{entry.get("item", "")}"  {where}'.rstrip()


# ---------------------------------------------------------------------------
# Demo / self-test / CLI — extract.py owns its own entry point so the dependency
# runs front-end -> librarian (recurrence.py never imports this module).
# ---------------------------------------------------------------------------

MODE_DOC = """\
Free-text matching modes (you MUST choose one; default is strict).

Matching decides which gazetteer concept a stretch of note text counts as. It is
fragile in clinical text, so it is an explicit, opt-in choice, not a hidden default.

  strict    Exact, case-insensitive, whole-word, longest-match only.
            Safest. No paraphrase, no typo tolerance. (Default.)

  synonyms  strict + a curated {variant -> canonical} map YOU supply. Catches
            paraphrase ("trouble sleeping" -> "poor sleep"). Reviewable: every
            pairing is explicit and human-vetted. An affix-antonym pairing
            (e.g. stable -> unstable) is refused.

  fuzzy     strict + near-match (difflib) of text against gazetteer terms, above
            a cutoff YOU set. Catches typos. RISK: string similarity cannot tell
            a typo from an opposite ("hypertension" vs "hypotension"), so matches
            are guarded by an affix-antonym detector + a look-alike denylist, and
            drug names can be exempted (no_fuzzy_terms). Use a high cutoff; review.

  both      synonyms + fuzzy together (guards still apply).

Guards are always on in fuzzy/both; strict is always the safe default. This is a
transparency / human-control aid, NOT a guarantee — review surfaced matches.
"""


def _config_for_mode(mode: str) -> MatchConfig:
    """Build a demo MatchConfig for ``mode`` using the sample fixtures."""
    from data.sample_records import FREETEXT_SYNONYMS

    if mode == "strict":
        return MatchConfig()
    if mode == "synonyms":
        return MatchConfig(mode="synonyms", synonyms=FREETEXT_SYNONYMS)
    if mode == "fuzzy":
        return MatchConfig(mode="fuzzy", fuzzy_cutoff=0.9)
    if mode == "both":
        return MatchConfig(mode="both", synonyms=FREETEXT_SYNONYMS, fuzzy_cutoff=0.9)
    raise ValueError(f"unknown mode {mode!r}")


def _run_demo(config: MatchConfig) -> int:
    """Show the bridge: prose -> extracted entries -> the engine surfaces a
    recurrence. Uses the synthetic sample from data/sample_records.py."""
    from data.sample_records import FREETEXT_GAZETTEER, FREETEXT_SAMPLE_NOTE

    print(f"Matching mode: {config.mode}")
    print("Source note:")
    print(FREETEXT_SAMPLE_NOTE)
    records = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, config=config)
    print("Extracted entries (literal mentions, cited — not interpreted):")
    for entry in records[0]["entries"]:
        print(f"  {format_entry(entry)}")
    print()
    print("Fed to the engine (detect_recurrence), it surfaces:")
    hits = detect_recurrence(records)
    if not hits:
        print("  (nothing recurs)")
    for hit in hits:
        print(f'  "{hit.item}" appears {hit.count}x — {", ".join(hit.dates)}')
    return 0


def _run_demo_relative(reference_date: datetime.date) -> int:
    """Opt-in relative-date demo (ADR 0013): resolve explicitly-anchored relatives
    against ``reference_date``, surface partial/frequency/unresolved phrases cited
    but undated, then show the engine consuming the records unchanged."""
    from data.sample_records import FREETEXT_GAZETTEER, FREETEXT_RELATIVE_NOTE

    print(f"Reference (anchor) date: {reference_date.isoformat()}")
    print("Source note:")
    print(FREETEXT_RELATIVE_NOTE)
    records = extract_records(
        FREETEXT_RELATIVE_NOTE,
        FREETEXT_GAZETTEER,
        resolve_relative=True,
        reference_date=reference_date,
    )
    print("Extracted entries (literal mention + cited temporal phrase; not interpreted):")
    for entry in records[0]["entries"]:
        print(f"  {format_entry(entry)}")
    print()
    print("Fed to the engine (detect_recurrence), it surfaces:")
    hits = detect_recurrence(records)
    if not hits:
        print("  (nothing recurs)")
    for hit in hits:
        print(f'  "{hit.item}" appears {hit.count}x — {", ".join(hit.dates)}')
    return 0


def _run_demo_multi() -> int:
    """Multi-patient demo (ADR 0016): split the synthetic batch on its explicit
    delimiter, show the accepted (cited, fail-closed) records and the neutral
    quarantine report, then feed ONLY the accepted records to the engine —
    quarantined segments never reach it."""
    from data.sample_records import (
        FREETEXT_GAZETTEER,
        FREETEXT_MULTI_DELIMITER,
        FREETEXT_MULTI_NOTE,
        FREETEXT_MULTI_SHIFTS,
    )
    from recurrence import format_report, run_report

    print("Source note (multi-patient batch):")
    print(FREETEXT_MULTI_NOTE)
    print(f"Explicit delimiter: {FREETEXT_MULTI_DELIMITER!r}")
    print()
    result = extract_records_multi(
        FREETEXT_MULTI_NOTE,
        FREETEXT_GAZETTEER,
        delimiter=FREETEXT_MULTI_DELIMITER,
        shift_by_id=FREETEXT_MULTI_SHIFTS,
    )
    print("Accepted records (cited, de-identified, fail-closed on identity):")
    for record in result.records:
        prov = record["provenance"]
        print(f'  {record["id"]}  (segment {prov["segment_index"]})')
        for entry in record["entries"]:
            print(f"    {format_entry(entry)}")
    print()
    print("Quarantined segments (refused — neutral provenance only):")
    if not result.quarantined:
        print("  (none)")
    for q in result.quarantined:
        detail = f" ({q.detail})" if q.detail else ""
        print(f"  segment {q.index} @offset {q.char_offset}: {q.reason}{detail}")
    print()
    print("Fed to the engine (run_report) — quarantined segments never reach it:")
    text = format_report(run_report(result.records))
    print(text if text else "  (nothing surfaces)")
    return 0


def _run_self_test() -> int:
    """Slice-2 spec check: each matching mode against the hand-written oracle, the
    fuzzy guard, and the date shift. Returns 0 on success, non-zero on failure."""
    from data.sample_records import (
        FREETEXT_EXPECTED_RECORDS,
        FREETEXT_EXPECTED_RECORDS_RELATIVE,
        FREETEXT_EXPECTED_RECORDS_SYNONYMS,
        FREETEXT_GAZETTEER,
        FREETEXT_RELATIVE_NOTE,
        FREETEXT_SAMPLE_NOTE,
        FREETEXT_SYNONYMS,
    )

    results: list[tuple[str, bool]] = []

    strict = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
    results.append(("strict_extracts_match_oracle", strict == FREETEXT_EXPECTED_RECORDS))
    strict_by = {h.item: h for h in detect_recurrence(strict)}
    results.append(
        (
            "strict_bridge_surfaces_recurrence",
            "poor sleep" in strict_by and strict_by["poor sleep"].count == 2,
        )
    )

    syn = extract_records(
        FREETEXT_SAMPLE_NOTE,
        FREETEXT_GAZETTEER,
        config=MatchConfig(mode="synonyms", synonyms=FREETEXT_SYNONYMS),
    )
    results.append(
        ("synonyms_extracts_match_oracle", syn == FREETEXT_EXPECTED_RECORDS_SYNONYMS)
    )
    syn_by = {h.item: h for h in detect_recurrence(syn)}
    results.append(
        (
            "synonyms_merge_lifts_count",
            "poor sleep" in syn_by and syn_by["poor sleep"].count == 3,
        )
    )

    typo = find_gazetteer_hits(
        "poor slep", ["poor sleep"], config=MatchConfig(mode="fuzzy", fuzzy_cutoff=0.9)
    )
    results.append(("fuzzy_merges_typo", typo == [(0, 9, "poor sleep")]))

    blocked = find_gazetteer_hits(
        "hypertension", ["hypotension"], config=MatchConfig(mode="fuzzy", fuzzy_cutoff=0.8)
    )
    results.append(("fuzzy_blocks_affix_antonym", blocked == []))

    shifted = extract_records(
        FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, date_shift_days=10_000
    )
    shifted_by = {h.item: h for h in detect_recurrence(shifted)}
    results.append(
        (
            "shift_preserves_recurrence",
            "poor sleep" in shifted_by and shifted_by["poor sleep"].count == 2,
        )
    )

    # Relative-date anchoring (opt-in; ADR 0013).
    rel = extract_records(
        FREETEXT_RELATIVE_NOTE,
        FREETEXT_GAZETTEER,
        resolve_relative=True,
        reference_date=datetime.date(2026, 3, 15),
    )
    results.append(
        ("relative_extracts_match_oracle", rel == FREETEXT_EXPECTED_RECORDS_RELATIVE)
    )
    rel_off = extract_records(FREETEXT_RELATIVE_NOTE, FREETEXT_GAZETTEER)
    results.append(
        (
            "relative_default_off_skips_unanchored",
            len(rel_off[0]["entries"]) == 1
            and "date_kind" not in rel_off[0]["entries"][0],
        )
    )
    unresolved = extract_entries(
        "3 weeks ago poor sleep.\n", FREETEXT_GAZETTEER, resolve_relative=True
    )
    results.append(
        (
            "relative_unresolved_without_anchor",
            len(unresolved) == 1
            and unresolved[0]["date"] == ""
            and unresolved[0]["date_kind"] == "unresolved",
        )
    )

    failures = [name for name, ok in results if not ok]
    if failures:
        print(f"FAILED ({len(failures)}):", file=sys.stderr)
        for name in failures:
            print(f"  - {name}", file=sys.stderr)
        return 1
    print(f"OK: {len(results)} scenarios passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Free-text extraction front-end (slice 2) — turn dated prose "
        "into the engine's canonical records. Surfaces literal mentions with "
        "provenance; never interprets (Stance A, strict literal). Matching mode "
        "is an explicit choice (see --explain-modes).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--version",
        action="store_true",
        help="Print the front-end name and version, then exit",
    )
    p.add_argument(
        "--explain-modes",
        action="store_true",
        help="Explain the matching modes (strict/synonyms/fuzzy/both) and exit",
    )
    p.add_argument(
        "--match-mode",
        choices=list(_MODES),
        default="strict",
        help="Matching mode for --demo (default: strict). See --explain-modes.",
    )
    p.add_argument(
        "--self-test",
        action="store_true",
        help="Check extraction against the hand-written oracle + the fuzzy guard",
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="Extract the sample note and show the engine surfacing a recurrence",
    )
    p.add_argument(
        "--demo-multi",
        action="store_true",
        help="Multi-patient fail-closed demo: split a synthetic batch on an "
        "explicit delimiter, show accepted records + the quarantine report (ADR 0016)",
    )
    p.add_argument(
        "--reference-date",
        metavar="YYYY-MM-DD",
        default=None,
        help="Anchor (encounter/document) date; runs the opt-in relative-date "
        "demo on the relative sample note (ADR 0013).",
    )
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.version:
        print(f"Health-Prototype extraction front-end {VERSION}")
        return 0
    if args.explain_modes:
        print(MODE_DOC)
        return 0
    if args.self_test:
        return _run_self_test()
    if args.reference_date is not None:
        try:
            ref = datetime.date.fromisoformat(args.reference_date)
        except ValueError:
            print(
                f"invalid --reference-date {args.reference_date!r} (use YYYY-MM-DD)",
                file=sys.stderr,
            )
            return 2
        return _run_demo_relative(ref)
    if args.demo_multi:
        return _run_demo_multi()
    if args.demo:
        return _run_demo(_config_for_mode(args.match_mode))
    build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
