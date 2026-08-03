from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agentcore_cursor import bootstrap, hooks  # noqa: E402
from agentcore_cursor.session_scope import SessionScope  # noqa: E402


class _Gateway:
    def __init__(self, startup: dict[str, object]) -> None:
        self.startup = startup
        self.session_open_calls: list[dict[str, object]] = []

    def call_tool(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        if name == "agentcore_memory-memory_status":
            return {"ok": True}
        if name == "agentcore_memory-session_open":
            self.session_open_calls.append(dict(arguments))
            return {
                "ok": True,
                "session_id": f"session-{len(self.session_open_calls)}",
                "session_key": arguments["session_key"],
            }
        if name == "agentcore_memory-startup_context":
            return dict(self.startup)
        raise AssertionError(f"unexpected tool: {name}")


class CursorLifecycleHardeningTests(unittest.TestCase):
    def _bootstrap_patches(self, root: Path, gateway: _Gateway):
        return (
            patch.object(bootstrap, "resolve_workspace", return_value=root),
            patch.object(bootstrap, "validate_workspace_enrollment"),
            patch.object(bootstrap, "resolve_project_key", return_value="agentcore-control-plane"),
            patch.object(bootstrap, "GatewayClient", return_value=gateway),
            patch.object(bootstrap, "read_projections", return_value={}),
            patch.object(bootstrap, "_git", return_value="main"),
        )

    def test_bootstrap_fails_closed_when_startup_context_returns_not_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gateway = _Gateway({"ok": False, "error": "memory_unavailable"})
            patches = self._bootstrap_patches(root, gateway)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                result = bootstrap.run_bootstrap(workspace=str(root))

        self.assertFalse(result.ok)
        self.assertFalse(result.status_flags["startup_context_automatically_injected"])

    def test_before_submit_blocks_when_bootstrap_is_not_healthy(self) -> None:
        rejected = bootstrap.BootstrapResult(
            ok=False,
            project_key="agentcore-control-plane",
            project_root=r"D:\github\agentcore-control-plane",
            error="startup_context failed",
        )
        with (
            patch.object(hooks, "load_bootstrap_json", return_value=None),
            patch.object(hooks, "run_bootstrap", return_value=rejected),
        ):
            result = hooks.handle_before_submit(
                {
                    "workspace_roots": [r"D:\github\agentcore-control-plane"],
                    "prompt": "operator request",
                }
            )

        self.assertFalse(result["continue"])

    def test_before_submit_blocks_when_prompt_gate_artifact_cannot_be_updated(self) -> None:
        data = {
            "result": {
                "ok": True,
                "session_id": "session-test",
                "project_key": "agentcore-control-plane",
            }
        }
        with (
            patch.object(hooks, "load_bootstrap_json", return_value=data),
            patch.object(hooks, "append_prompt", return_value={"ok": True, "event_id": "event-test"}),
            patch.object(hooks, "_set_prompt_capture_flag", return_value=False),
        ):
            result = hooks.handle_before_submit(
                {
                    "workspace_roots": [r"D:\github\agentcore-control-plane"],
                    "prompt": "operator request",
                }
            )

        self.assertFalse(result["continue"])

    def test_new_cursor_chat_reuses_project_task_session_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gateway = _Gateway({"ok": True, "continuity_status": "current"})
            patches = self._bootstrap_patches(root, gateway)
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                first = bootstrap.run_bootstrap(
                    workspace=str(root), cursor_conversation_id="chat-one"
                )
                second = bootstrap.run_bootstrap(
                    workspace=str(root), cursor_conversation_id="chat-two"
                )

        self.assertTrue(first.ok)
        self.assertTrue(second.ok)
        self.assertEqual(first.session_key, second.session_key)
        self.assertEqual(
            gateway.session_open_calls[0]["session_key"],
            gateway.session_open_calls[1]["session_key"],
        )

    def test_stop_resets_prompt_capture_after_successful_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / ".agentcore" / "runtime" / "cursor-bootstrap.json"
            artifact.parent.mkdir(parents=True)
            artifact.write_text(
                json.dumps(
                    {
                        "result": {
                            "ok": True,
                            "status_flags": {
                                "current_prompt_captured_before_tools": True,
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            scope = SessionScope(
                project_root=root,
                intent="test",
                acceptance=["done"],
                declared_files=[str(root / "declared.txt")],
            )
            scope.save_atomic()
            with (
                patch.object(hooks, "_normalize_workspace_path", return_value=root),
                patch.object(hooks, "_append_durable_hook_event", return_value={"ok": True}),
                patch.object(hooks, "_build_durable_handoff", return_value={"ok": True}),
            ):
                result = hooks.handle_stop({"workspace_roots": [str(root)]})

            data = json.loads(artifact.read_text(encoding="utf-8"))

        self.assertEqual(result, {})
        self.assertFalse(
            data["result"]["status_flags"]["current_prompt_captured_before_tools"]
        )

    def test_shell_file_write_uses_the_same_prompt_gate_as_mcp_writes(self) -> None:
        denied = {
            "permission": "deny",
            "user_message": "AgentCore Stage B Deny: current operator prompt is not durably captured",
        }
        with patch.object(hooks, "handle_pre_tool", return_value=denied) as pre_tool:
            result = hooks.handle_before_shell(
                {
                    "workspace_roots": [r"D:\github\agentcore-control-plane"],
                    "command": r"Set-Content D:\github\agentcore-control-plane\x.txt value",
                }
            )

        self.assertEqual(result, denied)
        self.assertEqual(pre_tool.call_args.args[0]["tool_name"], "write_file")

    def test_shell_file_write_uses_the_same_declared_file_gate(self) -> None:
        denied = {
            "permission": "deny",
            "user_message": "AgentCore Stage B Deny: target not declared in session-scope.json",
        }
        with patch.object(hooks, "handle_pre_tool", return_value=denied) as pre_tool:
            result = hooks.handle_before_shell(
                {
                    "workspace_roots": [r"D:\github\agentcore-control-plane"],
                    "command": r"Set-Content D:\github\agentcore-control-plane\undeclared.txt value",
                }
            )

        self.assertEqual(result, denied)
        self.assertTrue(pre_tool.call_args.args[0]["tool_input"]["path"].endswith("undeclared.txt"))

    def test_compound_shell_file_mutation_is_denied_when_all_targets_cannot_be_gated(self) -> None:
        with patch.object(hooks, "handle_pre_tool", return_value={"permission": "allow"}):
            result = hooks.handle_before_shell(
                {
                    "workspace_roots": [r"D:\github\agentcore-control-plane"],
                    "command": "Set-Content first.txt one; Set-Content second.txt two",
                }
            )

        self.assertEqual(result["permission"], "deny")
        self.assertIn("not safely resolvable", result["user_message"])

    def test_shell_mutation_parser_skips_known_option_values(self) -> None:
        is_mutation, targets = hooks._shell_file_mutation_targets(
            "Set-Content -Encoding utf8 out.txt data"
        )

        self.assertTrue(is_mutation)
        self.assertEqual(targets, ["out.txt"])

    def test_shell_mutation_parser_denies_unknown_switch(self) -> None:
        is_mutation, targets = hooks._shell_file_mutation_targets(
            "Set-Content -Unknown value out.txt data"
        )

        self.assertTrue(is_mutation)
        self.assertIsNone(targets)

    def test_compound_redirect_is_not_treated_as_one_safe_target(self) -> None:
        is_mutation, targets = hooks._shell_file_mutation_targets(
            "echo first > first.txt; echo second > second.txt"
        )

        self.assertTrue(is_mutation)
        self.assertIsNone(targets)

    def test_multiple_redirects_return_every_file_target(self) -> None:
        is_mutation, targets = hooks._shell_file_mutation_targets(
            "echo first > first.txt 2> errors.txt"
        )

        self.assertTrue(is_mutation)
        self.assertEqual(targets, ["first.txt", "errors.txt"])

    def test_piped_file_mutation_is_not_treated_as_one_safe_target(self) -> None:
        is_mutation, targets = hooks._shell_file_mutation_targets(
            "Get-Content source.txt | Set-Content destination.txt"
        )

        self.assertTrue(is_mutation)
        self.assertIsNone(targets)

    def test_common_shell_aliases_are_file_mutators(self) -> None:
        for command in ("rm file.txt", "del file.txt", "erase file.txt", "ri file.txt", "ni file.txt", "sc file.txt data"):
            with self.subTest(command=command):
                is_mutation, targets = hooks._shell_file_mutation_targets(command)
                self.assertTrue(is_mutation)
                self.assertEqual(targets, ["file.txt"])

    def test_move_copy_and_rename_preserve_source_and_destination(self) -> None:
        for command in (
            "mv source.txt destination.txt",
            "move source.txt destination.txt",
            "cp source.txt destination.txt",
            "copy source.txt destination.txt",
            "ren source.txt destination.txt",
        ):
            with self.subTest(command=command):
                is_mutation, targets = hooks._shell_file_mutation_targets(command)
                self.assertTrue(is_mutation)
                self.assertEqual(targets, ["source.txt", "destination.txt"])

    def test_move_checks_protected_source_before_safe_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            protected = root / "PROJECT_ANCHOR.md"
            protected.write_text("locked", encoding="utf-8")

            def gate(payload):
                path = Path(payload["tool_input"]["path"])
                if hooks._authority_path_class(root, path) == "operator_locked":
                    return {"permission": "deny", "user_message": "operator locked"}
                return {"permission": "allow"}

            with patch.object(hooks, "handle_pre_tool", side_effect=gate) as pre_tool:
                result = hooks.handle_before_shell(
                    {
                        "workspace_roots": [str(root)],
                        "command": "mv PROJECT_ANCHOR.md safe.txt",
                    }
                )

        self.assertEqual(result["permission"], "deny")
        self.assertEqual(pre_tool.call_count, 1)

    def test_wildcard_delete_expands_before_authority_classification(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "PROJECT_ANCHOR.md").write_text("locked", encoding="utf-8")
            (root / "ordinary.md").write_text("ordinary", encoding="utf-8")

            def gate(payload):
                path = Path(payload["tool_input"]["path"])
                if hooks._authority_path_class(root, path) == "operator_locked":
                    return {"permission": "deny", "user_message": "operator locked"}
                return {"permission": "allow"}

            with patch.object(hooks, "handle_pre_tool", side_effect=gate):
                result = hooks.handle_before_shell(
                    {"workspace_roots": [str(root)], "command": "rm *.md"}
                )

        self.assertEqual(result["permission"], "deny")


if __name__ == "__main__":
    unittest.main()
