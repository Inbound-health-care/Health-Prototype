#!/usr/bin/env python3
"""
audit.py — governance audit trail + deterministic monitor (VERSION 0.1.0)
==========================================================================

Pure-stdlib. Zero external dependencies. Local-only (no network egress).
Stage 1 of the ADR 0029 rollout; decision record ADR 0030.

An append-only, hash-chained, tamper-EVIDENT record of what the engine surfaced:
one event per audited run (extract / extract_multi / report) carrying DIGESTS
and per-lens COUNTS — never note text, item values, or any clinical content
(OWASP logging guidance: the trail must stay safe to keep even where the data
it describes is not). "Why did the system surface this six months ago?" is then
answerable with proof: the output you hold re-hashes to what the trail recorded.

Like everything in this repo, the trail is a LIBRARIAN: it records, counts, and
cites; it never scores, ranks, or interprets. The monitor half (`summarize` /
`compare`) reports counts and differences as data — judgment stays human.

Chain construction (RFC 6962 lineage; evidence in
docs/RESEARCH_2026-06-11_audit-trail-standards.md):

    entry_hash = SHA-256(prev_hash + "\\n" + canonical_json(event))

with canonical JSON as the stdlib RFC 8785 approximation (sorted keys, tight
separators, ASCII) — floats are REJECTED by validation, since float repr is the
known canonicalization hazard. Honest limits, stated plainly: the chain detects
in-place edits, insertion, deletion, and reordering anywhere before the tail;
TAIL TRUNCATION and WHOLE-FILE REWRITE are detectable only against an externally
recorded head — call `head()` (CLI `--head`) and publish the value outside the
file (a commit message, a PR, a printed run log). Single-writer by design: the
stdlib has no portable file lock, so concurrent writers are out of scope.

This module imports the engine and the extractor (a front door, like the views);
they never import it back.

  Self-test:  python audit.py --self-test
  Demo:       python audit.py --demo
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

import extract
import recurrence

# Module version — surfaced by `--version`; bump on a user-visible release.
VERSION = "0.1.0"

# The chain's fixed genesis: the "previous hash" of the first entry. A constant
# (not empty) so a verifier can distinguish "first entry" from "missing field".
GENESIS_HASH = "0" * 64

# Fixed, neutral event types (librarian rule: provenance tokens, never labels of
# meaning). One per audited front door.
EVENT_TYPES = ("extract", "extract_multi", "report")


# ---------------------------------------------------------------------------
# Canonical JSON + hashing — deterministic bytes or a loud failure
# ---------------------------------------------------------------------------


def canonical_json(obj: object) -> str:
    """Serialize ``obj`` to the stdlib approximation of RFC 8785 canonical JSON.

    Sorted keys + tight separators + ASCII escapes make the bytes deterministic
    across runs and platforms — PROVIDED no float is present (float repr is the
    known divergence; `_check_no_floats` rejects them before anything is hashed).
    Non-serializable input raises ValueError (library code fails loudly).
    """
    try:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"event is not canonically serializable: {exc}") from exc


def _check_no_floats(obj: object, path: str = "event") -> None:
    """Reject floats ANYWHERE in a nested payload (bools are ints and pass).

    Floats break byte-determinism of the canonical form (RFC 8785 minimizes
    numbers; stdlib json does not), so a float must be carried as a string
    (e.g. ``str(fuzzy_cutoff)``) — the caller decides the representation.
    """
    if type(obj) is float:
        raise ValueError(f"{path}: floats are not allowed in audit events; use str")
    if isinstance(obj, dict):
        for key, value in obj.items():
            if not isinstance(key, str):
                raise ValueError(f"{path}: non-string key {key!r}")
            _check_no_floats(value, f"{path}.{key}")
    elif isinstance(obj, (list, tuple)):
        for i, value in enumerate(obj):
            _check_no_floats(value, f"{path}[{i}]")


def sha256_text(text: str) -> str:
    """SHA-256 hex digest of a string (the trail's one-way reference to content)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _entry_hash(prev_hash: str, core: dict) -> str:
    """The chain step: SHA-256 over the previous hash + this entry's canonical bytes."""
    material = prev_hash + "\n" + canonical_json(core)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    """Wall-clock default for ``recorded`` (ISO 8601 UTC, second precision)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# The trail — append-only entries, each chained to the one before
# ---------------------------------------------------------------------------


@dataclass
class AuditEntry:
    """One immutable-by-convention event: what ran, over which input, surfacing
    how much — plus the chain fields that make editing it after the fact visible.

    Field names follow HL7 FHIR AuditEvent vocabulary as a REFERENCE (type /
    recorded / agent / entity) — a naming convention, not a compliance claim.
    ``entity`` says what the event was about, strictly by DIGEST: even record
    ids are stored as per-id SHA-256 (an extracted record's id is the patient
    key — an identifier the trail must never carry as a value). ``payload``
    carries the counts the monitor consumes. Neither ever holds clinical text.
    """

    seq: int
    recorded: str
    type: str
    agent: str
    entity: dict
    payload: dict
    prev_hash: str
    entry_hash: str

    def core(self) -> dict:
        """The hashed portion — everything except the chain fields themselves."""
        return {
            "seq": self.seq,
            "recorded": self.recorded,
            "type": self.type,
            "agent": self.agent,
            "entity": self.entity,
            "payload": self.payload,
        }


def _entry_from_line(line: str, lineno: int) -> AuditEntry:
    """Parse one stored JSONL line back into an AuditEntry (loudly on malformed)."""
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"line {lineno}: not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError(f"line {lineno}: expected an object, got {type(obj).__name__}")
    try:
        event = obj["event"]
        return AuditEntry(
            seq=event["seq"],
            recorded=event["recorded"],
            type=event["type"],
            agent=event["agent"],
            entity=event["entity"],
            payload=event["payload"],
            prev_hash=obj["prev_hash"],
            entry_hash=obj["entry_hash"],
        )
    except (KeyError, TypeError) as exc:
        raise ValueError(f"line {lineno}: missing audit field: {exc}") from exc


def read_entries(path: str) -> list[AuditEntry]:
    """Read a JSONL trail file into entries WITHOUT verifying the chain.

    Parsing and verification are separate so a verifier can REPORT a broken
    chain (CLI `--verify`) instead of refusing to look at it.
    """
    entries: list[AuditEntry] = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if line:
                entries.append(_entry_from_line(line, lineno))
    return entries


def verify_entries(entries: list[AuditEntry]) -> tuple[bool, int | None]:
    """Walk the chain; return (ok, first_bad_seq).

    Detects in-place edits, insertion, deletion, and reordering anywhere before
    the tail. It can NOT see tail truncation or a coherent whole-file rewrite —
    those need the externally recorded head (`verify_head`). That limit is the
    documented design, not an oversight.
    """
    prev = GENESIS_HASH
    for i, entry in enumerate(entries, start=1):
        if entry.seq != i:
            return False, i
        if entry.prev_hash != prev:
            return False, i
        if _entry_hash(prev, entry.core()) != entry.entry_hash:
            return False, i
        prev = entry.entry_hash
    return True, None


class AuditTrail:
    """Append-only, hash-chained event trail; in-memory, optionally persisted.

    With ``path``, every appended entry is also written as one canonical-JSON
    line (flush + fsync, single writer); re-opening an existing file verifies
    its chain and CONTINUES it — the chain never restarts. ``now`` injects the
    clock (a callable returning the ``recorded`` string) so tests and demos are
    deterministic; the default is wall-clock UTC.
    """

    def __init__(self, path: str | None = None, *, now: Callable[[], str] | None = None):
        if path is not None and not isinstance(path, str):
            raise ValueError(f"path must be a str or None, got {path!r}")
        if now is not None and not callable(now):
            raise ValueError(f"now must be callable, got {now!r}")
        self._path = path
        self._now = now or _utc_now
        self.entries: list[AuditEntry] = []
        if path is not None and os.path.exists(path) and os.path.getsize(path) > 0:
            self.entries = read_entries(path)
            ok, bad_seq = verify_entries(self.entries)
            if not ok:
                raise ValueError(f"existing trail fails verification at seq {bad_seq}")

    def head(self) -> str:
        """The chain head — record THIS value outside the file (commit, PR, log)
        to make tail truncation and whole-file rewrite detectable."""
        return self.entries[-1].entry_hash if self.entries else GENESIS_HASH

    def append(self, type_: str, *, agent: str, entity: dict, payload: dict) -> AuditEntry:
        """Append one validated, chained event; persist it if a path is set."""
        if type_ not in EVENT_TYPES:
            raise ValueError(f"type must be one of {EVENT_TYPES}, got {type_!r}")
        if not isinstance(agent, str) or not agent.strip():
            raise ValueError(f"agent must be a non-empty str, got {agent!r}")
        if not isinstance(entity, dict):
            raise ValueError(f"entity must be a dict, got {entity!r}")
        if not isinstance(payload, dict):
            raise ValueError(f"payload must be a dict, got {payload!r}")
        recorded = self._now()
        if not isinstance(recorded, str):
            raise ValueError(f"now() must return a str, got {recorded!r}")
        core = {
            "seq": len(self.entries) + 1,
            "recorded": recorded,
            "type": type_,
            "agent": agent,
            "entity": entity,
            "payload": payload,
        }
        _check_no_floats(core)
        prev = self.head()
        entry = AuditEntry(
            **core, prev_hash=prev, entry_hash=_entry_hash(prev, core)
        )
        if self._path is not None:
            line = canonical_json(
                {"event": entry.core(), "prev_hash": prev, "entry_hash": entry.entry_hash}
            )
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())
        self.entries.append(entry)
        return entry

    def verify(self) -> tuple[bool, int | None]:
        """Walk the in-memory chain; (ok, first_bad_seq). See `verify_entries`."""
        return verify_entries(self.entries)

    def verify_head(self, expected_head: str) -> bool:
        """Check the chain head against an EXTERNALLY recorded value — the only
        defense this design offers against truncation / whole-file rewrite."""
        return self.head() == expected_head


# ---------------------------------------------------------------------------
# Audited front doors — run the engine/extractor unchanged, log digests+counts
# ---------------------------------------------------------------------------


def audited_extract(trail: AuditTrail, note: str, gazetteer: list[str], **kwargs) -> list[dict]:
    """`extract.extract_records` + one trail event. Results pass through UNTOUCHED."""
    records = extract.extract_records(note, gazetteer, **kwargs)
    config = kwargs.get("config")
    trail.append(
        "extract",
        agent=f"extract {extract.VERSION}",
        entity={
            "input_sha256": sha256_text(note),
            "gazetteer_sha256": sha256_text(canonical_json(gazetteer)),
            "config_repr_sha256": sha256_text(repr(config)) if config else None,
            "record_id_sha256s": sorted(sha256_text(r["id"]) for r in records),
        },
        payload={
            "records": len(records),
            "entries": sum(len(r["entries"]) for r in records),
            "output_sha256": sha256_text(canonical_json(records)),
        },
    )
    return records


def audited_extract_multi(
    trail: AuditTrail, note: str, gazetteer: list[str], **kwargs
) -> "extract.MultiExtractResult":
    """`extract.extract_records_multi` + one trail event (quarantine counted by
    NEUTRAL reason token). Results pass through untouched."""
    result = extract.extract_records_multi(note, gazetteer, **kwargs)
    config = kwargs.get("config")
    quarantined = dict(sorted(Counter(q.reason for q in result.quarantined).items()))
    output = {
        "records": result.records,
        "quarantined": [[q.index, q.reason, q.char_offset] for q in result.quarantined],
    }
    trail.append(
        "extract_multi",
        agent=f"extract {extract.VERSION}",
        entity={
            "input_sha256": sha256_text(note),
            "gazetteer_sha256": sha256_text(canonical_json(gazetteer)),
            "config_repr_sha256": sha256_text(repr(config)) if config else None,
            "record_id_sha256s": sorted(sha256_text(r["id"]) for r in result.records),
        },
        payload={
            "records": len(result.records),
            "entries": sum(len(r["entries"]) for r in result.records),
            "quarantined": quarantined,
            "output_sha256": sha256_text(canonical_json(output)),
        },
    )
    return result


def audited_report(
    trail: AuditTrail,
    records: list,
    *,
    field: str = "item",
    normalize: bool = False,
    synonyms: dict | None = None,
    fuzzy_cutoff: float | None = None,
) -> list:
    """`recurrence.run_report` + one trail event. Reports pass through untouched.

    The matching knobs are logged as provenance (HOW the run matched);
    ``fuzzy_cutoff`` is carried as a string per the no-float rule.
    """
    reports = recurrence.run_report(
        records,
        field=field,
        normalize=normalize,
        synonyms=synonyms,
        fuzzy_cutoff=fuzzy_cutoff,
    )
    findings = dict(
        sorted(Counter(f.expert for r in reports for f in r.findings).items())
    )
    trail.append(
        "report",
        agent=f"recurrence {recurrence.VERSION}",
        entity={
            "input_sha256": sha256_text(canonical_json(records)),
            "record_id_sha256s": [sha256_text(r.record_id) for r in reports],
            "matching": {
                "field": field,
                "normalize": normalize,
                "synonyms_sha256": sha256_text(canonical_json(synonyms)) if synonyms else None,
                "fuzzy_cutoff": str(fuzzy_cutoff) if fuzzy_cutoff is not None else None,
            },
        },
        payload={
            "records": len(reports),
            "findings": findings,
            "report_sha256": sha256_text(recurrence.format_report(reports)),
        },
    )
    return reports


# ---------------------------------------------------------------------------
# Monitor — counts over the trail, surfaced as data; never a judgment
# ---------------------------------------------------------------------------


def summarize(trail: AuditTrail) -> dict:
    """Counts across the whole trail: events by type, findings by lens,
    quarantined segments by reason. Numbers only — no thresholds, no labels."""
    by_type = dict(sorted(Counter(e.type for e in trail.entries).items()))
    findings: Counter = Counter()
    quarantined: Counter = Counter()
    for e in trail.entries:
        if e.type == "report":
            findings.update(e.payload.get("findings", {}))
        else:
            quarantined.update(e.payload.get("quarantined", {}))
    return {
        "events": len(trail.entries),
        "by_type": by_type,
        "findings_by_lens": dict(sorted(findings.items())),
        "quarantined_by_reason": dict(sorted(quarantined.items())),
    }


def compare(trail: AuditTrail, boundary_seq: int) -> dict:
    """Per-lens finding counts before vs after ``boundary_seq`` (inclusive left),
    plus the signed difference — surfaced as numbers for a HUMAN to read. The
    monitor never says what a difference means.
    """
    if not isinstance(boundary_seq, int) or isinstance(boundary_seq, bool):
        raise ValueError(f"boundary_seq must be an int, got {boundary_seq!r}")
    if not 1 <= boundary_seq < len(trail.entries):
        raise ValueError(
            f"boundary_seq must split the trail (1 <= b < {len(trail.entries)}), got {boundary_seq}"
        )

    def lens_counts(entries: list[AuditEntry]) -> Counter:
        c: Counter = Counter()
        for e in entries:
            if e.type == "report":
                c.update(e.payload.get("findings", {}))
        return c

    side_a = lens_counts(trail.entries[:boundary_seq])
    side_b = lens_counts(trail.entries[boundary_seq:])
    lenses = sorted(set(side_a) | set(side_b))
    return {
        "boundary_seq": boundary_seq,
        "window_a": {"events": boundary_seq, "findings_by_lens": dict(sorted(side_a.items()))},
        "window_b": {
            "events": len(trail.entries) - boundary_seq,
            "findings_by_lens": dict(sorted(side_b.items())),
        },
        "difference_by_lens": {k: side_b[k] - side_a[k] for k in lenses},
    }


def format_summary(summary: dict) -> str:
    """Render `summarize` output as neutral text (counts, cited; nothing judged)."""

    def counts(d: dict) -> str:
        return ", ".join(f"{k} {v}" for k, v in d.items()) if d else "none"

    return "\n".join(
        [
            "audit summary",
            f"  events: {summary['events']} ({counts(summary['by_type'])})",
            f"  findings by lens: {counts(summary['findings_by_lens'])}",
            f"  quarantined by reason: {counts(summary['quarantined_by_reason'])}",
        ]
    )


def format_compare(comparison: dict) -> str:
    """Render `compare` output as neutral text: A, B, and the signed difference."""
    a, b = comparison["window_a"], comparison["window_b"]
    lines = [
        f"audit compare at seq {comparison['boundary_seq']} "
        f"(window A: {a['events']} events, window B: {b['events']} events)"
    ]
    for lens, diff in comparison["difference_by_lens"].items():
        lines.append(
            f"  {lens}: {a['findings_by_lens'].get(lens, 0)} -> "
            f"{b['findings_by_lens'].get(lens, 0)} (difference {diff:+d})"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Demo + self-test
# ---------------------------------------------------------------------------


def _demo_clock() -> Callable[[], str]:
    """A fixed, stepping clock so the demo (and its hashes) are deterministic."""
    base = datetime.datetime(2026, 6, 11, tzinfo=datetime.timezone.utc)
    tick = -1

    def now() -> str:
        nonlocal tick
        tick += 1
        return (base + datetime.timedelta(seconds=tick)).strftime("%Y-%m-%dT%H:%M:%SZ")

    return now


def _build_demo_trail(path: str | None = None) -> AuditTrail:
    """The canonical two-event demo trail the oracle pins: one audited
    multi-patient extraction, then one audited report over SAMPLE_RECORDS."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from data.sample_records import (
        FREETEXT_GAZETTEER,
        FREETEXT_MULTI_DELIMITER,
        FREETEXT_MULTI_NOTE,
        FREETEXT_MULTI_SHIFTS,
        SAMPLE_RECORDS,
    )

    trail = AuditTrail(path, now=_demo_clock())
    audited_extract_multi(
        trail,
        FREETEXT_MULTI_NOTE,
        FREETEXT_GAZETTEER,
        delimiter=FREETEXT_MULTI_DELIMITER,
        shift_by_id=FREETEXT_MULTI_SHIFTS,
    )
    audited_report(trail, SAMPLE_RECORDS)
    return trail


