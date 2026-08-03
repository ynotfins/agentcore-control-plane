from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from agentcore_cursor import hooks
from agentcore_cursor.session_scope import SessionScope


def _armed_workspace(root: Path, *, declared: list[Path] | None = None) -> None:
    subprocess.run(
        ["git", "init", "--quiet", str(root)],
        capture_output=True,
        check=True,
        text=True,
    )
    artifact = root / ".agentcore" / "runtime" / "cursor-bootstrap.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(
        json.dumps(
            {
                "result": {
                    "ok": True,
                    "session_id": "session-current",
                    "session_key": "task-current",
                    "project_key": "project-current",
                    "status_flags": {
                        "startup_context_completed": True,
                        "current_prompt_captured_before_tools": True,
                    },
                },
                "current_prompt_capture": {
                    "event_id": "event-current",
                    "prompt_sha256": "a" * 64,
                    "session_id": "session-current",
                    "conversation_id": "conversation-current",
                },
            }
        ),
        encoding="utf-8",
    )
    SessionScope(
        project_root=root,
        prompt_event_id="event-current",
        session_id="session-current",
        intent="secure mutation",
        acceptance=["authorized target only"],
        declared_files=[str(path.resolve()) for path in (declared or [])],
    ).save_atomic()


def test_before_submit_clears_stale_gate_before_append_failure(tmp_path: Path) -> None:
    _armed_workspace(tmp_path, declared=[tmp_path / "safe.txt"])
    with (
        patch.object(hooks, "append_prompt", return_value={"ok": False}),
        patch.object(hooks, "load_bootstrap_json", wraps=hooks.load_bootstrap_json),
    ):
        result = hooks.handle_before_submit(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-current",
                "prompt": "new prompt",
            }
        )
    artifact = json.loads(
        (tmp_path / ".agentcore" / "runtime" / "cursor-bootstrap.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["continue"] is False
    assert artifact["result"]["status_flags"]["current_prompt_captured_before_tools"] is False
    assert "current_prompt_capture" not in artifact


@pytest.mark.parametrize("append_result", [{"ok": True}, {"ok": True, "event_id": ""}])
def test_before_submit_requires_durable_event_id(
    tmp_path: Path, append_result: dict[str, object]
) -> None:
    _armed_workspace(tmp_path, declared=[tmp_path / "safe.txt"])
    with patch.object(hooks, "append_prompt", return_value=append_result):
        result = hooks.handle_before_submit(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-current",
                "prompt": "new prompt",
            }
        )
    assert result["continue"] is False


def test_apply_patch_checks_every_mutated_path(tmp_path: Path) -> None:
    safe = tmp_path / "safe.txt"
    undeclared = tmp_path / "undeclared.txt"
    _armed_workspace(tmp_path, declared=[safe])
    projection = tmp_path / "GLOBAL_STATE.md"
    projection.write_text("current", encoding="utf-8")
    with (
        patch.object(hooks, "GLOBAL_GENERATED_READ_ONLY", set()),
        patch.object(hooks, "GLOBAL_STATE_FILE", projection),
    ):
        result = hooks.handle_pre_tool(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-current",
                "tool_name": "ApplyPatch",
                "tool_input": {
                    "patch": (
                        "*** Begin Patch\n"
                        "*** Update File: safe.txt\n"
                        "*** Update File: undeclared.txt\n"
                        "*** End Patch\n"
                    )
                },
            }
        )
    assert result["permission"] == "deny"
    assert "not declared" in result["user_message"]
    assert str(undeclared.resolve()) in result["user_message"]


def test_move_tool_checks_source_and_destination(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination.txt"
    _armed_workspace(tmp_path, declared=[destination])
    projection = tmp_path / "GLOBAL_STATE.md"
    projection.write_text("current", encoding="utf-8")
    with (
        patch.object(hooks, "GLOBAL_GENERATED_READ_ONLY", set()),
        patch.object(hooks, "GLOBAL_STATE_FILE", projection),
    ):
        result = hooks.handle_pre_tool(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-current",
                "tool_name": "filesystem-move_file",
                "tool_input": {"source": str(source), "destination": str(destination)},
            }
        )
    assert result["permission"] == "deny"
    assert str(source.resolve()) in result["user_message"]


