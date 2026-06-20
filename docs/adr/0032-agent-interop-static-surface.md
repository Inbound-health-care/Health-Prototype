# 0032 — Agent-interop: a static A2A + MCP surface for `detect_recurrence`

## Context

Across the operator's repos, a deterministic, no-LLM "agent-interop" surface is
being rolled out: a static A2A **Agent Card** plus static **MCP tool
definitions** that let other agents discover and (eventually) call existing
deterministic functions. The pattern shipped first in `Demo-math-slot-test-only`
and is being applied where a repo has a real, honest capability to advertise.

This repository has exactly one such capability worth surfacing: the
deterministic recurrence engine `detect_recurrence()` (`recurrence.py`). It is
pure, defensive (malformed input is skipped, not raised), exact-match by default
with opt-in normalize/synonyms/fuzzy layers, and it surfaces and **cites** only —
it never scores, ranks, diagnoses, triages, or recommends. That "librarian"
boundary is the whole point of the project and must not be eroded by the act of
publishing a machine-readable description of it.

The constraint, restated: this is a research/training prototype on **synthetic
data**. An agent-interop card must not read as a clinical, diagnostic, or
medical-decision capability.

## Decision

Add a **phase-A, static-only** agent-interop surface — no server, no live
endpoint, therefore no authentication:

- `.well-known/agent-card.json` — A2A discovery card advertising the single skill
  `detect-recurrence`. `url` points to the repository (not a live JSON-RPC
  endpoint); `capabilities.streaming` is `false`; a custom `x-lifecycle` block
  records `interopPhase: "A"`, `liveEndpoint: false`, and the growing-not-frozen
  status. The description carries the librarian / non-clinical framing verbatim.
- `tools/mcp/tools.json` — one MCP tool-def, `detect_recurrence`, whose
  input/output schemas mirror the real function signature and `RecurrenceHit`
  return shape.
- `tools/agent_card_validate.py` — a **stdlib-only** validator that checks the
  A2A required fields, kebab-case skill ids, the lifecycle block, and the MCP
  tool schemas, and enforces the **no-overclaim honesty rule**: while STATUS.md
  records `agent_interop_phase: A`, the card may not advertise a live endpoint or
  streaming, and its `interopPhase` must match STATUS.md.
- `tests/test_agent_card.py` — teeth: the real surface validates AND six
  broken/overclaiming variants each fail, so the gate cannot go vacuously green.
- `STATUS.md` gains a machine-readable `agent_interop_phase: A` marker; the new
  files are registered in `.github/control-policy.json` `required_files`; `make
  agent-card` runs the validator and is wired into `make check` and CI; the
  validator is added to the canonical `make compile` file list.
- `docs/agent-interop.md` — the machine-readability discovery sheet (where the
  card + tool-def live, and what is intentionally NOT claimed).

Phase B (a live A2A/MCP endpoint plus machine-to-machine auth) is explicitly
deferred and out of scope here.

## Consequences

Positive:

- The repo becomes discoverable and consumable by agents via the standard
  `/.well-known/agent-card.json` path, with the deterministic, no-LLM nature and
  the librarian boundary stated in machine-readable form.
- The honesty rule is enforced, not just documented: the card cannot drift into
  claiming a live or clinical capability without the gate failing.
- The runtime stays pure stdlib; the validator adds no dependency.
- The surface is static and version-pinned — no new runtime attack surface.

Trade-offs:

- The card describes a function in `recurrence.py`; if that signature changes,
  the tool-def must be updated alongside it (the validator checks shape, not that
  the schema still matches the live function — that stays a review responsibility).
- A static card is not yet *callable*; the value is discovery/description until a
  phase-B endpoint exists (deliberately deferred).

## Confirmation

Required confirmation for this PR:

```bash
python tools/agent_card_validate.py
python -m unittest tests.test_agent_card
make check
```

CI confirmation:

- The new `agent-card` step passes in `CI`.
- `Repository controls` passes with the new `required_files`.
- Existing `CI`, `Sensitive change scan`, and `Dependency review` workflows still pass.

## Evidence level

IMPLEMENTED_UNVERIFIED until the PR checks pass and Scott or CI confirms the new
gate on the branch. The card makes no clinical or medical-safety claim by
construction; that boundary is restated here and enforced by the validator.
