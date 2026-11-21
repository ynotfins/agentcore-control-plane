from __future__ import annotations

import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[2]
RENDERER_PATH = REPO / "scripts" / "bifrost" / "render_bifrost_config.py"
REGISTRY_PATH = REPO / "contracts" / "bifrost-upstream-mcp-registry.json"
GATEWAY_PATH = REPO / "contracts" / "agentcore-gateway-client.json"


def load_renderer():
    spec = importlib.util.spec_from_file_location("research_mcp_renderer", RENDERER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ResearchMcpRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.renderer = load_renderer()
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.gateway = json.loads(GATEWAY_PATH.read_text(encoding="utf-8"))

    def test_alias_is_name_only_and_secret_never_enters_argv(self) -> None:
        secret = "test-secret-value-that-must-never-render"
        wiring = self.renderer.OutputSchemaWiring(self.registry)
        with patch.dict(os.environ, {"APIFY_API_KEY": secret}, clear=False):
            client = self.renderer.build_stdio_client(
                self.registry["servers"]["apify-research"],
                self.registry["authority"],
                wiring,
            )
        serialized = json.dumps(client)
        self.assertNotIn(secret, serialized)
        args = client["stdio_config"]["args"]
        alias_index = args.index("--alias-env")
        self.assertEqual("APIFY_TOKEN=APIFY_API_KEY", args[alias_index + 1])
        self.assertNotIn("--allow-env", args)

    def test_exa_telemetry_is_disabled_without_a_secret_value(self) -> None:
        wiring = self.renderer.OutputSchemaWiring(self.registry)
        client = self.renderer.build_stdio_client(
            self.registry["servers"]["exa-research"],
            self.registry["authority"],
            wiring,
        )
        args = client["stdio_config"]["args"]
        static_index = args.index("--static-env")
        self.assertEqual("AGNOST_DISABLE_LOGS=true", args[static_index + 1])

    def test_active_research_servers_render_code_mode_and_named_tools(self) -> None:
        config = self.renderer.build_bifrost_config(self.registry, self.gateway)
        clients = {client["name"]: client for client in config["mcp"]["client_configs"]}
        for name in ("apify_research", "exa_research", "firecrawl_research", "tavily_research"):
            client = clients[name]
            self.assertTrue(client["is_code_mode_client"])
            self.assertNotIn("*", client["tools_to_execute"])
            self.assertNotIn("tools_to_auto_execute", client)
        self.assertNotIn("brightdata_research", clients)

    def test_builder_vk_grants_research_clients_only(self) -> None:
        config = self.renderer.build_bifrost_config(self.registry, self.gateway)
        virtual_keys = {key["name"]: key for key in config["governance"]["virtual_keys"]}
        expected = {"apify_research", "exa_research", "firecrawl_research", "tavily_research"}
        builder = {item["mcp_client_name"] for item in virtual_keys["builder"]["mcp_configs"]}
        self.assertTrue(expected.issubset(builder))
        for profile_name, key in virtual_keys.items():
            if profile_name != "builder":
                actual = {item["mcp_client_name"] for item in key["mcp_configs"]}
                self.assertTrue(expected.isdisjoint(actual))


if __name__ == "__main__":
    unittest.main()
