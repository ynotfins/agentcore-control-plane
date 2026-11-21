from __future__ import annotations

import io
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from agentcore_cursor import hook_dispatcher, hooks


@pytest.fixture(autouse=True)
def _isolate_global_interlock(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        hooks, "GLOBAL_PROMPT_INTERLOCK_PATH", tmp_path / "global-interlock.json"
    )


def _write_bootstrap(root: Path, result: dict[str, object]) -> Path:
    subprocess.run(
        ["git", "init", "--quiet", str(root)],
        capture_output=True,
        check=True,
        text=True,
    )
    path = root / ".agentcore" / "runtime" / "cursor-bootstrap.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"result": result}), encoding="utf-8")
    return path


def test_before_submit_allows_prompt_when_recovered_session_is_unhealthy(tmp_path: Path) -> None:
    artifact = _write_bootstrap(
        tmp_path,
        {
            "ok": True,
            "session_id": "session-stale",
            "project_key": "project-stale",
            "continuity_status": "projection_stale",
            "status_flags": {
                "durable_backend_available": True,
                "project_automatically_resolved": True,
                "startup_context_completed": True,
                "current_prompt_captured_before_tools": True,
            },
        },
    )

    with patch.object(hooks, "append_prompt") as append_prompt:
        result = hooks.handle_before_submit(
            {
                "workspace_roots": [str(tmp_path)],
                "generation_id": "generation-new",
                "prompt": "continue working",
            }
        )

    persisted = json.loads(artifact.read_text(encoding="utf-8"))
    assert result["continue"] is True
    assert "projection_stale" in result["user_message"]
    assert append_prompt.call_count == 0
    assert persisted["result"]["status_flags"]["current_prompt_captured_before_tools"] is False
    assert "current_prompt_capture" not in persisted


def test_before_submit_allows_prompt_when_gateway_transport_is_refused(tmp_path: Path) -> None:
    rejected = SimpleNamespace(
        as_dict=lambda: {
            "ok": False,
            "project_key": tmp_path.name,
            "error": "URLError: <urlopen error [WinError 10061] connection refused>",
            "status_flags": {
                "durable_backend_available": False,
                "project_automatically_resolved": True,
                "startup_context_completed": False,
                "current_prompt_captured_before_tools": False,
            },
        }
    )

    with (
        patch.object(hooks, "load_bootstrap_json", return_value=None),
        patch.object(hooks, "run_bootstrap", return_value=rejected),
        patch.object(hooks, "append_prompt") as append_prompt,
        patch.object(hooks, "_set_prompt_capture_flag") as set_prompt_capture,
    ):
        result = hooks.handle_before_submit(
            {
                "workspace_roots": [str(tmp_path)],
                "generation_id": "generation-new",
                "prompt": "continue working",
            }
        )

    assert result["continue"] is True
    assert "WinError 10061" in result["user_message"]
    assert append_prompt.call_count == 0
    assert not any(call.kwargs.get("captured") is True for call in set_prompt_capture.call_args_list)


def test_malformed_before_submit_payload_fails_open() -> None:
    result = hook_dispatcher._dispatch(
        "beforeSubmitPrompt",
        {"_malformed_stdin": True, "_raw_len": 3, "_raw_preview": "len=3"},
    )

    assert result["continue"] is True
    assert "malformed" in result["user_message"].lower()
    assert any((hooks.GLOBAL_PROMPT_INTERLOCK_PATH / "unresolved").iterdir())


def test_before_submit_dispatcher_exception_fails_open() -> None:
    result = hook_dispatcher._controlled_error(
        "beforeSubmitPrompt", RuntimeError("synthetic dispatcher failure")
    )

    assert result["continue"] is True
    assert "synthetic dispatcher failure" in result["user_message"]
    assert any((hooks.GLOBAL_PROMPT_INTERLOCK_PATH / "unresolved").iterdir())


def test_dispatcher_main_emits_fail_open_response_when_handler_raises(monkeypatch) -> None:
    class _Stdin:
        buffer = io.BytesIO(b'{"prompt":"continue working"}')

    def _raise(_payload):
        raise RuntimeError("synthetic handler failure")

    output = io.StringIO()
    monkeypatch.setattr(sys, "stdin", _Stdin())
    monkeypatch.setattr(sys, "stdout", output)
    monkeypatch.setitem(hook_dispatcher.HANDLERS, "beforeSubmitPrompt", _raise)

    assert hook_dispatcher.main(["beforeSubmitPrompt"]) == 0
    result = json.loads(output.getvalue())
    assert result["continue"] is True
    assert result["agentcore_continuity_degraded"] is True
    assert "synthetic handler failure" in result["user_message"]


def test_pre_tool_write_denials_remain_fail_closed() -> None:
    missing_workspace = hooks.handle_pre_tool(
        {"tool_name": "write_file", "tool_input": {"path": "unsafe.txt"}}
    )
    dispatcher_error = hook_dispatcher._controlled_error(
        "preToolUse", RuntimeError("synthetic mutation failure")
    )

    assert missing_workspace["permission"] == "deny"
    assert dispatcher_error["permission"] == "deny"