def _run_demo() -> int:
    trail = _build_demo_trail()
    print("audit trail demo (synthetic records; digests and counts only)")
    for e in trail.entries:
        detail = ", ".join(
            f"{k} {v}" for k, v in e.payload.items() if isinstance(v, int)
        )
        print(f"  seq {e.seq}  {e.recorded}  {e.type}  {detail}")
    ok, _ = trail.verify()
    print(f"chain: {'intact' if ok else 'BROKEN'} ({len(trail.entries)} entries)")
    print(f"head: {trail.head()}")
    print()
    print(format_summary(summarize(trail)))
    return 0


def _run_self_test() -> int:
    """Hand-checkable spec cases, asserted toward the hand-written oracle."""
    from data.sample_records import AUDIT_ANSWER_KEY

    failures: list[str] = []

    def check(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            failures.append(name)

    trail = _build_demo_trail()
    extract_event, report_event = trail.entries

    check(
        "extract_multi counts match the hand oracle",
        extract_event.payload["records"] == AUDIT_ANSWER_KEY["extract_multi"]["records"]
        and extract_event.payload["entries"] == AUDIT_ANSWER_KEY["extract_multi"]["entries"]
        and extract_event.payload["quarantined"]
        == AUDIT_ANSWER_KEY["extract_multi"]["quarantined"],
    )
    check(
        "report counts match the hand oracle",
        report_event.payload["records"] == AUDIT_ANSWER_KEY["report"]["records"]
        and report_event.payload["findings"] == AUDIT_ANSWER_KEY["report"]["findings"],
    )
    check("fresh chain verifies", trail.verify() == (True, None))

    tampered = _build_demo_trail()
    tampered.entries[0].payload["records"] = 99
    check("tampered payload fails at seq 1", tampered.verify() == (False, 1))

    check(
        "fixed clock makes the head reproducible",
        trail.head() == _build_demo_trail().head(),
    )
    check("head anchor matches itself", trail.verify_head(trail.head()))
    check("head anchor catches a different chain", not trail.verify_head(GENESIS_HASH))

    try:
        AuditTrail(now=_demo_clock()).append(
            "report", agent="x", entity={}, payload={"cutoff": 0.85}
        )
        check("float payload is refused", False)
    except ValueError:
        check("float payload is refused", True)

    print(f"self-test: {8 - len(failures)}/8 passed")
    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Governance audit trail — append-only, hash-chained record of "
        "what the engine surfaced (digests + counts only). Records and cites; "
        "never interprets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--version",
        action="store_true",
        help="Print the module name and version, then exit",
    )
    p.add_argument(
        "--self-test", action="store_true", help="Run the built-in spec cases"
    )
    p.add_argument(
        "--demo",
        action="store_true",
        help="Audited demo run (multi-extract + report over the sample data)",
    )
    p.add_argument(
        "--verify",
        metavar="FILE",
        help="Verify a JSONL trail file's hash chain; exit 1 if broken",
    )
    p.add_argument(
        "--head",
        metavar="FILE",
        help="Print a trail file's chain head (record it OUTSIDE the file)",
    )
    p.add_argument(
        "--summary",
        metavar="FILE",
        help="Print event/finding/quarantine counts for a trail file",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(f"Health-Prototype audit trail {VERSION}")
        return 0
    if args.self_test:
        return _run_self_test()
    if args.demo:
        return _run_demo()
    if args.verify:
        entries = read_entries(args.verify)
        ok, bad_seq = verify_entries(entries)
        if ok:
            print(f"chain: intact ({len(entries)} entries)")
            return 0
        print(f"chain: BROKEN at seq {bad_seq}")
        return 1
    if args.head:
        entries = read_entries(args.head)
        print(entries[-1].entry_hash if entries else GENESIS_HASH)
        return 0
    if args.summary:
        trail = AuditTrail(args.summary)
        print(format_summary(summarize(trail)))
        return 0
    build_parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
