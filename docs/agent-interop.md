# Agent-interop (A2A / MCP) — discovery sheet

The machine-readability layer: where this repo's agent-interop surface lives and, just as
importantly, what it does **not** claim. Decision + rationale: `docs/adr/0032-agent-interop-static-surface.md`.
Lifecycle/phase: `STATUS.md` (`agent_interop_phase`).

## Where the surface lives

| Artifact | Path | What it is |
|---|---|---|
| A2A Agent Card | `.well-known/agent-card.json` | Static discovery card (RFC 8615 path). Advertises the skill `detect-recurrence`. |
| MCP tool-defs | `tools/mcp/tools.json` | Static tool definition for `detect_recurrence` (input/output schemas mirror the real function). |
| Honesty validator | `tools/agent_card_validate.py` | `make agent-card` — checks the card/tool-defs and enforces the no-overclaim rule. |
| Teeth | `tests/test_agent_card.py` | Proves the validator bites on a broken/overclaiming card. |

Pinned versions: **A2A v1.0** (the top-level `protocolVersion` field was removed in v1.0; lifecycle
lives in the custom `x-lifecycle` block) · **MCP 2025-06-18**.

## The one skill: `detect-recurrence`

Wraps `detect_recurrence(records, field="item", min_count=2, normalize=False, synonyms=None,
fuzzy_cutoff=None)` in `recurrence.py`. Input records are `{id, entries:[{date, item, source_span}]}`;
output is a list of hits, each `{record_id, item, count, dates, variants}`. Deterministic and
defensive; exact-match by default, with opt-in normalize/synonyms/fuzzy layers (every merge is still
cited in `variants`).

## What this is NOT (the librarian boundary)

- **No live endpoint.** Phase A is a static, committed surface only — no server, no JSON-RPC/MCP
  endpoint, no authentication. `url` points at the repository. A live endpoint + machine-to-machine
  auth is **phase B**, deferred. The validator fails the build if the card claims a live transport
  while `STATUS.md` says phase A.
- **No clinical claim.** This is a research/training prototype on **synthetic data**. The skill
  surfaces and cites recurrence provenance; it does **not** diagnose, triage, score, rank, infer
  causation, or recommend. See `SECURITY.md` / `SECURITY_AND_TOOL_POLICY.md`.

## Validate

```bash
make agent-card                       # validator over the real files
python -m unittest tests.test_agent_card
```
