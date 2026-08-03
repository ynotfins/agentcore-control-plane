from __future__ import annotations

import sys
from pathlib import Path

import pytest

MEMORY_ROOT = Path(__file__).resolve().parents[1]
if str(MEMORY_ROOT) not in sys.path:
    sys.path.insert(0, str(MEMORY_ROOT))

import server  # noqa: E402


@pytest.mark.parametrize(
    "field,value",
    [
        ("project_key", "swarm-ecosystem-control"),
        ("project_root", r"D:\github\swarm-ecosystem-control"),
        ("canonical_repo_path", r"H:\SwarmData\swarmclaw"),
        ("worktree_path", r"F:\AgentCore\agentmemory\swarmvault"),
    ],
)
def test_memory_rejects_swarm_project_identity(field: str, value: str) -> None:
    args = {
        "project_key": "safe-project",
        "project_root": r"D:\github\safe-project",
        "canonical_repo_path": r"D:\github\safe-project",
        "worktree_path": r"D:\github\safe-project",
    }
    args[field] = value

    with pytest.raises(ValueError, match="swarm_project_refused"):
        server.validate_project_boundary(args)


def test_memory_accepts_agentcore_project_identity() -> None:
    server.validate_project_boundary(
        {
            "project_key": "agentcore-control-plane",
            "project_root": r"D:\github\agentcore-control-plane",
            "canonical_repo_path": r"D:\github\agentcore-control-plane",
            "worktree_path": r"D:\github\agentcore-control-plane",
        }
    )


def test_memory_rejects_alias_key_on_enrolled_path() -> None:
    with pytest.raises(ValueError, match="project_identity_mismatch"):
        server.validate_project_boundary(
            {
                "project_key": "renamed-control-plane",
                "project_root": r"D:\github\agentcore-control-plane",
                "canonical_repo_path": r"D:\github\agentcore-control-plane",
                "worktree_path": r"D:\github\agentcore-control-plane",
            }
        )


def test_project_scoped_tools_require_enrolled_key() -> None:
    server.validate_tool_project_boundary(
        "retrieve_context",
        {
            "project_key": "agentcore-control-plane",
            "project_root": r"D:\github\agentcore-control-plane",
        },
    )
    with pytest.raises(ValueError, match="project_path_required"):
        server.validate_tool_project_boundary(
            "retrieve_context", {"project_key": "agentcore-control-plane"}
        )
    with pytest.raises(ValueError, match="project_not_enrolled"):
        server.validate_tool_project_boundary(
            "retrieve_context",
            {
                "project_key": "renamed-project",
                "project_root": r"D:\github\renamed-project",
            },
        )
    with pytest.raises(ValueError, match="project_scope_required"):
        server.validate_tool_project_boundary("docs_search", {"query": "test"})


def test_memory_rejects_unregistered_or_renamed_project() -> None:
    with pytest.raises(ValueError, match="project_not_enrolled"):
        server.validate_project_boundary(
            {
                "project_key": "renamed-project",
                "project_root": r"D:\github\renamed-project",
                "canonical_repo_path": r"D:\github\renamed-project",
                "worktree_path": r"D:\github\renamed-project",
            }
        )


def test_memory_rejects_mixed_enrolled_project_identity() -> None:
    with pytest.raises(ValueError, match="project_identity_mismatch"):
        server.validate_project_boundary(
            {
                "project_key": "mixed-project",
                "project_root": r"D:\github\agentcore-control-plane",
                "canonical_repo_path": r"D:\github\agentcore-context-engine",
            }
        )


def test_session_key_reuse_cannot_change_identity() -> None:
    existing = {
        "project_key": "agentcore-control-plane",
        "client_key": "cursor",
        "agent_key": "cursor-composer",
    }
    server._require_session_identity(
        existing,
        project_key="agentcore-control-plane",
        client_key="cursor",
        agent_key="cursor-composer",
    )
    with pytest.raises(ValueError, match="session_identity_mismatch"):
        server._require_session_identity(
            existing,
            project_key="agentcore-context-engine",
            client_key="cursor",
            agent_key="cursor-composer",
        )


def test_opaque_reference_must_match_requested_project() -> None:
    server._require_reference_project_identity(
        {"agentcore-control-plane"}, "agentcore-control-plane"
    )
    with pytest.raises(ValueError, match="project_identity_mismatch"):
        server._require_reference_project_identity(
            {"agentcore-control-plane", "agentcore-context-engine"},
            "agentcore-control-plane",
        )
