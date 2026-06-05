#!/usr/bin/env python3
"""
extract.py — Free-text extraction FRONT-END (deterministic, slice 1)
====================================================================

Pure-stdlib. Zero external dependencies. Local-only (no network egress).

Turns dated-line prose notes into the recurrence engine's canonical record shape
{id, entries:[{date, item, source_span}]} — which recurrence.py's five surfacing
rules then consume UNCHANGED. Extraction is a front door to the librarian; it is
NOT part of the librarian. The engine and its tests are untouched, and the
dependency runs one way: extract.py imports recurrence.py, never the reverse.

Stance A — strict literal (chosen by the operator; see ADR 0008): emit every
exact, word-bounded, longest-match gazetteer hit on a dated line, with its
character-offset provenance. NO cue logic, NO presence/absence/ownership
judgment: "chest pain" is emitted from "Denies chest pain" — the firewall point.
Filtering a mention is the human's job, done on the cited provenance.

Firewall, by construction (see ADR 0009 — NOT legal advice):
  - Allowlist (HIPAA Safe Harbor): only curated gazetteer concepts can surface,
    so names / SSNs / MRNs and the other identifiers are structurally
    un-extractable. The "Patient:" header value becomes the record id and is
    never gazetteer-scanned.
  - Dates de-identified by a consistent per-record shift (an Expert-Determination
    technique): every date moves by the same offset, so intervals are preserved
    and the engine's date math survives while the calendar is obscured. The
    default shift is 0 (unshifted).

Deferred to later slices (researched, intentionally not built): relative dates
("3 weeks ago") need an anchor; fuzzy/synonym gazetteer matching reuses the
engine's existing v1 layer as an opt-in; multi-patient notes.

  Self-test:  python extract.py --self-test
  Demo:       python extract.py --demo
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys

from recurrence import detect_recurrence

# Front-end version — independent of the engine's VERSION. Bump on a
# user-visible change to extraction behavior.
VERSION = "0.1.0"


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
# Gazetteer matching — exact, case-insensitive, word-bounded, longest-match.
# Fuzzy/synonym matching is deferred to a later slice via the engine's v1 layer.
# ---------------------------------------------------------------------------


def find_gazetteer_hits(text: str, gazetteer: list[str]) -> list[tuple[int, int, str]]:
    """All literal gazetteer matches in ``text`` as ``(start, end, term)``, with
    offsets into ``text`` and ``end`` exclusive. Matching is case-insensitive,
    word-bounded (a term never matches inside a larger word), longest-match-wins
    and non-overlapping; results are sorted by start.

    The returned ``term`` is the gazetteer's canonical spelling, NOT the surface
    casing, so the same concept groups across dates under the engine's exact
    match (e.g. "Poor sleep" and "poor sleep" both group as "poor sleep").
    """
    # Match on a case-folded copy. For ASCII (this slice) casefold is length-
    # preserving, so positions in `low` are valid offsets into `text`; surface
    # strings always come from `text`. A non-ASCII slice should instead match the
    # original text with re.IGNORECASE (no separate lowered copy).
    low = text.casefold()
    candidates: list[tuple[int, int, str]] = []
    for term in gazetteer:
        # Word boundaries on [0-9A-Za-z] only (explicit, not \b): "sleep" must
        # not match inside "asleep"/"sleeps", while "chest pain"'s internal space
        # is unaffected (only the term's outer edges are guarded).
        pattern = re.compile(
            r"(?<![0-9A-Za-z])" + re.escape(term.casefold()) + r"(?![0-9A-Za-z])"
        )
        for m in pattern.finditer(low):
            candidates.append((m.start(), m.end(), term))

    # Longest-match-wins, non-overlapping. Sort by descending length, then start,
    # then term, so greedy acceptance is fully deterministic; then keep a
    # candidate only if it does not overlap one already accepted.
    candidates.sort(key=lambda c: (-(c[1] - c[0]), c[0], c[2]))
    accepted: list[tuple[int, int, str]] = []
    for start, end, term in candidates:
        if any(start < a_end and a_start < end for a_start, a_end, _ in accepted):
            continue
        accepted.append((start, end, term))
    accepted.sort(key=lambda c: c[0])
    return accepted


# ---------------------------------------------------------------------------
# Identity (record id) — the "Patient:" header value, taken verbatim and never
# gazetteer-scanned (the allowlist firewall, ADR 0009).
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
) -> list[dict]:
    """The flat list of ``{date, item, source_span}`` entries for ``note`` (no
    record wrapper). One entry per gazetteer hit on a dated line, in document
    order. Dates are shifted by ``date_shift_days`` (default 0) then rendered
    ISO; ``source_span`` is a ``[start, end]`` character offset into the note
    (end exclusive) and is NEVER shifted."""
    _validate_gazetteer(gazetteer)
    _validate_shift(date_shift_days)
    entries: list[dict] = []
    for _line_start, date, content_start in parse_dated_lines(note):
        # Match only over the line's content (past the date token, up to the
        # newline), so the date itself can never be matched and a term cannot
        # cross a line boundary.
        newline = note.find("\n", content_start)
        line_end = len(note) if newline == -1 else newline
        content = note[content_start:line_end]
        shifted = shift_date(date, date_shift_days).isoformat()
        for rel_start, rel_end, term in find_gazetteer_hits(content, gazetteer):
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
) -> list[dict]:
    """Turn one prose note into canonical records (slice 1: exactly one record,
    keyed by the ``Patient:`` header). Returns ``[]`` when there is no header.
    The list return type leaves multi-patient notes a non-breaking future slice.

    The output is the shape recurrence.py's rules already consume; ``source_span``
    is an additive optional field the rules ignore (the ``tag`` precedent)."""
    _validate_gazetteer(gazetteer)
    _validate_shift(date_shift_days)
    rid = parse_patient_id(note)
    if rid is None:
        return []
    entries = extract_entries(note, gazetteer, date_shift_days=date_shift_days)
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


def _run_demo() -> int:
    """Show the bridge: prose -> extracted entries -> the engine surfaces a
    recurrence. Uses the synthetic sample from data/sample_records.py."""
    from data.sample_records import FREETEXT_GAZETTEER, FREETEXT_SAMPLE_NOTE

    print("Source note:")
    print(FREETEXT_SAMPLE_NOTE)
    records = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
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
    """Slice-1 spec check: extraction equals the hand-written oracle, the records
    bridge into the engine, and a date shift preserves the recurrence. Returns 0
    on success, non-zero on failure."""
    from data.sample_records import (
        FREETEXT_EXPECTED_RECORDS,
        FREETEXT_GAZETTEER,
        FREETEXT_SAMPLE_NOTE,
    )

    results: list[tuple[str, bool]] = []

    records = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
    results.append(("extracts_match_oracle", records == FREETEXT_EXPECTED_RECORDS))

    by_item = {h.item: h for h in detect_recurrence(records)}
    results.append(
        (
            "bridge_surfaces_recurrence",
            "poor sleep" in by_item and by_item["poor sleep"].count == 2,
        )
    )

    shifted = extract_records(
        FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, date_shift_days=10_000
    )
    shifted_items = {h.item: h for h in detect_recurrence(shifted)}
    results.append(
        (
            "shift_preserves_recurrence",
            "poor sleep" in shifted_items and shifted_items["poor sleep"].count == 2,
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
        description="Free-text extraction front-end (slice 1) — turn dated prose "
        "into the engine's canonical records. Surfaces literal mentions with "
        "provenance; never interprets (Stance A, strict literal).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--version",
        action="store_true",
        help="Print the front-end name and version, then exit",
    )
    p.add_argument(
        "--self-test",
        action="store_true",
        help="Check extraction against the hand-written oracle + the engine bridge",
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
    if args.self_test:
        return _run_self_test()
    if args.demo:
        return _run_demo()
    build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
