"""banned_words.py — the single source of truth for the librarian-rule word check.

The librarian rule (AGENTS.md): the engine and its views SURFACE, COUNT, and CITE —
they never score, rank, diagnose, or say what a pattern *means*. Every view/output
test asserts that none of these interpretive or ranking substrings appears in rendered
output. This tuple used to be copy-pasted into ~10 test modules (audit 2026-06-07,
Tier 4 #14); a forbidden word then had to be added in up to ten places. It lives here
ONCE now — import it (`from tests.banned_words import BANNED`).

This is the FULL suite-wide UNION: every per-rule test checks against the whole set,
so a word banned for one view is banned for all. Two groups:
  - interpretive / severity / direction / causation (the engine must never judge), and
  - ranking / aggregation (the combined report lists, never ranks or totals).

Substring matching is intentional ("diagnos" catches diagnose/diagnosis/diagnostic;
"accelerat" catches accelerate/accelerating). Keep entries lowercase; tests lowercase
the output before scanning.
"""

from __future__ import annotations

BANNED: tuple[str, ...] = (
    # interpretive / severity / direction / causation
    "worsening", "worsen", "severe", "severity", "suggests", "diagnos", "risk",
    "concern", "caution", "abnormal", "score", "relapse", "acute", "accelerat",
    "decelerat", "increasing", "decreasing", "escalat", "declining", "deteriorat",
    "improving", "trend", "associated", "correlated", "linked", "cause", "caused",
    "relationship",
    # ranking / aggregation (the combined view lists, never ranks/totals)
    "top", "most", "priority", "prioritize", "rank", "ranking", "total",
    "highest", "lowest", "worst", "best",
)
