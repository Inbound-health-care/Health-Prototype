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

Deferred to later slices (researched, intentionally not built): relative dates
("3 weeks ago") need an anchor; multi-patient notes.

  Self-test:      python extract.py --self-test
  Demo:           python extract.py --demo [--match-mode {strict,synonyms,fuzzy,both}]
  Explain modes:  python extract.py --explain-modes
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import re
import sys
from dataclasses import dataclass

from recurrence import _check_fuzzy_cutoff, _normalize, detect_recurrence

# Front-end version — independent of the engine's VERSION. Bump on a
# user-visible change to extraction behavior.
VERSION = "0.2.0"


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
# Date extraction — explicit dates only. Relative/incomplete expressions
# ("today", "3 weeks ago") need an anchor date and are deferred (see ADR 0008).
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
) -> list[dict]:
    """The flat list of ``{date, item, source_span}`` entries for ``note`` (no
    record wrapper). One entry per gazetteer hit on a dated line, in document
    order. ``config`` (default strict) selects the matching mode. Dates are
    shifted by ``date_shift_days`` (default 0) then rendered ISO; ``source_span``
    is a ``[start, end]`` character offset into the note (end exclusive) and is
    NEVER shifted."""
    _validate_gazetteer(gazetteer)
    _validate_shift(date_shift_days)
    config = config or MatchConfig()
    entries: list[dict] = []
    for _line_start, date, content_start in parse_dated_lines(note):
        # Match only over the line's content (past the date token, up to the
        # newline), so the date itself can never be matched and a term cannot
        # cross a line boundary.
        newline = note.find("\n", content_start)
        line_end = len(note) if newline == -1 else newline
        content = note[content_start:line_end]
        shifted = shift_date(date, date_shift_days).isoformat()
        for rel_start, rel_end, term in find_gazetteer_hits(
            content, gazetteer, config=config
        ):
            entries.append(
                {
                    "date": shifted,
                    "item": term,
                    "source_span": [content_start + rel_start, content_start + rel_end],
                }
            )
    return entries


def extract_records(
    note: str,
    gazetteer: list[str],
    *,
    date_shift_days: int = 0,
    record_id_prefix: str = "",
    config: MatchConfig | None = None,
) -> list[dict]:
    """Turn one prose note into canonical records (slice 1: exactly one record,
    keyed by the ``Patient:`` header). Returns ``[]`` when there is no header.
    The list return type leaves multi-patient notes a non-breaking future slice.

    The output is the shape recurrence.py's rules already consume; ``source_span``
    is an additive optional field the rules ignore (the ``tag`` precedent)."""
    _validate_gazetteer(gazetteer)
    _validate_shift(date_shift_days)
    config = config or MatchConfig()
    rid = parse_patient_id(note)
    if rid is None:
        return []
    entries = extract_entries(
        note, gazetteer, date_shift_days=date_shift_days, config=config
    )
    return [{"id": f"{record_id_prefix}{rid}", "entries": entries}]


def format_entry(entry: dict) -> str:
    """Render one entry as a neutral provenance line for ``--demo``. Surfaces the
    date, the literal item, and the source span; it interprets nothing."""
    span = entry.get("source_span")
    where = f"@{span}" if span is not None else ""
    return f'{entry.get("date", "")}  "{entry.get("item", "")}"  {where}'.rstrip()


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


def _run_self_test() -> int:
    """Slice-2 spec check: each matching mode against the hand-written oracle, the
    fuzzy guard, and the date shift. Returns 0 on success, non-zero on failure."""
    from data.sample_records import (
        FREETEXT_EXPECTED_RECORDS,
        FREETEXT_EXPECTED_RECORDS_SYNONYMS,
        FREETEXT_GAZETTEER,
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
    if args.demo:
        return _run_demo(_config_for_mode(args.match_mode))
    build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
