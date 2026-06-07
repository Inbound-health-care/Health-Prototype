"""test_rule_properties.py — property-based (metamorphic) tests for the FIVE
surfacing rules (recurrence.py), folded in per the 2026 eval-methodology research
(ADR 0027).

The hand-written oracle (data/sample_records.py) pins the rules on ~9 crafted
records; the multi-patient EXTRACTOR already has Hypothesis properties
(test_extract_multi_properties.py). These properties extend that coverage UP to
the RULE layer — metamorphic relations that must hold for arbitrary records
Hypothesis generates, at the documented default thresholds:

  P1 — record isolation: appending a disjoint record never changes any OTHER
       record's findings (the no-bleed promise, at the rule layer). Catches
       cross-record state leaks (shared mutable, mis-scoped keys).
  P2 — reordering invariance: shuffling the record list AND the entries within a
       record leaves the finding SET identical. Catches order/position/state bugs
       the fixed-order oracle cannot see.
  P3 — shift invariance: a constant date shift maps recurrence dates by exactly
       the offset and leaves every interval/count finding (gap days, frequency
       window span, cadence intervals, co-occurrence counts) unchanged. Catches
       mixed shifted/unshifted-date arithmetic.

The rules are deterministic, pure-stdlib functions; these are pure invariants (no
banned-word output). Hypothesis is dev-only: this module SKIPS cleanly when it is
absent (so `make test` / CI stay pure-stdlib green) and runs under `make proptest`
and the CI proptest step. Determinism on CI: derandomized (ADR 0025).

Run: make proptest   (or)   uvx --with hypothesis python -m unittest tests.test_rule_properties
"""

from __future__ import annotations

import dataclasses
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recurrence import (  # noqa: E402
    detect_cadence_change,
    detect_cooccurrence,
    detect_frequency,
    detect_gap,
    detect_recurrence,
)

try:
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st

    HAS_HYPOTHESIS = True
except ImportError:  # pragma: no cover - dev-only tool absent
    HAS_HYPOTHESIS = False

# Determinism on CI (ADR 0025): when these properties gate a PR they must
# reproduce locally byte-for-byte, so under CI we derandomize. GitHub Actions sets
# CI=true; locally `make proptest` stays random (broader exploration).
if HAS_HYPOTHESIS and os.environ.get("CI"):  # pragma: no cover - CI-only path
    settings.register_profile("ci", derandomize=True)
    settings.load_profile("ci")


# All five rules share one record-grouping core, so the structural metamorphic
# relations (P1, P2) are asserted across the whole registry at once. Each is
# called with default thresholds — the documented v0 behavior the oracle pins.
_DETECTORS = (
    detect_recurrence,
    detect_gap,
    detect_frequency,
    detect_cooccurrence,
    detect_cadence_change,
)


def _shift_iso(date_str: str, k: int) -> str:
    """Shift an ISO date string by k days; '' (undated) stays ''."""
    if not date_str:
        return date_str
    return (datetime.date.fromisoformat(date_str) + datetime.timedelta(days=k)).isoformat()


def _shift_records(records: list, k: int) -> list:
    """Copy records with every DATED entry's date shifted by k days (undated
    entries untouched)."""
    out = []
    for r in records:
        entries = [
            {**e, "date": _shift_iso(e["date"], k)} if e.get("date") else dict(e)
            for e in r["entries"]
        ]
        out.append({"id": r["id"], "entries": entries})
    return out


def _freq_span(hit) -> int:
    """A frequency hit's window length in days (shift-invariant)."""
    return (
        datetime.date.fromisoformat(hit.window_end)
        - datetime.date.fromisoformat(hit.window_start)
    ).days