def test_failed_disarm_cannot_reuse_previous_prompt_write_authority(tmp_path: Path) -> None:
    _write_bootstrap(
        tmp_path,
        {
            "ok": True,
            "session_id": "session-current",
            "session_key": "task-current",
            "project_key": "project-current",
            "continuity_status": "current",
            "status_flags": {
                "startup_context_completed": True,
                "current_prompt_captured_before_tools": True,
            },
        },
    )
    artifact = tmp_path / ".agentcore" / "runtime" / "cursor-bootstrap.json"
    data = json.loads(artifact.read_text(encoding="utf-8"))
    data["current_prompt_capture"] = {
        "event_id": "event-previous",
        "prompt_sha256": "a" * 64,
        "session_id": "session-current",
        "conversation_id": "conversation-current",
        "generation_id": "generation-previous",
    }
    artifact.write_text(json.dumps(data), encoding="utf-8")

    with (
        patch.object(hooks, "_set_prompt_capture_flag", return_value=False),
        patch.object(hooks, "_set_prompt_interlock", return_value=False),
        patch.object(hooks, "_set_prompt_interlock_failsafe", return_value=False),
    ):
        submit = hooks.handle_before_submit(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-current",
                "generation_id": "generation-new",
                "prompt": "new prompt",
            }
        )

    with patch.object(hooks, "GLOBAL_STATE_FILE", tmp_path / "GLOBAL_STATE.md"):
        mutation = hooks.handle_pre_tool(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-current",
                "generation_id": "generation-new",
                "tool_name": "write_file",
                "tool_input": {"path": str(tmp_path / "safe.txt")},
            }
        )

    assert submit["continue"] is True
    assert mutation["permission"] == "deny"
    assert "prompt" in mutation["user_message"].lower()


def test_unscoped_failure_cannot_be_cleared_by_another_project(tmp_path: Path) -> None:
    project_a = tmp_path / "project-a"
    project_b = tmp_path / "project-b"
    project_a.mkdir()
    project_b.mkdir()
    capture_a = {
        "event_id": "event-a",
        "session_id": "session-a",
        "conversation_id": "conversation-a",
        "generation_id": "generation-a",
    }

    assert hooks.set_global_prompt_interlock(
        blocked=False, root_path=project_a, **capture_a
    )
    assert hooks.set_global_prompt_interlock(
        blocked=True, unresolved_reason="malformed_before_submit_input"
    )
    assert hooks.set_global_prompt_interlock(blocked=True, root_path=project_b)
    assert hooks.set_global_prompt_interlock(
        blocked=False,
        root_path=project_b,
        event_id="event-b",
        session_id="session-b",
        conversation_id="conversation-b",
        generation_id="generation-b",
    )

    assert hooks._global_prompt_interlock_blocks(project_a, capture_a) is True


def test_all_persistence_writes_failing_cannot_reuse_prior_generation(tmp_path: Path) -> None:
    artifact = _write_bootstrap(
        tmp_path,
        {
            "ok": True,
            "session_id": "session-current",
            "session_key": "task-current",
            "project_key": "project-current",
            "continuity_status": "current",
            "status_flags": {
                "startup_context_completed": True,
                "current_prompt_captured_before_tools": True,
            },
        },
    )
    data = json.loads(artifact.read_text(encoding="utf-8"))
    data["current_prompt_capture"] = {
        "event_id": "event-previous",
        "prompt_sha256": "a" * 64,
        "session_id": "session-current",
        "conversation_id": "conversation-current",
        "generation_id": "generation-previous",
    }
    artifact.write_text(json.dumps(data), encoding="utf-8")

    with (
        patch.object(hooks, "_set_prompt_interlock", return_value=False),
        patch.object(hooks, "_set_prompt_interlock_failsafe", return_value=False),
        patch.object(hooks, "set_global_prompt_interlock", return_value=False),
        patch.object(hooks, "_set_prompt_capture_flag", return_value=False),
    ):
        submit = hooks.handle_before_submit(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-current",
                "generation_id": "generation-new",
                "prompt": "new prompt",
            }
        )

    with (
        patch.object(hooks, "_global_prompt_interlock_blocks", return_value=False),
        patch.object(hooks, "_prompt_interlock_blocks", return_value=False),
    ):
        mutation = hooks.handle_pre_tool(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-current",
                "generation_id": "generation-new",
                "tool_name": "write_file",
                "tool_input": {"path": str(tmp_path / "safe.txt")},
            }
        )

    persisted = json.loads(artifact.read_text(encoding="utf-8"))
    assert submit["continue"] is True
    assert persisted["result"]["status_flags"]["current_prompt_captured_before_tools"] is True
    assert mutation["permission"] == "deny"
    assert "session/turn" in mutation["user_message"]


