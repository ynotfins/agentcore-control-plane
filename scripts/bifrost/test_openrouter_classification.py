"""Tests for OpenRouter four-tool classification and JIT VK bridge helpers."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "bifrost"))

import jit_vk_bridge as bridge  # noqa: E402


class OpenRouterClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = json.loads(
            (ROOT / "contracts" / "bifrost-upstream-mcp-registry.json").read_text(encoding="utf-8")
        )
        self.manifest = json.loads(
            (ROOT / "contracts" / "openrouter-tool-manifest.json").read_text(encoding="utf-8")
        )
        self.or_server = self.registry["servers"]["openrouter"]

    def test_four_tools_classified(self) -> None:
        permitted = set(self.or_server["permitted_tools"])
        denied = set(self.or_server["denied_tools"])
        self.assertIn("get-preset", permitted)
        self.assertIn("list-presets", permitted)
        self.assertIn("generate-speech", permitted)
        self.assertIn("transcribe-audio", permitted)
        self.assertIn("send-message", denied)
        self.assertIn("generate-image", denied)
        self.assertNotIn("send-message", permitted)
        self.assertNotIn("generate-image", permitted)

    def test_discovery_group_includes_presets_not_billable(self) -> None:
        g = self.or_server["tool_groups"]["openrouter-discovery-read"]["tools"]
        self.assertIn("get-preset", g)
        self.assertIn("list-presets", g)
        self.assertNotIn("send-message", g)
        self.assertNotIn("generate-image", g)
        self.assertNotIn("generate-speech", g)
        self.assertNotIn("transcribe-audio", g)
        self.assertEqual(len(g), 13)

    def test_media_and_transcription_groups(self) -> None:
        media = self.or_server["tool_groups"]["openrouter-media-generation"]
        tr = self.or_server["tool_groups"]["openrouter-transcription"]
        self.assertEqual(media["tools"], ["generate-speech"])
        self.assertEqual(media["access_policy"], "billable_approval")
        self.assertEqual(media.get("content_trust_class"), "raw_untrusted")
        self.assertEqual(tr["tools"], ["transcribe-audio"])
        self.assertEqual(tr["access_policy"], "billable_approval")
        self.assertEqual(tr.get("content_trust_class"), "raw_untrusted")
        self.assertIn("repository_files", tr.get("upload_policy", {}).get("forbid", []))

    def test_manifest_covers_twenty_live_tools(self) -> None:
        self.assertEqual(self.manifest["discovery"]["tool_count"], 20)
        self.assertEqual(len(self.manifest["tools"]), 20)
        self.assertTrue(self.manifest["no_wildcard_grants"])
        self.assertTrue(self.manifest["no_automatic_activation"])

    def test_load_tool_group_filters_denied(self) -> None:
        billable = bridge.load_tool_group("openrouter-billable")
        self.assertEqual(billable, [])  # denied filtered out
        discovery = bridge.load_tool_group("openrouter-discovery-read")
        self.assertIn("get-preset", discovery)
        self.assertEqual(len(discovery), 13)

    def test_openrouter_not_in_permanent_profiles(self) -> None:
        for pid, profile in self.registry["capability_profiles"].items():
            self.assertNotIn(
                "openrouter",
                profile.get("allowed_server_ids") or [],
                msg=f"profile {pid} must not permanently expose openrouter",
            )

    def test_status_remains_dormant(self) -> None:
        self.assertEqual(self.or_server.get("status"), "dormant")


class NodeToolPolicyTests(unittest.TestCase):
    def test_bootstrap_and_builder_policy(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from agentcore_workflow.node_tool_policy import tools_for_node, MEMORY_TOOLS

        boot = tools_for_node("bootstrap")
        self.assertTrue(any("session_open" in t for t in boot))
        self.assertTrue(any("startup_context" in t for t in boot))
        builder = tools_for_node("builder", jit_tools=("openrouter-list-models",))
        self.assertIn("openrouter-list-models", builder)
        self.assertEqual(len(MEMORY_TOOLS), 10)


if __name__ == "__main__":
    unittest.main()
