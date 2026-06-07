"""test_extract_multi_properties.py — property-based tests for the fail-closed
multi-patient extractor (ADR 0016), folded in per the freshness check.

The hand-written oracle in test_extract_multi.py pins one batch; these properties
assert the SAFETY INVARIANTS hold for arbitrary batches Hypothesis generates:
  1. no-bleed + accounting — every accepted id is a key that occurs in exactly one
     single-header segment; every entry traces (by span) only to its own segment;
     accepted + quarantined == number of segments; reasons are fixed tokens.
  2. de-identification — a consistent per-patient shift moves every date by exactly
     the offset (intervals preserved), the ADR 0009 claim, for any dates/shift.
  3. additivity — a single-segment batch reduces to extract_records exactly.

Hypothesis is a dev-only tool (no runtime dependency): this module SKIPS cleanly
when it is absent (so `make test` / CI stay pure-stdlib green) and runs under
`make proptest` (uvx --with hypothesis). See the toolchain audit.

Run: make proptest      (or)      uvx --with hypothesis python -m unittest tests.test_extract_multi_properties
"""

from __future__ import annotations

import datetime
import os
import re
import sys
import unittest
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extract import (  # noqa: E402
    _QUARANTINE_REASONS,
    extract_records,
    extract_records_multi,
)

try:
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st

    HAS_HYPOTHESIS = True
except ImportError:  # pragma: no cover - dev-only tool absent
    HAS_HYPOTHESIS = False

# Determinism on CI (ADR 0025): when these properties gate a PR they must reproduce
# locally byte-for-byte, so under CI we derandomize (a fixed search instead of a
# random seed). GitHub Actions sets CI=true; locally `make proptest` stays random
# (broader exploration). The per-test @settings keep their own max_examples and
# inherit derandomize from the loaded profile.
if HAS_HYPOTHESIS and os.environ.get("CI"):  # pragma: no cover - CI-only path
    settings.register_profile("ci", derandomize=True)
    settings.load_profile("ci")

DELIM = "\n---\n"
GAZ = ["poor sleep", "headache", "cough"]
_HEADER = re.compile(r"(?m)^\s*Patient:\s*(.+?)\s*$")


def _expected_accepted(segments: list[str]) -> set[str]:
    """Independently compute which keys SHOULD be accepted: a key is accepted iff
    it is the single distinct header of exactly one segment (no cross-segment
    collision). Computed without the code under test."""
    candidate_keys = [
        next(iter(d))
        for s in segments
        if len(d := set(_HEADER.findall(s))) == 1
    ]
    counts = Counter(candidate_keys)
    return {k for k in candidate_keys if counts[k] == 1}


if HAS_HYPOTHESIS:
    _KEYS = st.sampled_from(["A", "B", "C", "D"])
    _ITEMS = st.sampled_from(GAZ)
    # A safe mid-range so a large shift cannot overflow date bounds.
    _DATES = st.dates(
        min_value=datetime.date(2050, 1, 1), max_value=datetime.date(2060, 12, 31)
    )
    _DATED_LINE = st.builds(lambda d, it: f"{d.isoformat()} {it}.\n", _DATES, _ITEMS)
    _BODY = st.lists(_DATED_LINE, max_size=3).map("".join)

    @st.composite
    def _segment(draw):
        choice = draw(st.sampled_from(["none", "one", "same", "two"]))
        body = draw(_BODY)
        if choice == "none":
            head = ""
        elif choice == "one":
            head = f"Patient: {draw(_KEYS)}\n"
        elif choice == "same":  # same value twice -> 1 distinct -> accept
            k = draw(_KEYS)
            head = f"Patient: {k}\nPatient: {k}\n"
        else:  # two distinct -> ambiguous
            k1 = draw(_KEYS)
            k2 = draw(_KEYS.filter(lambda x: x != k1))
            head = f"Patient: {k1}\nPatient: {k2}\n"
        return head + body

    _DATED_PAIRS = st.lists(st.tuples(_DATES, _ITEMS), max_size=4)

    class TestMultiProperties(unittest.TestCase):
        @settings(max_examples=250, deadline=None,
                  suppress_health_check=[HealthCheck.too_slow])
        @given(st.lists(_segment(), min_size=1, max_size=6))
        def test_no_bleed_and_accounting(self, segments):
            note = DELIM.join(segments)
            result = extract_records_multi(note, GAZ, delimiter=DELIM)
            # Every segment resolves to exactly one outcome.
            self.assertEqual(
                len(result.records) + len(result.quarantined), len(segments)
            )
            for q in result.quarantined:
                self.assertIn(q.reason, _QUARANTINE_REASONS)
            ids = [r["id"] for r in result.records]
            self.assertEqual(len(ids), len(set(ids)))             # no duplicate ids
            self.assertEqual(set(ids), _expected_accepted(segments))
            for r in result.records:
                a, b = r["provenance"]["segment_span"]
                for e in r["entries"]:
                    s, t = e["source_span"]
                    self.assertEqual(note[s:t].casefold(), e["item"].casefold())
                    self.assertTrue(a <= s and t <= b)            # no-bleed

        @settings(max_examples=200, deadline=None)
        @given(_DATED_PAIRS.filter(bool), st.integers(-10_000, 10_000))
        def test_consistent_shift_preserves_every_date(self, pairs, k):
            note = "Patient: P\n" + "".join(
                f"{d.isoformat()} {it}.\n" for d, it in pairs
            )
            r0 = extract_records_multi(note, GAZ, delimiter=DELIM, shift_by_id={"P": 0})
            rk = extract_records_multi(note, GAZ, delimiter=DELIM, shift_by_id={"P": k})
            e0, ek = r0.records[0]["entries"], rk.records[0]["entries"]
            self.assertEqual(len(e0), len(ek))
            for a, b in zip(e0, ek):
                self.assertEqual(
                    datetime.date.fromisoformat(b["date"]),
                    datetime.date.fromisoformat(a["date"]) + datetime.timedelta(days=k),
                )

        @settings(max_examples=150, deadline=None)
        @given(_DATED_PAIRS)
        def test_single_segment_reduces_to_extract_records(self, pairs):
            note = "Patient: P\n" + "".join(
                f"{d.isoformat()} {it}.\n" for d, it in pairs
            )
            multi = extract_records_multi(note, GAZ, delimiter=DELIM).records
            single = extract_records(note, GAZ)
            self.assertEqual(multi[0]["entries"], single[0]["entries"])

else:  # pragma: no cover - hypothesis not installed

    class TestMultiProperties(unittest.TestCase):
        @unittest.skip("hypothesis not installed (run: make proptest)")
        def test_properties_require_hypothesis(self):
            pass


if __name__ == "__main__":
    unittest.main()
