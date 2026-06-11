# 0030 — Governance audit trail: hash-chained event log + deterministic monitor (ADR 0029 Stage 1)

**Status:** CONFIRMED_ASSISTANT_SIDE

## Context

ADR 0029 planned a three-stage, deterministic, librarian-safe rollout and put
governance first: an append-only, tamper-evident record of what the engine
surfaced, plus a monitor that reports counts — extending the ADR 0028 baseline
from *how the repo changes* to *what the engine did*. The phase ran under the
new-phase discipline: standards research first
(`docs/RESEARCH_2026-06-11_audit-trail-standards.md` — RFC 6962 chains, RFC 8785
canonicalization, 45 CFR 164.312(b) / ASTM E2147-18 / FHIR AuditEvent as concept
references, OWASP logging), then a hand-written oracle (`AUDIT_ANSWER_KEY`,
landed in its own commit before any code), then the build.

## Decision

New module `audit.py` (pure stdlib; imports `recurrence` + `extract`, never the
reverse — a front door, like the views):

- **Chain:** `entry_hash = SHA-256(prev_hash + "\n" + canonical_json(event))`,
  genesis `"0"*64`. Canonical JSON is the stdlib RFC 8785 approximation
  (sorted keys, tight separators, ASCII) with **floats rejected by validation**
  (float repr is the canonicalization hazard; carry e.g. `fuzzy_cutoff` as a
  string).
- **Events:** one per audited run — `extract` / `extract_multi` / `report` —
  via pass-through wrappers (`audited_*`) that return exactly what the
  un-audited calls return. Field names follow FHIR AuditEvent vocabulary
  (`type` / `recorded` / `agent` / `entity`) as a naming reference only.
- **Digests + counts, never values (OWASP):** events carry input/output/config
  SHA-256 digests and per-lens counts. Even record ids are stored as per-id
  digests — an extracted record's id IS the patient key, so the trail never
  carries it as a value; coverage stays provable by hashing the id you hold.
  This was caught by the suite's own no-identifier test during the build and
  fixed before landing (raw ids briefly appeared in the event entity).
- **Persistence:** optional JSONL (one canonical line per event; flush+fsync;
  single-writer by design — stdlib has no portable lock). Re-opening a file
  verifies and CONTINUES its chain.
- **Honest limits, stated in-module and pinned by a test:** the chain catches
  in-place edits, insertion, deletion, and reordering; **tail truncation and
  whole-file rewrite are only detectable against an externally recorded head**
  (`head()` / `--head`; publish the value outside the file). An HMAC-signed
  head was considered and rejected: this is a zero-secret repo, and a key with
  nowhere to live is theater.
- **Monitor:** `summarize` / `compare` report event counts, findings-by-lens,
  and quarantine-by-reason, plus signed differences between trail windows —
  numbers only, banned-words-clean. The librarian rule holds in the trail
  exactly as it does in the views: it records and cites; it never interprets.
- **Wiring:** `make compile` list, `make selftest` (`python audit.py
  --self-test`), `make proptest` + the CI proptest step
  (`tests.test_audit_properties`). CLI: `--self-test | --demo | --verify FILE |
  --head FILE | --summary FILE | --version`.

Rejected alternatives: storing finding text in the trail (duplicates surfaced
content into a second file — provenance is provable by `report_sha256` instead);
Merkle trees (RFC 6962's consistency proofs are for *distributed* verifiers; a
local single-writer chain + external head gives the same tamper-evidence here);
an ML drift monitor (ADR 0029 reframed it — a deterministic engine has no model
to drift; the monitor is telemetry).

## Consequences

- Every audited run is now reconstructable with proof: re-render the output you
  hold, re-hash, match the trail.
- The five clinical modules are byte-identical to `main` (verified by diff);
  auditing is strictly opt-in and additive — un-audited calls are untouched.
- The trail is safe to keep even where the data is not (digests + counts only),
  which is the property a real-PHI future needs the most.
- Tamper-evidence is honest, not oversold: without an externally recorded head,
  truncation/rewrite pass — the limit is documented where the tool is used.
- One more module in the compile/selftest lists; suite grows 267 → 317 tests
  (7 expected skips), properties 8 → 12.

## Confirmation

- `python audit.py --self-test` — 8/8, asserted toward the pre-committed
  hand oracle (`AUDIT_ANSWER_KEY`, tallied by hand from `REPORT_ANSWER_KEY`
  and the FREETEXT multi oracles).
- `make check` green — **317 tests** (7 expected skips: Hypothesis + live-JS),
  self-tests 6 + 10 + 8, ruff clean.
- `CI=1 make proptest` — **12/12** (4 new chain properties: any-sequence
  verifies; single tamper fails at exactly its seq; the head pins every
  payload; canonical round-trip preserves the chain).
- `make scan-sensitive` — OK.
- `git diff origin/main -- recurrence.py extract.py view_html.py report_html.py
  digest_html.py` — empty.
- Tamper-class coverage in `tests/test_audit.py`: payload/hash/prev-hash edits,
  middle deletion, reorder, insertion all caught at the right seq; the
  truncation limit is itself a test (passes `verify`, fails `verify_head`).

CONFIRMED_USER_SIDE when Scott runs `python audit.py --demo` (or `--self-test`)
on his own device.

## Research basis

- `docs/RESEARCH_2026-06-11_audit-trail-standards.md` (RESEARCH_ONLY) — the
  dated, sourced evidence: RFC 6962/9162, Ma & Tsudik 2008 (truncation), RFC
  8785, NIST SP 800-92r1 (draft status), 45 CFR 164.312(b), ASTM E2147-18,
  HL7 FHIR AuditEvent, OWASP Logging Cheat Sheet / Top 10:2025 A09.
- Plan: ADR 0029 (Stage 1). Baseline this extends: ADR 0028.
