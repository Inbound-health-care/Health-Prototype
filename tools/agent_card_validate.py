#!/usr/bin/env python3
"""Validate the static agent-interop surface (A2A Agent Card + MCP tool-defs).

Enforces the no-overclaim honesty rule from ADR-0032: while STATUS.md records
``agent_interop_phase: A``, the card must NOT advertise a live, callable
endpoint. Pure standard library — this repo's runtime stays stdlib-only.

``validate_agent_surface`` and ``parse_phase`` are importable so
``tests/test_agent_card.py`` can prove the gate BITES (a broken or overclaiming
card must fail). Run ``python tools/agent_card_validate.py`` to check the real
files; it exits 1 on any error.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARD_PATH = ROOT / ".well-known" / "agent-card.json"
TOOLS_PATH = ROOT / "tools" / "mcp" / "tools.json"
STATUS_PATH = ROOT / "STATUS.md"

_KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_PHASE = re.compile(r"^agent_interop_phase:\s*(\S+)\s*$", re.MULTILINE)


def parse_phase(status_text: str) -> str | None:
    """Read ``agent_interop_phase`` from STATUS.md (a marker line or front-matter)."""
    match = _PHASE.search(status_text)
    return match.group(1) if match else None


def validate_agent_surface(card: dict, tools: dict, phase: str | None) -> tuple[bool, list[str]]:
    """Return ``(ok, errors)``. Never raises, so the teeth test can assert on any shape."""
    errors: list[str] = []

    def req(cond: object, msg: str) -> None:
        if not cond:
            errors.append(msg)

    card = card if isinstance(card, dict) else {}
    tools = tools if isinstance(tools, dict) else {}

    # --- A2A Agent Card: five required top-level fields + each skill's fields ---
    req(isinstance(card.get("name"), str) and card.get("name"), "card.name missing")
    req(isinstance(card.get("description"), str) and card.get("description"), "card.description missing")
    req(isinstance(card.get("version"), str) and card.get("version"), "card.version missing")
    req(isinstance(card.get("url"), str) and card.get("url"), "card.url missing")
    skills = card.get("skills")
    req(isinstance(skills, list) and len(skills) >= 1, "card.skills must be a non-empty array")
    for i, skill in enumerate(skills if isinstance(skills, list) else []):
        skill = skill if isinstance(skill, dict) else {}
        sid = skill.get("id")
        req(isinstance(sid, str) and bool(_KEBAB.match(sid)), f"skill[{i}].id missing or not kebab-case")
        req(isinstance(skill.get("name"), str) and skill.get("name"), f"skill[{i}].name missing")
        req(isinstance(skill.get("description"), str) and skill.get("description"), f"skill[{i}].description missing")

    # --- lifecycle block (machine-readable growing-until-frozen signal) ---
    lc = card.get("x-lifecycle")
    req(isinstance(lc, dict), "card.x-lifecycle missing")
    if isinstance(lc, dict):
        req(isinstance(lc.get("status"), str), "x-lifecycle.status missing")
        req(isinstance(lc.get("frozen"), bool), "x-lifecycle.frozen must be a boolean")
        req(isinstance(lc.get("interopPhase"), str), "x-lifecycle.interopPhase missing")
        req(isinstance(lc.get("liveEndpoint"), bool), "x-lifecycle.liveEndpoint must be a boolean")
    lc = lc if isinstance(lc, dict) else {}

    # --- honesty: no live endpoint while phase A (ADR-0032) ---
    req(phase is not None, "STATUS.md agent_interop_phase not found")
    if phase == "A":
        caps = card.get("capabilities")
        caps = caps if isinstance(caps, dict) else {}
        req(caps.get("streaming") is False, "phase A: card.capabilities.streaming must be false (no live A2A streaming endpoint)")
        req(lc.get("liveEndpoint") is False, "phase A: x-lifecycle.liveEndpoint must be false")
        req(lc.get("interopPhase") == phase, f"phase A: x-lifecycle.interopPhase ({lc.get('interopPhase')}) must match STATUS.md ({phase})")

    # --- MCP tool-defs: each tool needs a name, description, object in/out schemas ---
    tool_list = tools.get("tools")
    req(isinstance(tool_list, list) and len(tool_list) >= 1, "tools.tools must be a non-empty array")
    for i, tool in enumerate(tool_list if isinstance(tool_list, list) else []):
        tool = tool if isinstance(tool, dict) else {}
        req(isinstance(tool.get("name"), str) and tool.get("name"), f"tool[{i}].name missing")
        req(isinstance(tool.get("description"), str) and tool.get("description"), f"tool[{i}].description missing")
        in_schema = tool.get("inputSchema")
        out_schema = tool.get("outputSchema")
        req(isinstance(in_schema, dict) and in_schema.get("type") == "object", f"tool[{i}].inputSchema must be an object schema")
        req(isinstance(out_schema, dict) and out_schema.get("type") == "object", f"tool[{i}].outputSchema must be an object schema")

    return (len(errors) == 0, errors)


def main() -> int:
    card = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    tools = json.loads(TOOLS_PATH.read_text(encoding="utf-8"))
    phase = parse_phase(STATUS_PATH.read_text(encoding="utf-8"))
    ok, errors = validate_agent_surface(card, tools, phase)
    if ok:
        n = len(tools.get("tools", []))
        print(f"agent-card: OK — A2A card + {n} MCP tool(s) valid; honesty check passed (phase {phase}).")
        return 0
    print("agent-card: INVALID —", file=sys.stderr)
    for err in errors:
        print(f"  - {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
