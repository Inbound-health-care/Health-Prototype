"""Teeth for the agent-interop validation gate (ADR-0032).

The REAL surface must validate, and the gate must BITE on a broken or
overclaiming card/tool-def — otherwise it is a vacuous green check. Mirrors the
repo's stance that a check that cannot fail is worse than no check.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import agent_card_validate as acv  # noqa: E402

CARD_PATH = ROOT / ".well-known" / "agent-card.json"
TOOLS_PATH = ROOT / "tools" / "mcp" / "tools.json"
STATUS_PATH = ROOT / "STATUS.md"
_PRESENT = CARD_PATH.exists() and TOOLS_PATH.exists() and STATUS_PATH.exists()


@unittest.skipUnless(_PRESENT, "agent-interop surface files absent")
class AgentInteropSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.card = json.loads(CARD_PATH.read_text(encoding="utf-8"))
        cls.tools = json.loads(TOOLS_PATH.read_text(encoding="utf-8"))
        cls.phase = acv.parse_phase(STATUS_PATH.read_text(encoding="utf-8"))

    def test_status_phase_a_and_real_surface_validates(self) -> None:
        self.assertEqual(self.phase, "A")
        ok, errors = acv.validate_agent_surface(self.card, self.tools, self.phase)
        self.assertEqual(errors, [])
        self.assertTrue(ok)

    # --- teeth: each broken/overclaiming variant MUST fail ---

    def test_bites_on_live_streaming_while_phase_a(self) -> None:
        bad = copy.deepcopy(self.card)
        bad["capabilities"]["streaming"] = True
        ok, _ = acv.validate_agent_surface(bad, self.tools, self.phase)
        self.assertFalse(ok)

    def test_bites_on_live_endpoint_while_phase_a(self) -> None:
        bad = copy.deepcopy(self.card)
        bad["x-lifecycle"]["liveEndpoint"] = True
        ok, _ = acv.validate_agent_surface(bad, self.tools, self.phase)
        self.assertFalse(ok)

    def test_bites_on_interop_phase_mismatch(self) -> None:
        bad = copy.deepcopy(self.card)
        bad["x-lifecycle"]["interopPhase"] = "B"
        ok, _ = acv.validate_agent_surface(bad, self.tools, self.phase)
        self.assertFalse(ok)

    def test_bites_on_missing_required_a2a_field(self) -> None:
        bad = copy.deepcopy(self.card)
        del bad["skills"]
        ok, _ = acv.validate_agent_surface(bad, self.tools, self.phase)
        self.assertFalse(ok)

    def test_bites_on_non_kebab_skill_id(self) -> None:
        bad = copy.deepcopy(self.card)
        bad["skills"][0]["id"] = "Detect_Recurrence"
        ok, _ = acv.validate_agent_surface(bad, self.tools, self.phase)
        self.assertFalse(ok)

    def test_bites_on_tool_missing_output_schema(self) -> None:
        bad = copy.deepcopy(self.tools)
        del bad["tools"][0]["outputSchema"]
        ok, _ = acv.validate_agent_surface(self.card, bad, self.phase)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