if HAS_HYPOTHESIS:
    # Small item alphabet so repeats (and thus findings) are common; dates in a
    # safe mid-range so a large shift cannot overflow date bounds (matches the
    # extractor property file's convention).
    _ITEMS = st.sampled_from(["poor sleep", "anxiety", "headache", "cough"])
    _DATES = st.dates(
        min_value=datetime.date(2050, 1, 1), max_value=datetime.date(2060, 12, 31)
    )
    _ENTRY = st.one_of(
        st.builds(lambda d, it: {"date": d.isoformat(), "item": it}, _DATES, _ITEMS),
        st.builds(lambda it: {"item": it}, _ITEMS),  # undated occurrence
    )
    _ENTRIES = st.lists(_ENTRY, max_size=8)

    @st.composite
    def _records(draw, max_size: int = 4):
        """A list of records with UNIQUE ids R0..Rn (so 'another record's
        findings' is well defined). 'NEW' is never used here, leaving it free for
        the disjoint record in the isolation property."""
        entry_lists = draw(st.lists(_ENTRIES, max_size=max_size))
        return [{"id": f"R{i}", "entries": es} for i, es in enumerate(entry_lists)]

    @st.composite
    def _records_and_shuffled(draw):
        """(records, shuffled) where shuffled permutes the record list AND the
        entries within each record — both orderings the engine must ignore."""
        base = draw(_records())
        order = draw(st.permutations(range(len(base))))
        shuffled = []
        for i in order:
            es = base[i]["entries"]
            eorder = draw(st.permutations(range(len(es))))
            shuffled.append({"id": base[i]["id"], "entries": [es[j] for j in eorder]})
        return base, shuffled

    class TestRuleLayerProperties(unittest.TestCase):
        # -- P1: record isolation (no-bleed at the rule layer) ----------------
        @settings(max_examples=200, deadline=None,
                  suppress_health_check=[HealthCheck.too_slow])
        @given(_records(), _ENTRIES)
        def test_adding_record_preserves_others(self, records, new_entries):
            r_new = {"id": "NEW", "entries": new_entries}
            ids = {r["id"] for r in records}
            for detect in _DETECTORS:
                base = detect(records)
                augmented = detect(records + [r_new])
                kept = [h for h in augmented if h.record_id in ids]
                self.assertEqual(kept, base, detect.__name__)

        # -- P2: reordering invariance ----------------------------------------
        @settings(max_examples=200, deadline=None,
                  suppress_health_check=[HealthCheck.too_slow])
        @given(_records_and_shuffled())
        def test_reordering_preserves_findings(self, pair):
            base, shuffled = pair
            for detect in _DETECTORS:
                self.assertEqual(
                    sorted(detect(base), key=dataclasses.astuple),
                    sorted(detect(shuffled), key=dataclasses.astuple),
                    detect.__name__,
                )

        # -- P3: shift invariance ---------------------------------------------
        @settings(max_examples=200, deadline=None)
        @given(_records(), st.integers(-10_000, 10_000))
        def test_shift_maps_recurrence_dates(self, records, k):
            base = detect_recurrence(records)
            shifted = detect_recurrence(_shift_records(records, k))
            self.assertEqual(len(base), len(shifted))
            for b, s in zip(base, shifted):
                self.assertEqual(
                    (s.record_id, s.item, s.count, s.variants),
                    (b.record_id, b.item, b.count, b.variants),
                )
                self.assertEqual(s.dates, [_shift_iso(d, k) for d in b.dates])

        @settings(max_examples=200, deadline=None)
        @given(_records(), st.integers(-10_000, 10_000))
        def test_shift_preserves_intervals_and_counts(self, records, k):
            shifted = _shift_records(records, k)
            # gap: the gap length (a date delta) is shift-invariant.
            self.assertEqual(
                [(h.record_id, h.item, h.gap_days) for h in detect_gap(records)],
                [(h.record_id, h.item, h.gap_days) for h in detect_gap(shifted)],
            )
            # frequency: count and window span are shift-invariant.
            self.assertEqual(
                [(h.record_id, h.item, h.count, _freq_span(h))
                 for h in detect_frequency(records)],
                [(h.record_id, h.item, h.count, _freq_span(h))
                 for h in detect_frequency(shifted)],
            )
            # cadence: before/after intervals are shift-invariant.
            self.assertEqual(
                [(h.record_id, h.item, h.before_interval, h.after_interval)
                 for h in detect_cadence_change(records)],
                [(h.record_id, h.item, h.before_interval, h.after_interval)
                 for h in detect_cadence_change(shifted)],
            )
            # co-occurrence: shared-date count is shift-invariant.
            self.assertEqual(
                [(h.record_id, h.item_a, h.item_b, h.count)
                 for h in detect_cooccurrence(records)],
                [(h.record_id, h.item_a, h.item_b, h.count)
                 for h in detect_cooccurrence(shifted)],
            )

else:  # pragma: no cover - hypothesis not installed

    class TestRuleLayerProperties(unittest.TestCase):
        @unittest.skip("hypothesis not installed (run: make proptest)")
        def test_properties_require_hypothesis(self):
            pass


if __name__ == "__main__":
    unittest.main()
