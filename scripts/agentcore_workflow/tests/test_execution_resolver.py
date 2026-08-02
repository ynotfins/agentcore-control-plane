from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from agentcore_workflow.execution_resolver import (  # noqa: E402
    governed_node,
    resolve_execution_profile,
)
from agentcore_workflow.workflow import NODE_ORDER, build_topology, topology_fingerprint  # noqa: E402


def _state(*, risk: str = "medium") -> dict:
    return {
        "project_id": "",
        "project_key": "fixture",
        "current_risk_class": risk,
        "provider": "openrouter",
        "model": "deepseek/deepseek-v4-pro",
        "active_tools": [],
    }


def test_every_existing_node_resolves_without_topology_change():
    for node in NODE_ORDER:
        profile = resolve_execution_profile(
            _state(risk="high" if node == "ab_alternate" else "medium"),
            node,
        )
        assert profile.roles
        assert profile.node == node
    assert len(NODE_ORDER) == 15
    assert topology_fingerprint(build_topology()) == topology_fingerprint(build_topology())


def test_security_critic_activates_only_for_high_risk():
    medium = resolve_execution_profile(_state(risk="medium"), "critics_and_score")
    high = resolve_execution_profile(_state(risk="high"), "critics_and_score")
    assert "security-critic" not in medium.roles
    assert "security-critic" in high.roles
    assert len(high.skills) <= 4


def test_builder_receives_only_current_jit_tools():
    profile = resolve_execution_profile(
        _state(),
        "da_builder",
        active_tools=("depwire-verify_change", "filesystem-edit_file"),
    )
    assert set(profile.tools) == {"depwire-verify_change", "filesystem-edit_file"}


def test_gemini_provider_resolves_to_provider_model_spec():
    state = _state()
    state["provider"] = "gemini"
    state["model"] = "gemini-3.6-flash"
    profile = resolve_execution_profile(state, "da_builder")
    assert profile.model_id == "gemini:gemini-3.6-flash"


def test_wrapper_persists_resolution_evidence_without_changing_route():
    def node(state):
        assert state["resolved_execution_profile"]["roles"]
        return {"next_action": "gate_check"}

    result = governed_node("start", node)(_state())
    assert result["next_action"] == "gate_check"
    assert len(result["resolved_execution_history"]) == 1
    assert len(result["resolved_execution_profile"]["resolution_sha256"]) == 64
