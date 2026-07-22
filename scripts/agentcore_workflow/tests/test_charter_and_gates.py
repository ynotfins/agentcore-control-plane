"""Unit tests for charter synthesis and expanded deterministic gates."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from agentcore_workflow.charter import (  # noqa: E402
    first_micro_key,
    m6_catalogue,
    synthesize_from_goal,
    use_m6_hardcoded_catalogue,
)
from agentcore_workflow.critics import judge  # noqa: E402
from agentcore_workflow.gates import (  # noqa: E402
    GATE_REGISTRY,
    gate_filesystem_boundary,
    gate_formatting,
    gate_secret_scan,
    run_all_gates,
)
from agentcore_workflow.workflow import build_topology, topology_fingerprint  # noqa: E402


FINGERPRINT_LOCKED = "a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32"


def test_topology_fingerprint_unchanged():
    fp = topology_fingerprint(build_topology())
    assert fp == FINGERPRINT_LOCKED


def test_m6_catalogue_preserved_without_acceptance():
    assert use_m6_hardcoded_catalogue("M6") is True
    assert use_m6_hardcoded_catalogue("M6", acceptance_criteria=[]) is True
    assert use_m6_hardcoded_catalogue("M6", acceptance_criteria=["x"]) is False
    assert use_m6_hardcoded_catalogue("M7", acceptance_criteria=None) is False
    assert use_m6_hardcoded_catalogue("M6", charter_override=True) is False
    cat = m6_catalogue()
    assert cat["macro_steps"][0]["key"] == "M6.1"
    assert first_micro_key(cat["macro_steps"], cat["micro_steps"], "M6.1") == "M6.1.1"


def test_synthesize_from_goal_deterministic():
    a = synthesize_from_goal(
        "Fix calc.add\n- add unit tests\n- run pytest",
        milestone_key="G1",
        acceptance_criteria=["tests pass", "no secret leak"],
        risk_profile="high",
    )
    b = synthesize_from_goal(
        "Fix calc.add\n- add unit tests\n- run pytest",
        milestone_key="G1",
        acceptance_criteria=["tests pass", "no secret leak"],
        risk_profile="high",
    )
    assert a["macro_steps"] == b["macro_steps"]
    assert a["micro_steps"] == b["micro_steps"]
    assert a["acceptance_criteria"] == ["tests pass", "no secret leak"]
    assert first_micro_key(a["macro_steps"], a["micro_steps"]) != ""


def test_judge_cannot_waive_hard_gate_failure():
    det = [{"check": "c1", "passed": True}]
    gv = {"requirement": "pass", "lint": "fail"}
    verdict, reason = judge(0.99, det, gv, "low")
    assert verdict == "block"
    assert "non-waivable" in reason.lower() or "lint" in reason


def test_formatting_skips_when_tool_absent(monkeypatch):
    monkeypatch.setattr("agentcore_workflow.gates._tool_available", lambda _cmd: False)
    verdict, detail = gate_formatting({"autonomous": False})
    assert verdict == "warn"
    assert detail.get("skipped") is True


def test_formatting_fails_when_required_evidence_missing_autonomous(monkeypatch):
    monkeypatch.setattr("agentcore_workflow.gates._tool_available", lambda _cmd: False)
    verdict, detail = gate_formatting({
        "autonomous": True,
        "required_gates": ["formatting"],
    })
    assert verdict == "fail"
    assert "required evidence" in detail.get("reason", "").lower()


def test_secret_scan_detects_pattern():
    verdict, detail = gate_secret_scan({
        "execution_result": {"diff": "api_key=SUPERSECRETVALUE123"},
    })
    assert verdict == "fail"
    assert detail.get("violations")


def test_filesystem_boundary_rejects_c_drive():
    verdict, _ = gate_filesystem_boundary({"worktree_path": r"C:\Windows\Temp\evil"})
    assert verdict == "fail"


def test_filesystem_boundary_allows_github():
    verdict, _ = gate_filesystem_boundary({
        "worktree_path": str(REPO),
    })
    assert verdict == "pass"


def test_expanded_gates_in_registry():
    for name in (
        "formatting", "lint", "typecheck", "unit", "integration",
        "secret_scan", "depwire_verify", "filesystem_boundary", "dependency_scan",
    ):
        assert name in GATE_REGISTRY


def test_run_all_gates_warns_not_fails_without_required(monkeypatch):
    monkeypatch.setattr("agentcore_workflow.gates._tool_available", lambda _cmd: False)
    # Avoid DB-backed gates blowing up
    state = {
        "project_id": "00000000-0000-0000-0000-000000000001",
        "project_key": "t",
        "thread_uuid": "t",
        "milestone_key": "M6",
        "macro_steps": [{"key": "M6.1", "label": "x", "ordinal": 1}],
        "micro_steps": [{"key": "M6.1.1", "label": "y", "ordinal": 1, "macro_key": "M6.1"}],
        "current_micro_key": "M6.1.1",
        "autonomous": False,
        "worktree_path": str(REPO),
    }
    results = run_all_gates(state, gates=[
        "requirement", "formatting", "lint", "depwire_verify", "secret_scan",
        "filesystem_boundary", "dependency_scan",
    ])
    assert results["requirement"][0] == "pass"
    assert results["formatting"][0] == "warn"
    assert results["lint"][0] == "warn"
    assert results["depwire_verify"][0] == "warn"
    assert results["filesystem_boundary"][0] == "pass"