def test_unpersisted_dispatch_failure_blocks_tool_and_shell_mutations(tmp_path: Path) -> None:
    _write_bootstrap(
        tmp_path,
        {
            "ok": True,
            "session_id": "session-current",
            "session_key": "task-current",
            "project_key": "project-current",
            "status_flags": {
                "startup_context_completed": True,
                "current_prompt_captured_before_tools": True,
            },
        },
    )
    artifact = tmp_path / ".agentcore" / "runtime" / "cursor-bootstrap.json"
    data = json.loads(artifact.read_text(encoding="utf-8"))
    data["current_prompt_capture"] = {
        "event_id": "event-previous",
        "prompt_sha256": "a" * 64,
        "session_id": "session-current",
        "conversation_id": "conversation-current",
    }
    artifact.write_text(json.dumps(data), encoding="utf-8")

    with patch.object(hook_dispatcher, "set_global_prompt_interlock", return_value=False):
        submit = hook_dispatcher._dispatch(
            "beforeSubmitPrompt", {"_malformed_stdin": True, "_raw_len": 2}
        )
    tool = hooks.handle_pre_tool(
        {
            "workspace_roots": [str(tmp_path)],
            "conversation_id": "conversation-current",
            "generation_id": "generation-new",
            "tool_name": "write_file",
            "tool_input": {"path": str(tmp_path / "safe.txt")},
        }
    )
    shell = hooks.handle_before_shell(
        {
            "workspace_roots": [str(tmp_path)],
            "conversation_id": "conversation-current",
            "generation_id": "generation-new",
            "command": "Set-Content safe.txt value",
        }
    )

    assert submit["continue"] is True
    assert tool["permission"] == "deny"
    assert shell["permission"] == "deny"


def test_rootless_prompt_creates_unresolved_latch_that_project_success_cannot_clear(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    capture = {
        "event_id": "event-old",
        "session_id": "session-old",
        "conversation_id": "conversation-old",
        "generation_id": "generation-old",
    }
    assert hooks.set_global_prompt_interlock(
        blocked=False, root_path=project, **capture
    )

    submit = hooks.handle_before_submit(
        {
            "conversation_id": "conversation-old",
            "generation_id": "generation-new",
            "prompt": "rootless prompt",
        }
    )
    assert hooks.set_global_prompt_interlock(blocked=True, root_path=project)
    assert hooks.set_global_prompt_interlock(
        blocked=False,
        root_path=project,
        event_id="event-new",
        session_id="session-new",
        conversation_id="conversation-old",
        generation_id="generation-new",
    )

    assert submit["continue"] is True
    assert hooks._global_prompt_interlock_blocks(project, capture) is True


def test_concurrent_project_and_unresolved_records_do_not_overwrite_each_other(
    tmp_path: Path,
) -> None:
    projects = [tmp_path / f"project-{index}" for index in range(8)]
    for project in projects:
        project.mkdir()

    with ThreadPoolExecutor(max_workers=9) as pool:
        project_futures = [
            pool.submit(
                hooks.set_global_prompt_interlock,
                blocked=True,
                root_path=project,
            )
            for project in projects
        ]
        unresolved_future = pool.submit(
            hooks.set_global_prompt_interlock,
            blocked=True,
            unresolved_reason="concurrent_unscoped_failure",
        )
        results = [future.result() for future in project_futures]
        unresolved = unresolved_future.result()

    assert all(results)
    assert unresolved is True
    assert len(list(hooks.GLOBAL_PROMPT_INTERLOCK_PATH.glob("*.json"))) == len(projects)
    assert any((hooks.GLOBAL_PROMPT_INTERLOCK_PATH / "unresolved").iterdir())


def test_release_failure_revokes_new_capture_and_reblocks_authorization(
    tmp_path: Path,
) -> None:
    artifact = _write_bootstrap(
        tmp_path,
        {
            "ok": True,
            "session_id": "session-current",
            "session_key": "task-current",
            "project_key": "project-current",
            "continuity_status": "current",
            "status_flags": {
                "durable_backend_available": True,
                "project_automatically_resolved": True,
                "startup_context_completed": True,
                "current_prompt_captured_before_tools": False,
            },
        },
    )

    def _failsafe(root_path: Path, *, blocked: bool, **kwargs) -> bool:
        if blocked:
            return hooks._set_prompt_interlock(root_path, blocked=True)
        return False

    with (
        patch.object(
            hooks, "append_prompt", return_value={"ok": True, "event_id": "event-new"}
        ),
        patch.object(hooks, "_set_prompt_interlock_failsafe", side_effect=_failsafe),
    ):
        result = hooks.handle_before_submit(
            {
                "workspace_roots": [str(tmp_path)],
                "conversation_id": "conversation-current",
                "generation_id": "generation-new",
                "prompt": "new prompt",
            }
        )

    persisted = json.loads(artifact.read_text(encoding="utf-8"))
    assert result["continue"] is True
    assert result["agentcore_continuity_degraded"] is True
    assert persisted["result"]["status_flags"]["current_prompt_captured_before_tools"] is False
    assert "current_prompt_capture" not in persisted
    assert hooks._global_prompt_interlock_blocks(tmp_path, None) is True
