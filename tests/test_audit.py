"""test_audit.py — behavior contract for the governance audit trail (ADR 0030).

What is enforced, grouped the way the module is built:

  Canonical form    — key-order invariance, ASCII stability, the no-float rule
                      (floats are THE canonicalization hazard; rejected loudly).
  Chain integrity   — a fresh chain verifies; every tamper class is caught at
                      the right seq (payload edit, hash edit, prev_hash edit,
                      middle deletion, reordering, insertion); the HONEST LIMIT
                      is pinned as a test: tail truncation passes `verify` and
                      is caught ONLY by the external head anchor.
  Oracle agreement  — the audited demo events reproduce AUDIT_ANSWER_KEY
                      (hand-written first, in its own prior commit).
  Pass-through      — audited_* return EXACTLY what the un-audited calls
                      return; auditing must never change engine behavior.
  Persistence       — JSONL round-trip, resume-and-continue, malformed lines
                      and a tampered file fail loudly / are reported.
  Monitor           — summarize/compare counts match hand arithmetic; output
                      is banned-words-clean (the librarian rule holds in the
                      trail exactly as it does in the views).
  CLI               — in-process exit codes for --version/--verify/--head/
                      --summary on intact and tampered files.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import audit  # noqa: E402
import extract  # noqa: E402
import recurrence  # noqa: E402
from data.sample_records import (  # noqa: E402
    AUDIT_ANSWER_KEY,
    FREETEXT_GAZETTEER,
    FREETEXT_MULTI_DELIMITER,
    FREETEXT_MULTI_NOTE,
    FREETEXT_MULTI_SHIFTS,
    FREETEXT_SAMPLE_NOTE,
    SAMPLE_RECORDS,
)
from tests.banned_words import BANNED  # noqa: E402


def read_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def fixed_clock(start: int = 0):
    """A deterministic stepping clock: 2026-06-11T00:00:00Z + n seconds."""
    tick = start - 1

    def now() -> str:
        nonlocal tick
        tick += 1
        return f"2026-06-11T00:00:{tick:02d}Z"

    return now


def small_trail(path: str | None = None) -> audit.AuditTrail:
    """Three minimal hand-built events on a fixed clock."""
    trail = audit.AuditTrail(path, now=fixed_clock())
    for n in (1, 2, 3):
        trail.append(
            "report",
            agent="recurrence test",
            entity={"input_sha256": "x" * 64, "record_ids": [f"R{n}"]},
            payload={"records": n, "findings": {"recurrence": n}},
        )
    return trail


class TestCanonicalJson(unittest.TestCase):
    def test_key_order_is_irrelevant(self):
        a = audit.canonical_json({"b": 1, "a": [1, 2]})
        b = audit.canonical_json({"a": [1, 2], "b": 1})
        self.assertEqual(a, b)

    def test_non_ascii_is_escaped_stably(self):
        self.assertEqual(audit.canonical_json({"k": "é"}), '{"k":"\\u00e9"}')

    def test_unserializable_raises_value_error(self):
        with self.assertRaises(ValueError):
            audit.canonical_json({"k": {1, 2}})

    def test_float_anywhere_is_rejected(self):
        for bad in (
            {"x": 0.85},
            {"x": [1, 2.0]},
            {"x": {"y": [{"z": 3.14}]}},
        ):
            with self.assertRaises(ValueError):
                audit._check_no_floats(bad)

    def test_bool_int_str_none_pass(self):
        audit._check_no_floats({"a": True, "b": 0, "c": "s", "d": None, "e": [1, "x"]})

    def test_non_string_key_is_rejected(self):
        with self.assertRaises(ValueError):
            audit._check_no_floats({1: "x"})


class TestChainIntegrity(unittest.TestCase):
    def test_empty_trail_verifies_with_genesis_head(self):
        trail = audit.AuditTrail(now=fixed_clock())
        self.assertEqual(trail.verify(), (True, None))
        self.assertEqual(trail.head(), audit.GENESIS_HASH)

    def test_fresh_chain_verifies(self):
        self.assertEqual(small_trail().verify(), (True, None))

    def test_payload_tamper_caught_at_its_seq(self):
        trail = small_trail()
        trail.entries[1].payload["records"] = 99
        self.assertEqual(trail.verify(), (False, 2))

    def test_entry_hash_tamper_caught(self):
        trail = small_trail()
        trail.entries[2].entry_hash = "f" * 64
        self.assertEqual(trail.verify(), (False, 3))

    def test_prev_hash_tamper_caught(self):
        trail = small_trail()
        trail.entries[1].prev_hash = "f" * 64
        self.assertEqual(trail.verify(), (False, 2))

    def test_middle_deletion_caught(self):
        trail = small_trail()
        del trail.entries[1]
        ok, bad_seq = trail.verify()
        self.assertFalse(ok)
        self.assertEqual(bad_seq, 2)

    def test_reordering_caught(self):
        trail = small_trail()
        trail.entries[0], trail.entries[1] = trail.entries[1], trail.entries[0]
        self.assertEqual(trail.verify(), (False, 1))

    def test_insertion_caught(self):
        trail = small_trail()
        trail.entries.insert(1, trail.entries[0])
        self.assertEqual(trail.verify(), (False, 2))

    def test_tail_truncation_passes_verify_but_fails_head_anchor(self):
        # THE documented honest limit: a truncated chain is internally
        # consistent; only the externally recorded head catches it.
        trail = small_trail()
        anchored_head = trail.head()
        del trail.entries[-1]
        self.assertEqual(trail.verify(), (True, None))
        self.assertFalse(trail.verify_head(anchored_head))

    def test_head_anchor_matches_intact_chain(self):
        trail = small_trail()
        self.assertTrue(trail.verify_head(trail.head()))

    def test_fixed_clock_chain_is_reproducible(self):
        self.assertEqual(small_trail().head(), small_trail().head())

    def test_recorded_timestamp_is_part_of_the_hash(self):
        a = audit.AuditTrail(now=fixed_clock(0))
        b = audit.AuditTrail(now=fixed_clock(30))
        for t in (a, b):
            t.append("report", agent="x", entity={}, payload={})
        self.assertNotEqual(a.head(), b.head())


class TestAppendValidation(unittest.TestCase):
    def setUp(self):
        self.trail = audit.AuditTrail(now=fixed_clock())

    def test_unknown_event_type_raises(self):
        with self.assertRaises(ValueError):
            self.trail.append("judge", agent="x", entity={}, payload={})

    def test_empty_agent_raises(self):
        with self.assertRaises(ValueError):
            self.trail.append("report", agent="  ", entity={}, payload={})

    def test_non_dict_entity_raises(self):
        with self.assertRaises(ValueError):
            self.trail.append("report", agent="x", entity=[], payload={})

    def test_non_dict_payload_raises(self):
        with self.assertRaises(ValueError):
            self.trail.append("report", agent="x", entity={}, payload=[])

    def test_float_in_payload_raises_and_appends_nothing(self):
        with self.assertRaises(ValueError):
            self.trail.append("report", agent="x", entity={}, payload={"f": 0.5})
        self.assertEqual(self.trail.entries, [])

    def test_bad_constructor_args_raise(self):
        with self.assertRaises(ValueError):
            audit.AuditTrail(123)
        with self.assertRaises(ValueError):
            audit.AuditTrail(now="not callable")


class TestOracleAgreement(unittest.TestCase):
    """The audited demo must reproduce the hand-written, pre-committed key."""

    @classmethod
    def setUpClass(cls):
        cls.trail = audit._build_demo_trail()
        cls.extract_event, cls.report_event = cls.trail.entries

    def test_extract_multi_counts_match_key(self):
        key = AUDIT_ANSWER_KEY["extract_multi"]
        self.assertEqual(self.extract_event.payload["records"], key["records"])
        self.assertEqual(self.extract_event.payload["entries"], key["entries"])
        self.assertEqual(self.extract_event.payload["quarantined"], key["quarantined"])

    def test_report_counts_match_key(self):
        key = AUDIT_ANSWER_KEY["report"]
        self.assertEqual(self.report_event.payload["records"], key["records"])
        self.assertEqual(self.report_event.payload["findings"], key["findings"])

    def test_report_sha256_re_derives_from_the_actual_report(self):
        # Provenance is PROVABLE: re-render the report, re-hash, match the trail.
        reports = recurrence.run_report(SAMPLE_RECORDS)
        self.assertEqual(
            self.report_event.payload["report_sha256"],
            audit.sha256_text(recurrence.format_report(reports)),
        )

    def test_event_types_and_agents_cite_their_module(self):
        self.assertEqual(self.extract_event.type, "extract_multi")
        self.assertEqual(self.extract_event.agent, f"extract {extract.VERSION}")
        self.assertEqual(self.report_event.type, "report")
        self.assertEqual(self.report_event.agent, f"recurrence {recurrence.VERSION}")

    def test_no_clinical_text_or_identifier_in_any_event(self):
        # OWASP rule made checkable: no note text, no item value, no patient
        # key, and no raw record id appears anywhere in the serialized events —
        # digests and counts only (an extracted record's id IS the patient key).
        serialized = audit.canonical_json(
            [e.core() for e in self.trail.entries]
        ).lower()
        for fragment in ("poor sleep", "headache", "example-001", "patient:", "r001"):
            self.assertNotIn(fragment, serialized)
        # Coverage stays PROVABLE without the value: hash the id you hold,
        # match it against the event.
        self.assertIn(
            audit.sha256_text("R001"),
            self.report_event.entity["record_id_sha256s"],
        )
        self.assertIn(
            audit.sha256_text("EXAMPLE-001"),
            self.extract_event.entity["record_id_sha256s"],
        )


class TestPassThrough(unittest.TestCase):
    """Auditing must never change what the engine returns."""

    def test_audited_report_equals_plain_run_report(self):
        trail = audit.AuditTrail(now=fixed_clock())
        audited = audit.audited_report(trail, SAMPLE_RECORDS)
        plain = recurrence.run_report(SAMPLE_RECORDS)
        self.assertEqual(
            [(r.record_id, [(f.expert, f.line) for f in r.findings]) for r in audited],
            [(r.record_id, [(f.expert, f.line) for f in r.findings]) for r in plain],
        )
        self.assertEqual(len(trail.entries), 1)

    def test_audited_extract_equals_plain_extract(self):
        trail = audit.AuditTrail(now=fixed_clock())
        audited = audit.audited_extract(trail, FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
        plain = extract.extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
        self.assertEqual(audited, plain)
        self.assertEqual(trail.entries[0].type, "extract")
        self.assertEqual(trail.entries[0].payload["records"], len(plain))

    def test_audited_extract_multi_equals_plain(self):
        trail = audit.AuditTrail(now=fixed_clock())
        kwargs = dict(
            delimiter=FREETEXT_MULTI_DELIMITER, shift_by_id=FREETEXT_MULTI_SHIFTS
        )
        audited = audit.audited_extract_multi(
            trail, FREETEXT_MULTI_NOTE, FREETEXT_GAZETTEER, **kwargs
        )
        plain = extract.extract_records_multi(
            FREETEXT_MULTI_NOTE, FREETEXT_GAZETTEER, **kwargs
        )
        self.assertEqual(audited.records, plain.records)
        self.assertEqual(audited.quarantined, plain.quarantined)

    def test_matching_knobs_are_cited_with_fuzzy_as_string(self):
        trail = audit.AuditTrail(now=fixed_clock())
        audit.audited_report(
            trail, SAMPLE_RECORDS, normalize=True, fuzzy_cutoff=0.85
        )
        matching = trail.entries[0].entity["matching"]
        self.assertEqual(matching["normalize"], True)
        self.assertEqual(matching["fuzzy_cutoff"], "0.85")  # no-float rule


class TestPersistence(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "trail.jsonl")

    def test_round_trip_verifies_and_matches(self):
        written = small_trail(self.path)
        loaded = audit.AuditTrail(self.path)
        self.assertEqual(loaded.verify(), (True, None))
        self.assertEqual(loaded.head(), written.head())
        self.assertEqual(
            [e.core() for e in loaded.entries], [e.core() for e in written.entries]
        )

    def test_reopen_continues_the_chain(self):
        small_trail(self.path)
        resumed = audit.AuditTrail(self.path, now=fixed_clock(10))
        resumed.append("report", agent="x", entity={}, payload={"records": 4})
        self.assertEqual(resumed.entries[-1].seq, 4)
        self.assertEqual(audit.AuditTrail(self.path).verify(), (True, None))

    def test_tampered_file_refuses_to_open_as_trail(self):
        small_trail(self.path)
        lines = read_text(self.path).splitlines()
        obj = json.loads(lines[1])
        obj["event"]["payload"]["records"] = 99
        lines[1] = json.dumps(obj, sort_keys=True, separators=(",", ":"))
        write_text(self.path, "\n".join(lines) + "\n")
        with self.assertRaises(ValueError):
            audit.AuditTrail(self.path)
        # ...but the reporting path still reads it and locates the break.
        self.assertEqual(
            audit.verify_entries(audit.read_entries(self.path)), (False, 2)
        )

    def test_malformed_line_raises_with_line_number(self):
        small_trail(self.path)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write("not json\n")
        with self.assertRaises(ValueError) as ctx:
            audit.read_entries(self.path)
        self.assertIn("line 4", str(ctx.exception))

    def test_file_lines_are_canonical_json(self):
        small_trail(self.path)
        for line in read_text(self.path).splitlines():
            self.assertEqual(line, audit.canonical_json(json.loads(line)))


class TestMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trail = audit._build_demo_trail()

    def test_summary_counts_match_hand_arithmetic(self):
        summary = audit.summarize(self.trail)
        self.assertEqual(summary["events"], 2)
        self.assertEqual(summary["by_type"], {"extract_multi": 1, "report": 1})
        self.assertEqual(
            summary["findings_by_lens"], AUDIT_ANSWER_KEY["report"]["findings"]
        )
        self.assertEqual(
            summary["quarantined_by_reason"],
            AUDIT_ANSWER_KEY["extract_multi"]["quarantined"],
        )

    def test_compare_splits_and_differences_by_hand(self):
        trail = small_trail()  # findings: 1, then 2, then 3
        comparison = audit.compare(trail, 1)
        self.assertEqual(comparison["window_a"]["findings_by_lens"], {"recurrence": 1})
        self.assertEqual(comparison["window_b"]["findings_by_lens"], {"recurrence": 5})
        self.assertEqual(comparison["difference_by_lens"], {"recurrence": 4})

    def test_compare_bad_boundary_raises(self):
        trail = small_trail()
        for bad in (0, 3, -1, "1", True):
            with self.assertRaises(ValueError):
                audit.compare(trail, bad)

    def test_rendered_output_is_banned_words_clean(self):
        # The librarian rule holds in the trail exactly as in the views.
        texts = [
            audit.format_summary(audit.summarize(self.trail)),
            audit.format_compare(audit.compare(small_trail(), 1)),
        ]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            audit._run_demo()
            audit._run_self_test()
        texts.append(buf.getvalue())
        for text in texts:
            low = text.lower()
            for word in BANNED:
                self.assertNotIn(word, low, f"banned word {word!r} in output")

    def test_demo_output_is_deterministic(self):
        outputs = []
        for _ in range(2):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                audit._run_demo()
            outputs.append(buf.getvalue())
        self.assertEqual(outputs[0], outputs[1])


class TestCli(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "trail.jsonl")
        small_trail(self.path)

    def run_cli(self, *argv: str) -> tuple[int, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = audit.main(list(argv))
        return rc, buf.getvalue()

    def test_version(self):
        rc, out = self.run_cli("--version")
        self.assertEqual(rc, 0)
        self.assertIn(audit.VERSION, out)

    def test_self_test_passes(self):
        rc, _ = self.run_cli("--self-test")
        self.assertEqual(rc, 0)

    def test_verify_intact_file(self):
        rc, out = self.run_cli("--verify", self.path)
        self.assertEqual(rc, 0)
        self.assertIn("intact", out)

    def test_verify_tampered_file_exits_1_and_cites_seq(self):
        lines = read_text(self.path).splitlines()
        obj = json.loads(lines[0])
        obj["event"]["payload"]["records"] = 99
        lines[0] = json.dumps(obj, sort_keys=True, separators=(",", ":"))
        write_text(self.path, "\n".join(lines) + "\n")
        rc, out = self.run_cli("--verify", self.path)
        self.assertEqual(rc, 1)
        self.assertIn("seq 1", out)

    def test_head_prints_the_chain_head(self):
        rc, out = self.run_cli("--head", self.path)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), audit.AuditTrail(self.path).head())

    def test_summary_prints_counts(self):
        rc, out = self.run_cli("--summary", self.path)
        self.assertEqual(rc, 0)
        self.assertIn("events: 3", out)
        self.assertIn("recurrence 6", out)


if __name__ == "__main__":
    unittest.main()
