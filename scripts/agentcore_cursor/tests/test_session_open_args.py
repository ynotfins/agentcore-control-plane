"""Regression test: session_open requires 'project_key', not 'project_id'.

Root cause (2026-07-23): Phase 1 baseline audit called session_open with wrong
argument names (project_id, client_id, agent_role).  The server raises
KeyError('project_key') which propagates as the sanitized 'internal error'
response.  This test proves that (a) the wrong-args call raises KeyError and
(b) the correct-args call succeeds, verifying that the tools were never broken.

Run with:
    cd D:\\github\\agentcore-control-plane
    python -m pytest scripts/agentcore_cursor/tests/test_session_open_args.py -v
"""

from __future__ import annotations

import os
import sys
import unittest

_scripts = str(__import__("pathlib").Path(__file__).resolve().parents[2])
_memory = str(__import__("pathlib").Path(__file__).resolve().parents[2] / "agentcore_memory")
sys.path.insert(0, _scripts)
sys.path.insert(0, _memory)
import agentcore_memory.server as server  # noqa: E402


def _pw_available() -> bool:
    return bool(os.environ.get("AGENT_CORE_POSTGRES_PASSWORD"))


class TestSessionOpenArgNames(unittest.TestCase):
    @unittest.skipUnless(_pw_available(), "AGENT_CORE_POSTGRES_PASSWORD not set")
    def test_wrong_arg_name_raises_key_error(self) -> None:
        """Wrong arg 'project_id' raises KeyError before any DB call."""
        with self.assertRaises(KeyError) as ctx:
            server.session_open(
                {
                    "project_id": "agentcore-control-plane",  # WRONG — should be project_key
                    "client_id": "cursor",                    # WRONG — should be client_key
                    "agent_role": "cursor-composer",          # WRONG — should be agent_key
                }
            )
        self.assertEqual(ctx.exception.args[0], "project_key")

    @unittest.skipUnless(_pw_available(), "AGENT_CORE_POSTGRES_PASSWORD not set")
    def test_correct_arg_name_succeeds(self) -> None:
        """Correct arg 'project_key' opens a session successfully."""
        import subprocess
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(__import__("pathlib").Path(__file__).resolve().parents[3]),
            timeout=10,
        ).stdout.strip() or "unknown"

        result = server.session_open(
            {
                "project_key": "agentcore-control-plane",
                "client_key": "cursor-regression-test",
                "agent_key": "phase1b-regression-tester",
                "branch_name": "main",
                "head_commit": head,
            }
        )
        self.assertTrue(result.get("ok"), msg=f"session_open returned: {result}")
        self.assertIn("session_id", result)
        self.assertIn("session_key", result)


if __name__ == "__main__":
    unittest.main()
