"""
test_recurrence.py — the six required spec cases for detect_recurrence.

Run from the repo root:
    python -m unittest discover -s tests -t .

Each test asserts toward an externally-known answer, never toward whatever the
code happens to produce.
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recurrence import RecurrenceHit, detect_recurrence, format_hit  # noqa: E402


class TestDetectRecurrence(unittest.TestCase):
    # 1. Item recurs 3 times in one record -> caught, count == 3, all 3 dates.
    def test_recurs_three_times(self):
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
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].record_id, "R001")
        self.assertEqual(hits[0].item, "poor sleep")
        self.assertEqual(hits[0].count, 3)
        self.assertEqual(
            hits[0].dates, ["2026-01-10", "2026-02-02", "2026-03-15"]
        )

    # 2. Item appears exactly once -> NOT flagged (below min_count).
    def test_single_occurrence_not_flagged(self):
        hits = detect_recurrence(
            [{"id": "R002", "entries": [{"date": "2026-01-10", "item": "headache"}]}]
        )
        self.assertEqual(hits, [])

    # 3. Record with nothing recurring -> clean empty result, zero false positives.
    def test_nothing_recurring_is_empty(self):
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
        self.assertEqual(hits, [])

    # 4. Two different items each recur in one record -> both caught independently.
    def test_two_items_each_recur(self):
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
        self.assertEqual(len(hits), 2)
        self.assertIn("poor sleep", by_item)
        self.assertIn("appetite change", by_item)
        self.assertEqual(by_item["poor sleep"].count, 2)
        self.assertEqual(by_item["appetite change"].count, 2)
        self.assertEqual(
            by_item["appetite change"].dates, ["2026-02-20", "2026-03-01"]
        )

    # 5. Empty record / missing field -> handled gracefully, no crash, no false hit.
    def test_malformed_handled_gracefully(self):
        hits = detect_recurrence(
            [
                {"id": "R005", "entries": []},          # empty entries
                {"id": "R006"},                          # missing entries
                {"id": "R007", "entries": [              # missing item / None item
                    {"date": "2026-01-10"},
                    {"item": None, "date": "2026-02-02"},
                ]},
                {},                                      # empty record
                "not-a-record",                          # wrong type entirely
            ]
        )
        self.assertEqual(hits, [])

    # 6. min_count respected (set to 3 -> a 2x item does NOT flag).
    def test_min_count_respected(self):
        records = [
            {
                "id": "R008",
                "entries": [
                    {"date": "2026-01-10", "item": "poor sleep"},
                    {"date": "2026-02-02", "item": "poor sleep"},
                ],
            }
        ]
        self.assertEqual(detect_recurrence(records, min_count=3), [])
        # sanity: the same 2x item DOES flag at the default min_count of 2.
        self.assertEqual(len(detect_recurrence(records)), 1)


class TestSurfacingFirewall(unittest.TestCase):
    """Output cites provenance and carries no interpretation."""

    def test_format_hit_cites_provenance_only(self):
        line = format_hit(
            RecurrenceHit(
                record_id="R001",
                item="poor sleep",
                count=2,
                dates=["2026-01-10", "2026-02-02"],
            )
        )
        # provenance present: record id, item, count, every date
        self.assertIn("R001", line)
        self.assertIn("poor sleep", line)
        self.assertIn("2", line)
        self.assertIn("2026-01-10", line)
        self.assertIn("2026-02-02", line)
        # no interpretation present
        lowered = line.lower()
        for banned in ("worsening", "severe", "severity", "suggests", "diagnos",
                       "risk", "concern", "abnormal", "score"):
            self.assertNotIn(banned, lowered)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# Additional edge-case and structural tests
# ---------------------------------------------------------------------------


class TestDetectRecurrenceEdgeCases(unittest.TestCase):
    """Boundary and negative cases not covered by the six required spec cases."""

    def test_empty_list_returns_empty(self):
        self.assertEqual(detect_recurrence([]), [])

    def test_none_is_not_a_valid_call_but_empty_string_item_is_skipped(self):
        # An item value of "" must be skipped (code: `if item is None or item == ""`).
        hits = detect_recurrence(
            [
                {
                    "id": "R001",
                    "entries": [
                        {"date": "2026-01-01", "item": ""},
                        {"date": "2026-02-01", "item": ""},
                    ],
                }
            ]
        )
        self.assertEqual(hits, [])

    def test_whitespace_item_is_not_skipped(self):
        # " " is non-empty and not None — the engine must NOT silently drop it.
        hits = detect_recurrence(
            [
                {
                    "id": "R001",
                    "entries": [
                        {"date": "2026-01-01", "item": " "},
                        {"date": "2026-02-01", "item": " "},
                    ],
                }
            ]
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].item, " ")
        self.assertEqual(hits[0].count, 2)

    def test_custom_field_parameter(self):
        # The engine is domain-agnostic: any field key should work.
        hits = detect_recurrence(
            [
                {
                    "id": "RX01",
                    "entries": [
                        {"date": "2026-01-10", "symptom": "nausea"},
                        {"date": "2026-02-10", "symptom": "nausea"},
                        {"date": "2026-03-10", "symptom": "fever"},
                    ],
                }
            ],
            field="symptom",
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].item, "nausea")
        self.assertEqual(hits[0].count, 2)
        self.assertEqual(hits[0].record_id, "RX01")

    def test_custom_field_no_false_hit_on_default_field(self):
        # When field="symptom", the "item" key in entries must NOT trigger a hit.
        hits = detect_recurrence(
            [
                {
                    "id": "RX02",
                    "entries": [
                        {"date": "2026-01-10", "item": "fatigue"},
                        {"date": "2026-02-10", "item": "fatigue"},
                    ],
                }
            ],
            field="symptom",
        )
        self.assertEqual(hits, [])

    def test_multiple_records_hits_from_each(self):
        # Two records both have a recurrence; both should appear in the output.
        records = [
            {
                "id": "RA",
                "entries": [
                    {"date": "2026-01-01", "item": "cough"},
                    {"date": "2026-02-01", "item": "cough"},
                ],
            },
            {
                "id": "RB",
                "entries": [
                    {"date": "2026-01-05", "item": "fever"},
                    {"date": "2026-02-05", "item": "fever"},
                ],
            },
        ]
        hits = detect_recurrence(records)
        record_ids = [h.record_id for h in hits]
        self.assertIn("RA", record_ids)
        self.assertIn("RB", record_ids)
        self.assertEqual(len(hits), 2)

    def test_multiple_records_only_hitting_record_appears(self):
        # Only the record with a recurrence should contribute a hit.
        records = [
            {
                "id": "RC",
                "entries": [
                    {"date": "2026-01-01", "item": "rash"},
                    {"date": "2026-02-01", "item": "rash"},
                ],
            },
            {
                "id": "RD",
                "entries": [
                    {"date": "2026-01-10", "item": "nausea"},
                ],
            },
        ]
        hits = detect_recurrence(records)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].record_id, "RC")

    def test_min_count_one_flags_every_occurrence(self):
        # min_count=1 means even single-occurrence items are surfaced.
        hits = detect_recurrence(
            [
                {
                    "id": "RE",
                    "entries": [
                        {"date": "2026-01-01", "item": "headache"},
                        {"date": "2026-02-01", "item": "fatigue"},
                    ],
                }
            ],
            min_count=1,
        )
        items = {h.item for h in hits}
        self.assertIn("headache", items)
        self.assertIn("fatigue", items)
        self.assertEqual(len(hits), 2)

    def test_non_string_item_values_coerced_to_str(self):
        # Integer item values should be coerced to string and tracked.
        hits = detect_recurrence(
            [
                {
                    "id": "RF",
                    "entries": [
                        {"date": "2026-01-01", "item": 42},
                        {"date": "2026-02-01", "item": 42},
                    ],
                }
            ]
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].item, "42")
        self.assertEqual(hits[0].count, 2)

    def test_dates_sorted_chronologically_in_hit(self):
        # Entries added out of order — dates in the hit must still be sorted.
        hits = detect_recurrence(
            [
                {
                    "id": "RG",
                    "entries": [
                        {"date": "2026-03-01", "item": "dizziness"},
                        {"date": "2026-01-01", "item": "dizziness"},
                        {"date": "2026-02-01", "item": "dizziness"},
                    ],
                }
            ]
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(
            hits[0].dates, ["2026-01-01", "2026-02-01", "2026-03-01"]
        )

    def test_items_ordered_alphabetically_within_record(self):
        # Multiple recurring items in one record must come out sorted by name.
        hits = detect_recurrence(
            [
                {
                    "id": "RH",
                    "entries": [
                        {"date": "2026-01-01", "item": "zzz-item"},
                        {"date": "2026-02-01", "item": "zzz-item"},
                        {"date": "2026-01-05", "item": "aaa-item"},
                        {"date": "2026-02-05", "item": "aaa-item"},
                    ],
                }
            ]
        )
        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0].item, "aaa-item")
        self.assertEqual(hits[1].item, "zzz-item")

    def test_record_missing_id_key_uses_empty_string(self):
        # A record without an "id" key must not raise; record_id becomes "".
        hits = detect_recurrence(
            [
                {
                    "entries": [
                        {"date": "2026-01-01", "item": "pain"},
                        {"date": "2026-02-01", "item": "pain"},
                    ]
                }
            ]
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].record_id, "")

    def test_none_date_in_entry_stored_as_empty_string(self):
        # A None date must not crash and must appear in dates as "".
        hits = detect_recurrence(
            [
                {
                    "id": "RI",
                    "entries": [
                        {"date": None, "item": "fatigue"},
                        {"date": None, "item": "fatigue"},
                    ],
                }
            ]
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].dates, ["", ""])

    def test_non_dict_entry_in_list_is_skipped(self):
        # Non-dict entries in the entries list must not raise.
        hits = detect_recurrence(
            [
                {
                    "id": "RJ",
                    "entries": [
                        "string-entry",
                        42,
                        None,
                        {"date": "2026-01-01", "item": "valid"},
                        {"date": "2026-02-01", "item": "valid"},
                    ],
                }
            ]
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].item, "valid")

    def test_entries_is_dict_not_list_is_skipped(self):
        # A record where "entries" is a dict (not a list) must be skipped.
        hits = detect_recurrence(
            [{"id": "RK", "entries": {"date": "2026-01-01", "item": "pain"}}]
        )
        self.assertEqual(hits, [])

    def test_entries_is_string_not_list_is_skipped(self):
        hits = detect_recurrence([{"id": "RL", "entries": "2026-01-01"}])
        self.assertEqual(hits, [])

    def test_exact_min_count_boundary_is_inclusive(self):
        # An item appearing exactly min_count times must flag (>= not >).
        hits = detect_recurrence(
            [
                {
                    "id": "RM",
                    "entries": [
                        {"date": "2026-01-01", "item": "pain"},
                        {"date": "2026-02-01", "item": "pain"},
                        {"date": "2026-03-01", "item": "pain"},
                    ],
                }
            ],
            min_count=3,
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].count, 3)

    def test_one_below_min_count_does_not_flag(self):
        # One occurrence fewer than min_count must NOT flag.
        hits = detect_recurrence(
            [
                {
                    "id": "RN",
                    "entries": [
                        {"date": "2026-01-01", "item": "pain"},
                        {"date": "2026-02-01", "item": "pain"},
                    ],
                }
            ],
            min_count=3,
        )
        self.assertEqual(hits, [])

    def test_hit_count_matches_len_of_dates(self):
        # The count field on a hit must equal the number of dates.
        hits = detect_recurrence(
            [
                {
                    "id": "RO",
                    "entries": [
                        {"date": "2026-01-01", "item": "migraine"},
                        {"date": "2026-02-01", "item": "migraine"},
                        {"date": "2026-03-01", "item": "migraine"},
                        {"date": "2026-04-01", "item": "migraine"},
                    ],
                }
            ]
        )
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].count, len(hits[0].dates))
        self.assertEqual(hits[0].count, 4)


class TestRecurrenceHitDataclass(unittest.TestCase):
    """RecurrenceHit dataclass construction and equality."""

    def test_basic_construction(self):
        h = RecurrenceHit(record_id="R001", item="headache", count=2,
                          dates=["2026-01-01", "2026-02-01"])
        self.assertEqual(h.record_id, "R001")
        self.assertEqual(h.item, "headache")
        self.assertEqual(h.count, 2)
        self.assertEqual(h.dates, ["2026-01-01", "2026-02-01"])

    def test_dates_defaults_to_empty_list(self):
        h = RecurrenceHit(record_id="R001", item="pain", count=0)
        self.assertEqual(h.dates, [])

    def test_dataclass_equality(self):
        h1 = RecurrenceHit(record_id="R001", item="pain", count=2,
                           dates=["2026-01-01", "2026-02-01"])
        h2 = RecurrenceHit(record_id="R001", item="pain", count=2,
                           dates=["2026-01-01", "2026-02-01"])
        self.assertEqual(h1, h2)

    def test_dataclass_inequality_on_item(self):
        h1 = RecurrenceHit(record_id="R001", item="pain", count=2,
                           dates=["2026-01-01", "2026-02-01"])
        h2 = RecurrenceHit(record_id="R001", item="fever", count=2,
                           dates=["2026-01-01", "2026-02-01"])
        self.assertNotEqual(h1, h2)

    def test_dates_default_does_not_share_between_instances(self):
        # Each instance must have its own dates list (field(default_factory=list)).
        h1 = RecurrenceHit(record_id="R001", item="a", count=0)
        h2 = RecurrenceHit(record_id="R002", item="b", count=0)
        h1.dates.append("2026-01-01")
        self.assertEqual(h2.dates, [])


class TestFormatHitFormat(unittest.TestCase):
    """format_hit output structure."""

    def _make_hit(self, record_id, item, count, dates):
        return RecurrenceHit(record_id=record_id, item=item, count=count, dates=dates)

    def test_exact_format_two_dates(self):
        h = self._make_hit("R001", "poor sleep", 2, ["2026-01-10", "2026-02-02"])
        expected = 'Record R001: "poor sleep" recurred 2 times — 2026-01-10, 2026-02-02'
        self.assertEqual(format_hit(h), expected)

    def test_exact_format_one_date(self):
        # A hit with a single date (e.g. min_count=1) must format without trailing comma.
        h = self._make_hit("R002", "nausea", 1, ["2026-05-01"])
        result = format_hit(h)
        self.assertIn("2026-05-01", result)
        self.assertNotIn(",", result.split("—")[1])  # no comma after sole date

    def test_three_dates_comma_separated(self):
        h = self._make_hit("R003", "fatigue", 3,
                           ["2026-01-01", "2026-02-01", "2026-03-01"])
        result = format_hit(h)
        self.assertIn("2026-01-01, 2026-02-01, 2026-03-01", result)

    def test_em_dash_present_in_output(self):
        h = self._make_hit("R004", "pain", 2, ["2026-01-01", "2026-02-01"])
        self.assertIn("—", format_hit(h))

    def test_item_quoted_in_output(self):
        h = self._make_hit("R005", "back pain", 2, ["2026-01-01", "2026-02-01"])
        result = format_hit(h)
        self.assertIn('"back pain"', result)

    def test_count_appears_in_output(self):
        h = self._make_hit("R006", "dizziness", 5,
                           ["2026-01-01", "2026-02-01", "2026-03-01",
                            "2026-04-01", "2026-05-01"])
        result = format_hit(h)
        self.assertIn("5", result)

    def test_output_is_single_line(self):
        h = self._make_hit("R007", "headache", 2, ["2026-01-01", "2026-02-01"])
        result = format_hit(h)
        self.assertNotIn("\n", result)


class TestSelfTestScenarios(unittest.TestCase):
    """_self_test_scenarios must return 6 tuples that all pass."""

    def test_returns_six_scenarios(self):
        from recurrence import _self_test_scenarios
        results = _self_test_scenarios()
        self.assertEqual(len(results), 6)

    def test_all_scenarios_pass(self):
        from recurrence import _self_test_scenarios
        results = _self_test_scenarios()
        failures = [name for name, ok in results if not ok]
        self.assertEqual(failures, [], msg=f"Failing scenarios: {failures}")

    def test_each_result_is_name_bool_tuple(self):
        from recurrence import _self_test_scenarios
        results = _self_test_scenarios()
        for name, ok in results:
            self.assertIsInstance(name, str)
            self.assertIsInstance(ok, bool)

    def test_run_self_test_returns_zero_on_success(self):
        from recurrence import _run_self_test
        self.assertEqual(_run_self_test(), 0)


class TestBuildParser(unittest.TestCase):
    """build_parser produces a parser with the documented flags."""

    def setUp(self):
        from recurrence import build_parser
        self.parser = build_parser()

    def test_parser_has_self_test_flag(self):
        args = self.parser.parse_args(["--self-test"])
        self.assertTrue(args.self_test)

    def test_parser_has_demo_flag(self):
        args = self.parser.parse_args(["--demo"])
        self.assertTrue(args.demo)

    def test_self_test_defaults_to_false(self):
        args = self.parser.parse_args([])
        self.assertFalse(args.self_test)

    def test_demo_defaults_to_false(self):
        args = self.parser.parse_args([])
        self.assertFalse(args.demo)

    def test_both_flags_can_be_set_together(self):
        args = self.parser.parse_args(["--self-test", "--demo"])
        self.assertTrue(args.self_test)
        self.assertTrue(args.demo)
