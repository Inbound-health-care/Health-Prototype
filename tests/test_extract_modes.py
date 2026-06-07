"""
test_extract_modes.py — the free-text matching modes (extract.py, slice 2; ADR 0012).

Matching is an EXPLICIT, must-be-chosen MatchConfig: strict (default) / synonyms /
fuzzy / both. These tests assert: strict is unchanged from slice 1 (the safe
default); synonyms remap to a hand-vetted canonical against a hand-written oracle;
fuzzy merges a typo but is BLOCKED from merging affix-antonyms and denylisted
look-alikes, and can exempt drug-name terms; both composes the two; the config
validation forces a coherent, explicit choice (fail loudly); and the librarian
rule still holds in output for every mode.

Run from the repo root:
    python -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.sample_records import (  # noqa: E402
    FREETEXT_EXPECTED_RECORDS,
    FREETEXT_EXPECTED_RECORDS_SYNONYMS,
    FREETEXT_GAZETTEER,
    FREETEXT_SAMPLE_NOTE,
    FREETEXT_SYNONYMS,
)
from extract import (  # noqa: E402
    MODE_DOC,
    MatchConfig,
    _is_affix_antonym,
    _violates_anti_pairing,
    extract_records,
    find_gazetteer_hits,
    format_entry,
)
from recurrence import detect_recurrence  # noqa: E402
from tests.banned_words import BANNED  # noqa: E402


class TestStrictIsTheSafeDefault(unittest.TestCase):
    def test_default_config_is_strict(self):
        self.assertEqual(MatchConfig().mode, "strict")

    def test_strict_default_matches_slice1_oracle(self):
        # No config and an explicit strict config both reproduce slice 1 exactly.
        self.assertEqual(
            extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER),
            FREETEXT_EXPECTED_RECORDS,
        )
        self.assertEqual(
            extract_records(
                FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, config=MatchConfig()
            ),
            FREETEXT_EXPECTED_RECORDS,
        )

    def test_strict_count_is_two(self):
        records = extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER)
        by_item = {h.item: h for h in detect_recurrence(records)}
        self.assertEqual(by_item["poor sleep"].count, 2)


class TestSynonymsMode(unittest.TestCase):
    def setUp(self):
        self.cfg = MatchConfig(mode="synonyms", synonyms=FREETEXT_SYNONYMS)

    def test_records_equal_synonyms_oracle(self):
        self.assertEqual(
            extract_records(FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, config=self.cfg),
            FREETEXT_EXPECTED_RECORDS_SYNONYMS,
        )

    def test_synonym_remap_lifts_recurrence_count(self):
        records = extract_records(
            FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, config=self.cfg
        )
        by_item = {h.item: h for h in detect_recurrence(records)}
        self.assertEqual(by_item["poor sleep"].count, 3)

    def test_synonym_not_in_gazetteer_still_matches(self):
        # A paraphrase absent from the gazetteer surfaces under its canonical.
        cfg = MatchConfig(mode="synonyms", synonyms={"trouble sleeping": "poor sleep"})
        self.assertEqual(
            find_gazetteer_hits("trouble sleeping", ["poor sleep"], config=cfg),
            [(0, 16, "poor sleep")],
        )

    def test_synonym_cites_real_surface_span(self):
        # The emitted item is canonical, but the span points at the literal text.
        records = extract_records(
            FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, config=self.cfg
        )
        insomnia_entry = records[0]["entries"][-1]
        start, end = insomnia_entry["source_span"]
        self.assertEqual(FREETEXT_SAMPLE_NOTE[start:end].casefold(), "insomnia")
        self.assertEqual(insomnia_entry["item"], "poor sleep")


class TestFuzzyMode(unittest.TestCase):
    def test_fuzzy_merges_a_typo(self):
        cfg = MatchConfig(mode="fuzzy", fuzzy_cutoff=0.9)
        self.assertEqual(
            find_gazetteer_hits("poor slep", ["poor sleep"], config=cfg),
            [(0, 9, "poor sleep")],
        )

    def test_exact_still_works_in_fuzzy_mode(self):
        cfg = MatchConfig(mode="fuzzy", fuzzy_cutoff=0.9)
        self.assertEqual(
            find_gazetteer_hits("poor sleep", ["poor sleep"], config=cfg),
            [(0, 10, "poor sleep")],
        )

    def test_below_cutoff_does_not_match(self):
        cfg = MatchConfig(mode="fuzzy", fuzzy_cutoff=0.9)
        self.assertEqual(find_gazetteer_hits("xyzzy", ["poor sleep"], config=cfg), [])

    def test_affix_antonym_is_blocked(self):
        # "hypertension" ~ "hypotension" scores high but flips meaning -> blocked,
        # while a genuine typo of the same term passes at the same cutoff.
        cfg = MatchConfig(mode="fuzzy", fuzzy_cutoff=0.8)
        self.assertEqual(
            find_gazetteer_hits("hypertension", ["hypotension"], config=cfg), []
        )
        self.assertEqual(
            find_gazetteer_hits("hypotensiom", ["hypotension"], config=cfg),
            [(0, 11, "hypotension")],
        )

    def test_explicit_denylist_blocks_a_lookalike(self):
        # The same near-match: allowed by default, blocked when denylisted.
        allowed = MatchConfig(mode="fuzzy", fuzzy_cutoff=0.85)
        denied = MatchConfig(
            mode="fuzzy",
            fuzzy_cutoff=0.85,
            anti_pairings=frozenset({frozenset({"apple", "apples"})}),
        )
        self.assertEqual(
            find_gazetteer_hits("apples", ["apple"], config=allowed),
            [(0, 6, "apple")],
        )
        self.assertEqual(find_gazetteer_hits("apples", ["apple"], config=denied), [])

    def test_no_fuzzy_terms_exemption(self):
        # A term marked no-fuzzy never near-matches (drug-name exemption).
        cfg = MatchConfig(
            mode="fuzzy", fuzzy_cutoff=0.9, no_fuzzy_terms=frozenset({"poor sleep"})
        )
        self.assertEqual(find_gazetteer_hits("poor slep", ["poor sleep"], config=cfg), [])


class TestBothMode(unittest.TestCase):
    def test_synonym_and_typo_together(self):
        cfg = MatchConfig(
            mode="both",
            synonyms={"trouble sleeping": "poor sleep"},
            fuzzy_cutoff=0.9,
        )
        hits = find_gazetteer_hits(
            "trouble sleeping, hedache", ["poor sleep", "headache"], config=cfg
        )
        self.assertEqual([term for _s, _e, term in hits], ["poor sleep", "headache"])


class TestGuardsUnit(unittest.TestCase):
    AFFIX_ANTONYMS = [
        ("hypertension", "hypotension"),
        ("hyperglycemia", "hypoglycemia"),
        ("tachycardia", "bradycardia"),
        ("stable", "unstable"),
        ("compliant", "noncompliant"),
        ("symptomatic", "asymptomatic"),
    ]
    NOT_ANTONYMS = [
        ("poor sleep", "poor slep"),
        ("headache", "hedache"),
        ("hypotension", "hypotensiom"),
    ]

    def test_affix_antonyms_detected(self):
        for a, b in self.AFFIX_ANTONYMS:
            self.assertTrue(_is_affix_antonym(a, b), f"{a} / {b}")
            self.assertTrue(_is_affix_antonym(b, a), f"{b} / {a} (symmetric)")

    def test_typos_are_not_flagged_as_antonyms(self):
        for a, b in self.NOT_ANTONYMS:
            self.assertFalse(_is_affix_antonym(a, b), f"{a} / {b}")

    def test_violates_anti_pairing_combines_both_guards(self):
        empty: frozenset = frozenset()
        self.assertTrue(_violates_anti_pairing("hypertension", "hypotension", empty))
        self.assertFalse(_violates_anti_pairing("apple", "apples", empty))
        denylist = frozenset({frozenset({"apple", "apples"})})
        self.assertTrue(_violates_anti_pairing("apple", "apples", denylist))
        self.assertFalse(_violates_anti_pairing("apple", "apple", denylist))


class TestConfigForcesAnExplicitChoice(unittest.TestCase):
    def test_unknown_mode_raises(self):
        with self.assertRaises(ValueError):
            MatchConfig(mode="loose")

    def test_strict_rejects_smuggled_synonyms(self):
        with self.assertRaises(ValueError):
            MatchConfig(mode="strict", synonyms={"a": "b"})

    def test_strict_rejects_smuggled_fuzzy_cutoff(self):
        with self.assertRaises(ValueError):
            MatchConfig(mode="strict", fuzzy_cutoff=0.9)

    def test_synonyms_mode_requires_a_map(self):
        with self.assertRaises(ValueError):
            MatchConfig(mode="synonyms")
        with self.assertRaises(ValueError):
            MatchConfig(mode="synonyms", synonyms={})

    def test_fuzzy_mode_requires_a_cutoff(self):
        with self.assertRaises(ValueError):
            MatchConfig(mode="fuzzy")

    def test_bad_cutoff_raises(self):
        with self.assertRaises(ValueError):
            MatchConfig(mode="fuzzy", fuzzy_cutoff=1.5)

    def test_affix_antonym_synonym_is_refused(self):
        with self.assertRaises(ValueError):
            MatchConfig(mode="synonyms", synonyms={"stable": "unstable"})


class TestLibrarianRuleHoldsInEveryMode(unittest.TestCase):
    BANNED = BANNED  # the shared suite-wide union — see tests/banned_words.py
    CONFIGS = {
        "strict": MatchConfig(),
        "synonyms": MatchConfig(mode="synonyms", synonyms=FREETEXT_SYNONYMS),
        "fuzzy": MatchConfig(mode="fuzzy", fuzzy_cutoff=0.9),
        "both": MatchConfig(
            mode="both", synonyms=FREETEXT_SYNONYMS, fuzzy_cutoff=0.9
        ),
    }

    def test_no_mode_adds_interpretation_or_context_cue(self):
        for name, cfg in self.CONFIGS.items():
            records = extract_records(
                FREETEXT_SAMPLE_NOTE, FREETEXT_GAZETTEER, config=cfg
            )
            for entry in records[0]["entries"]:
                self.assertNotIn("context_cue", entry, name)
                line = format_entry(entry).lower()
                self.assertIn(entry["item"], line)
                for banned in self.BANNED:
                    self.assertNotIn(banned, line, f"{name}: banned {banned!r}")


class TestExplainModesDocuments(unittest.TestCase):
    def test_mode_doc_names_every_mode(self):
        for mode in ("strict", "synonyms", "fuzzy", "both"):
            self.assertIn(mode, MODE_DOC)

    def test_mode_doc_names_the_core_risk(self):
        # The honest risk (typo vs opposite) must be stated, not buried.
        self.assertIn("hypotension", MODE_DOC)


if __name__ == "__main__":
    unittest.main()