def test_governed_mutable_file_requires_authority_approval(tmp_path: Path) -> None:
    governed = tmp_path / "CONTEXT_BLOCK.md"
    _armed_workspace(tmp_path, declared=[governed])
    projection = tmp_path / "GLOBAL_STATE.md"
    projection.write_text("current", encoding="utf-8")
    manifest = Path(__file__).resolve().parents[3] / "contracts" / "authority-lock.yaml"
    with (
        patch.object(hooks, "AUTHORITY_LOCK_MANIFEST", manifest),
        patch.object(hooks, "GLOBAL_GENERATED_READ_ONLY", set()),
        patch.object(hooks, "GLOBAL_STATE_FILE", projection),
        patch.dict(
            "os.environ",
            {
                "AGENTCORE_AUTHORITY_CAPABILITY": "",
                "AGENTCORE_AUTHORITY_APPROVAL_ID": "",
            },
            clear=False,
        ),
    ):
        result = hooks.handle_pre_tool(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-current",
                "tool_name": "write_file",
                "tool_input": {"path": str(governed)},
            }
        )
    assert result["permission"] == "deny"
    assert "governed_mutable" in result["user_message"]


@pytest.mark.parametrize(
    "command",
    [
        "Get-Content source.txt | Tee-Object out.txt",
        "tee out.txt < source.txt",
        "sed -i s/old/new/ safe.txt",
        "python -c \"open('safe.txt','w').write('x')\"",
        "Set-Content $target value",
        "Set-Content $(Get-Location)\\safe.txt value",
    ],
)
def test_ambiguous_shell_mutation_forms_fail_closed(command: str, tmp_path: Path) -> None:
    _armed_workspace(tmp_path, declared=[tmp_path / "safe.txt"])
    result = hooks.handle_before_shell(
        {"workspace_roots": [str(tmp_path)], "command": command}
    )
    assert result["permission"] == "deny"


def test_remove_item_checks_every_positional_target(tmp_path: Path) -> None:
    _armed_workspace(tmp_path, declared=[tmp_path / "safe.txt"])
    result = hooks.handle_before_shell(
        {
            "workspace_roots": [str(tmp_path)],
            "command": "rm safe.txt undeclared.txt",
        }
    )
    assert result["permission"] == "deny"
    assert "undeclared" in result["user_message"]


def test_missing_workspace_denies_mutation_tool() -> None:
    result = hooks.handle_pre_tool(
        {"tool_name": "write_file", "tool_input": {"path": "safe.txt"}}
    )
    assert result["permission"] == "deny"


def test_missing_workspace_denies_mutating_shell() -> None:
    result = hooks.handle_before_shell({"command": "Set-Content safe.txt value"})
    assert result["permission"] == "deny"


def test_before_submit_bootstraps_when_runtime_artifact_is_absent(tmp_path: Path) -> None:
    subprocess.run(
        ["git", "init", "--quiet", str(tmp_path)],
        capture_output=True,
        check=True,
        text=True,
    )

    def _bootstrap(**_kwargs):
        artifact = tmp_path / ".agentcore" / "runtime" / "cursor-bootstrap.json"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        result = {
            "ok": True,
            "ambiguity": False,
            "session_id": "session-new",
            "session_key": "task-new",
            "project_key": "project-new",
            "status_flags": {"startup_context_completed": True},
        }
        artifact.write_text(json.dumps({"result": result}), encoding="utf-8")
        return SimpleNamespace(as_dict=lambda: result)

    with (
        patch.object(hooks, "run_bootstrap", side_effect=_bootstrap),
        patch.object(
            hooks, "append_prompt", return_value={"ok": True, "event_id": "event-new"}
        ),
    ):
        result = hooks.handle_before_submit(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-new",
                "prompt": "new prompt",
            }
        )

    assert result["continue"] is True
