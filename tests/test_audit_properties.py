"""test_audit_properties.py — property-based tests for the audit-trail chain
(ADR 0030), extending the repo's Hypothesis coverage (ADR 0025/0027) to the
governance layer.

The hand-written oracle (AUDIT_ANSWER_KEY) pins the audited demo; these
properties pin the CHAIN itself for arbitrary event sequences Hypothesis
generates:

  P1 — any appended sequence verifies: building a trail through the public
       `append` API always yields an internally consistent chain.
  P2 — single-point tamper detection: editing the payload of ANY one entry
       makes `verify` fail AT EXACTLY that entry's seq.
  P3 — head sensitivity: two trails that differ in any one appended payload
       end with different heads (so an external head anchor pins the whole
       history, not just the tail).
  P4 — serialization round-trip: the canonical JSONL line of every entry
       parses back to an entry that re-verifies, with the head preserved.

Hypothesis is dev-only: this module SKIPS cleanly when it is absent (so
`make test` / CI's plain suite stay pure-stdlib green) and runs under
`make proptest` and the CI proptest step. Determinism on CI: derandomized
(ADR 0025).

Run: make proptest   (or)   uvx --with hypothesis python -m unittest tests.test_audit_properties
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import audit  # noqa: E402

try:
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st

    HAS_HYPOTHESIS = True
except ImportError:  # pragma: no cover - dev-only tool absent
    HAS_HYPOTHESIS = False

# Determinism on CI (ADR 0025): when these properties gate a PR they must
# reproduce locally byte-for-byte, so under CI we derandomize. GitHub Actions
# sets CI=true; locally `make proptest` stays random (broader exploration).
if HAS_HYPOTHESIS and os.environ.get("CI"):  # pragma: no cover - CI-only path
    settings.register_profile("ci", derandomize=True)
    settings.load_profile("ci")


def _fixed_clock():
    """Deterministic stepping clock so head differences come ONLY from payloads."""
    tick = [-1]

    def now() -> str:
        tick[0] += 1
        return f"2026-06-11T00:{tick[0] // 60:02d}:{tick[0] % 60:02d}Z"

    return now


def _build(events) -> audit.AuditTrail:
    trail = audit.AuditTrail(now=_fixed_clock())
    for type_, payload in events:
        trail.append(type_, agent="prop test", entity={}, payload=payload)
    return trail


if HAS_HYPOTHESIS:
    # Event payloads: string keys, float-free scalar values — exactly the set
    # `_check_no_floats` admits. Small alphabets keep shrinking readable.
    _KEYS = st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=8)
    _VALUES = st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789 -", max_size=20),
        st.booleans(),
        st.none(),
    )
    _PAYLOADS = st.dictionaries(_KEYS, _VALUES, max_size=5)
    _EVENTS = st.lists(
        st.tuples(st.sampled_from(audit.EVENT_TYPES), _PAYLOADS),
        min_size=1,
        max_size=8,
    )

    class TestChainProperties(unittest.TestCase):
        # -- P1: every appended sequence verifies ------------------------------
        @settings(max_examples=200, deadline=None,
                  suppress_health_check=[HealthCheck.too_slow])
        @given(_EVENTS)
        def test_any_appended_sequence_verifies(self, events):
            self.assertEqual(_build(events).verify(), (True, None))

        # -- P2: tampering any one entry fails at exactly that seq -------------
        @settings(max_examples=200, deadline=None,
                  suppress_health_check=[HealthCheck.too_slow])
        @given(_EVENTS, st.integers(min_value=0, max_value=7))
        def test_single_tamper_fails_at_exactly_that_seq(self, events, index):
            trail = _build(events)
            index %= len(trail.entries)
            trail.entries[index].payload = dict(
                trail.entries[index].payload, __tampered__=1
            )
            self.assertEqual(trail.verify(), (False, index + 1))

        # -- P3: the head pins every payload in the history ---------------------
        @settings(max_examples=200, deadline=None,
                  suppress_health_check=[HealthCheck.too_slow])
        @given(_EVENTS, st.integers(min_value=0, max_value=7))
        def test_head_pins_every_payload(self, events, index):
            index %= len(events)
            type_, payload = events[index]
            changed = list(events)
            changed[index] = (type_, dict(payload, __changed__=1))
            self.assertNotEqual(_build(events).head(), _build(changed).head())

        # -- P4: canonical line round-trip preserves the chain ------------------
        @settings(max_examples=200, deadline=None,
                  suppress_health_check=[HealthCheck.too_slow])
        @given(_EVENTS)
        def test_canonical_line_round_trip_preserves_the_chain(self, events):
            trail = _build(events)
            lines = [
                audit.canonical_json(
                    {
                        "event": e.core(),
                        "prev_hash": e.prev_hash,
                        "entry_hash": e.entry_hash,
                    }
                )
                for e in trail.entries
            ]
            parsed = [
                audit._entry_from_line(line, i) for i, line in enumerate(lines, 1)
            ]
            self.assertEqual(audit.verify_entries(parsed), (True, None))
            self.assertEqual(parsed[-1].entry_hash, trail.head())

else:  # pragma: no cover - hypothesis not installed

    class TestChainProperties(unittest.TestCase):
        @unittest.skip("hypothesis not installed (run: make proptest)")
        def test_properties_require_hypothesis(self):
            pass


if __name__ == "__main__":
    unittest.main()
