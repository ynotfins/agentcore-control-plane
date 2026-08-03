from __future__ import annotations

import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agentcore_cursor import bootstrap  # noqa: E402
from agentcore_cursor import hooks  # noqa: E402


class BootstrapProjectBoundaryTests(unittest.TestCase):
    def test_ordinary_hook_bootstrap_has_no_global_runtime_or_database_mutation(self) -> None:
        hook_source = Path(hooks.__file__).read_text(encoding="utf-8")
        bootstrap_source = Path(bootstrap.__file__).read_text(encoding="utf-8")
        self.assertNotIn("_ensure_bifrost_gateway_running", hook_source)
        self.assertNotIn("AGENT_CORE_POSTGRES_PASSWORD", bootstrap_source)
        self.assertNotIn("active_task.json", bootstrap_source)

    def test_swarm_workspace_is_rejected_before_gateway_access(self) -> None:
        swarm_root = Path(r"D:\github\swarm-ecosystem-control")
        with (
            patch.object(bootstrap, "resolve_workspace", return_value=swarm_root),
            patch.object(bootstrap, "GatewayClient") as gateway,
            patch.object(bootstrap, "write_artifacts") as write_artifacts,
        ):
            result = bootstrap.run_bootstrap(workspace=str(swarm_root))

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "swarm_project_refused")
        gateway.assert_not_called()
        write_artifacts.assert_not_called()

    def test_unregistered_workspace_is_rejected_before_gateway_access(self) -> None:
        unregistered = Path(r"D:\github\renamed-foreign-repository")
        with (
            patch.object(bootstrap, "resolve_workspace", return_value=unregistered),
            patch.object(bootstrap, "GatewayClient") as gateway,
            patch.object(bootstrap, "write_artifacts") as write_artifacts,
        ):
            result = bootstrap.run_bootstrap(workspace=str(unregistered))

        self.assertFalse(result.ok)
        self.assertEqual(result.error, "project_not_enrolled")
        gateway.assert_not_called()
        write_artifacts.assert_not_called()

    def test_session_start_does_not_mutate_existing_rejected_workspace_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / ".agentcore" / "runtime" / "cursor-bootstrap.json"
            artifact.parent.mkdir(parents=True)
            original = {"result": {"status_flags": {"sentinel": True}}}
            artifact.write_text(json.dumps(original), encoding="utf-8")
            rejected = bootstrap.BootstrapResult(
                ok=False,
                project_key="swarm-ecosystem-control",
                project_root=str(root),
                error="swarm_project_refused",
            )
            with (
                patch.object(hooks, "_normalize_workspace_path", return_value=root),
                patch.object(hooks, "run_bootstrap", return_value=rejected),
            ):
                hooks.handle_session_start({"workspace_roots": [str(root)]})

            self.assertEqual(json.loads(artifact.read_text(encoding="utf-8")), original)

    def test_session_start_marks_the_exact_bootstrap_artifact_reported_by_bootstrap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reported = root / "custom-runtime" / "cursor-bootstrap.json"
            reported.parent.mkdir(parents=True)
            original = {"result": {"status_flags": {"prompt_captured": False}}}
            reported.write_text(json.dumps(original), encoding="utf-8")
            accepted = bootstrap.BootstrapResult(
                ok=True,
                project_key="agentcore-control-plane",
                project_root=str(root),
                bootstrap_path=str(reported),
            )
            with (
                patch.object(hooks, "_normalize_workspace_path", return_value=root),
                patch.object(hooks, "run_bootstrap", return_value=accepted),
            ):
                hooks.handle_session_start({"workspace_roots": [str(root)]})

            data = json.loads(reported.read_text(encoding="utf-8"))
            self.assertTrue(data["result"]["status_flags"]["startup_context_completed"])
            self.assertFalse(data["result"]["status_flags"]["prompt_captured"])


if __name__ == "__main__":
    unittest.main()
