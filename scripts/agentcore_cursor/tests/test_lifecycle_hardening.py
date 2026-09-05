from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agentcore import cursor_cli  # noqa: E402
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
                "continuity_status": "current",
                "status_flags": {
                    "durable_backend_available": True,
                    "project_automatically_resolved": True,
                    "startup_context_completed": True,
                },
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

    def test_before_submit_cost_control_blocks_degraded_bootstrap(self) -> None:
        rejected = bootstrap.BootstrapResult(
            ok=False,
            project_key="agentcore-control-plane",
            project_root=r"D:\github\agentcore-control-plane",
            error="RuntimeError: BIFROST_MCP_VIRTUAL_KEY missing from process/User env",
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
        self.assertIn("cost-control gate blocked", result["user_message"])
        self.assertIn("agentcore-gateway/auth health", result["user_message"])

    def test_before_submit_cost_control_blocks_unhealthy_recovery(self) -> None:
        data = {
            "result": {
                "ok": True,
                "session_id": "session-test",
                "project_key": "agentcore-control-plane",
                "continuity_status": "projection_stale",
                "status_flags": {
                    "durable_backend_available": True,
                    "project_automatically_resolved": True,
                    "startup_context_completed": True,
                },
            }
        }
        with patch.object(hooks, "load_bootstrap_json", return_value=data):
            result = hooks.handle_before_submit(
                {
                    "workspace_roots": [r"D:\github\agentcore-control-plane"],
                    "prompt": "operator request",
                }
            )

        self.assertFalse(result["continue"])
        self.assertIn("projection_stale", result["user_message"])

    def test_before_submit_allows_healthy_unrelated_prompt(self) -> None:
        data = {
            "result": {
                "ok": True,
                "session_id": "session-test",
                "project_key": "agentcore-control-plane",
                "continuity_status": "current",
                "status_flags": {
                    "durable_backend_available": True,
                    "project_automatically_resolved": True,
                    "startup_context_completed": True,
                },
            }
        }
        with (
            patch.object(hooks, "load_bootstrap_json", return_value=data),
            patch.object(hooks, "append_prompt", return_value={"ok": True, "event_id": "event-test"}),
            patch.object(hooks, "_set_prompt_capture_flag", return_value=True),
        ):
            result = hooks.handle_before_submit(
                {
                    "workspace_roots": [r"D:\github\agentcore-control-plane"],
                    "prompt": "ordinary unrelated request",
                }
            )

        self.assertTrue(result["continue"])

    def test_before_submit_allows_unknown_continuity_when_health_flags_pass(self) -> None:
        data = {
            "result": {
                "ok": True,
                "session_id": "session-test",
                "project_key": "agentcore-control-plane",
                "continuity_status": "unknown",
                "status_flags": {
                    "durable_backend_available": True,
                    "project_automatically_resolved": True,
                    "startup_context_completed": True,
                },
            }
        }
        with (
            patch.object(hooks, "load_bootstrap_json", return_value=data),
            patch.object(hooks, "append_prompt", return_value={"ok": True, "event_id": "event-test"}),
            patch.object(hooks, "_set_prompt_capture_flag", return_value=True),
        ):
            result = hooks.handle_before_submit(
                {
                    "workspace_roots": [r"D:\github\agentcore-control-plane"],
                    "prompt": "ordinary request after successful recovery",
                }
            )

        self.assertTrue(result["continue"])

    def test_new_cursor_chat_gets_distinct_task_session_key(self) -> None:
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
        self.assertNotEqual(first.session_key, second.session_key)
        self.assertNotEqual(
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

    def test_run_bootstrap_accepts_explicit_project_bound_session_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gateway = _Gateway({"ok": True, "continuity_status": "current"})
            patches = self._bootstrap_patches(root, gateway)
            explicit = "agentcore-control-plane:cursor:cursor-composer:task:existing"
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                result = bootstrap.run_bootstrap(
                    workspace=str(root), session_key=explicit
                )

        self.assertTrue(result.ok)
        self.assertEqual(result.selection_mode, "resume_explicit")
        self.assertEqual(gateway.session_open_calls[0]["session_key"], explicit)

    def test_run_bootstrap_rejects_session_key_for_other_project_without_opening_gateway_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            gateway = _Gateway({"ok": True, "continuity_status": "current"})
            patches = self._bootstrap_patches(root, gateway)
            wrong = "other-project:cursor:cursor-composer:task:existing"
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
                result = bootstrap.run_bootstrap(
                    workspace=str(root), session_key=wrong
                )

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "session_key_not_bound_to_project")
        self.assertEqual(gateway.session_open_calls, [])

    def test_cursor_status_reads_bootstrap_without_global_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runtime = root / ".agentcore" / "runtime"
            runtime.mkdir(parents=True)
            bootstrap_data = {
                "result": {
                    "ok": True,
                    "session_key": "agentcore-control-plane:cursor:cursor-composer:task:existing",
                    "session_id": "session-existing",
                    "continuity_status": "current",
                },
                "generated_at": "2026-09-04T00:00:00+00:00",
            }
            (runtime / "cursor-bootstrap.json").write_text(
                json.dumps(bootstrap_data), encoding="utf-8"
            )
            scope = SessionScope(
                project_root=root,
                intent="test",
                acceptance=["done"],
                declared_files=[str(root / "a.txt"), str(root / "b.txt")],
            )
            scope.required_tool_evidence["tool_events"] = [
                {"tool_name": "read_file", "evidence": "ok"},
                {"tool_name": "write_file", "evidence": "ok"},
            ]
            scope.save_atomic()

            buf = io.StringIO()
            with (
                patch.object(bootstrap, "resolve_workspace", return_value=root),
                contextlib.redirect_stdout(buf),
            ):
                return_code = cursor_cli.cmd_status(
                    SimpleNamespace(workspace=str(root), json=True)
                )
            output = json.loads(buf.getvalue())

        self.assertEqual(return_code, 0)
        self.assertEqual(
            output["session_key"],
            "agentcore-control-plane:cursor:cursor-composer:task:existing",
        )
        self.assertEqual(output["session_id"], "session-existing")
        self.assertEqual(output["continuity_status"], "current")
        self.assertEqual(output["session_scope"]["declared_file_count"], 2)
        self.assertEqual(output["session_scope"]["tool_event_count"], 2)
        self.assertTrue(output["session_scope"]["intent_declared"])

    def test_cursor_resume_passes_explicit_session_key_to_bootstrap(self) -> None:
        explicit = "agentcore-control-plane:cursor:cursor-composer:task:existing"
        fake_result = bootstrap.BootstrapResult(
            ok=True,
            project_key="agentcore-control-plane",
            project_root=r"D:\github\agentcore-control-plane",
            session_key=explicit,
        )
        with patch.object(cursor_cli, "run_bootstrap", return_value=fake_result) as run_bootstrap:
            return_code = cursor_cli.cmd_resume(
                SimpleNamespace(
                    workspace=r"D:\github\agentcore-control-plane",
                    session_key=explicit,
                    agent_key=bootstrap.DEFAULT_AGENT_KEY,
                    json=True,
                )
            )

        self.assertEqual(return_code, 0)
        self.assertEqual(run_bootstrap.call_args.kwargs["session_key"], explicit)

    def test_cursor_cli_accepts_json_flag_before_or_after_subcommand(self) -> None:
        for argv in (
            ["--json", "status", "--workspace", r"D:\github\agentcore-control-plane"],
            ["status", "--workspace", r"D:\github\agentcore-control-plane", "--json"],
        ):
            with self.subTest(argv=argv):
                args = cursor_cli.build_parser().parse_args(argv)
                self.assertTrue(args.json)
                self.assertEqual(args.cmd, "status")


if __name__ == "__main__":
    unittest.main()
