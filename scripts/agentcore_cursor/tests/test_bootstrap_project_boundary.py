from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agentcore_cursor import bootstrap  # noqa: E402


class BootstrapProjectBoundaryTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
