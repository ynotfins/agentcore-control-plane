from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO / "contracts" / "bifrost-upstream-mcp-registry.json"
REGISTRY_SCHEMA_PATH = REPO / "contracts" / "schemas" / "bifrost-upstream-mcp-registry.schema.json"
OUTPUT_SCHEMA_PATH = REPO / "contracts" / "mcp-tool-output-schemas.json"
PACKAGE_PATH = REPO / "tools" / "research-mcp" / "package.json"
LOCK_PATH = REPO / "tools" / "research-mcp" / "package-lock.json"

ACTIVE = {
    "apify-research": {
        "version": "0.15.4",
        "package": "@apify/actors-mcp-server",
        "env": [],
        "tools": [
            "search-actors",
            "fetch-actor-details",
            "call-actor",
            "search-apify-docs",
            "fetch-apify-docs",
        ],
    },
    "exa-research": {
        "version": "3.4.1",
        "package": "exa-mcp-server",
        "env": ["EXA_API_KEY"],
        "tools": ["web_search_exa", "web_fetch_exa"],
    },
    "firecrawl-research": {
        "version": "3.24.0",
        "package": "firecrawl-mcp",
        "env": ["FIRECRAWL_API_KEY"],
        "tools": [
            "firecrawl_search",
            "firecrawl_scrape",
            "firecrawl_map",
            "firecrawl_research_search_papers",
            "firecrawl_research_inspect_paper",
            "firecrawl_research_related_papers",
            "firecrawl_research_read_paper",
            "firecrawl_research_search_github",
        ],
    },
    "tavily-research": {
        "version": "0.2.22",
        "package": "tavily-mcp",
        "env": ["TAVILY_API_KEY"],
        "tools": [
            "tavily_search",
            "tavily_extract",
            "tavily_crawl",
            "tavily_map",
            "tavily_research",
        ],
    },
}


class ResearchMcpContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.registry_schema = json.loads(REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.output_schema = json.loads(OUTPUT_SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))
        cls.lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))

    def test_registry_schema_defines_secret_safe_env_aliases(self) -> None:
        aliases = self.registry_schema["$defs"]["upstream_server"]["properties"]["env_aliases"]
        self.assertEqual("object", aliases["type"])
        self.assertEqual("^[A-Z][A-Z0-9_]*$", aliases["propertyNames"]["pattern"])
        self.assertEqual("^[A-Z][A-Z0-9_]*$", aliases["additionalProperties"]["pattern"])

    def test_exact_package_lock(self) -> None:
        self.assertEqual(3, self.lock["lockfileVersion"])
        self.assertEqual(
            {spec["package"] for spec in ACTIVE.values()},
            set(self.package["dependencies"]),
        )
        for spec in ACTIVE.values():
            name = spec["package"]
            self.assertEqual(spec["version"], self.package["dependencies"][name])
            locked = self.lock["packages"][f"node_modules/{name}"]
            self.assertEqual(spec["version"], locked["version"])
            self.assertTrue(locked["integrity"].startswith("sha512-"))
        self.assertNotIn("@brightdata/mcp", self.package["dependencies"])
        self.assertNotIn("node_modules/@brightdata/mcp", self.lock["packages"])

    def test_active_servers_are_builder_only_code_mode_with_exact_tools(self) -> None:
        builder = self.registry["capability_profiles"]["builder"]["allowed_server_ids"]
        for server_id, spec in ACTIVE.items():
            server = self.registry["servers"][server_id]
            self.assertTrue(server["enabled"])
            self.assertEqual("active", server["status"])
            self.assertTrue(server["is_code_mode_client"])
            self.assertEqual(["builder"], server["capability_profiles"])
            self.assertEqual(spec["version"], server["pinned_version"])
            self.assertEqual(spec["env"], server["env_var_names"])
            self.assertEqual(spec["tools"], server["permitted_tools"])
            self.assertNotIn("*", server["permitted_tools"])
            self.assertIn(server_id, builder)
            for profile_id, profile in self.registry["capability_profiles"].items():
                if profile_id != "builder":
                    self.assertNotIn(server_id, profile["allowed_server_ids"])

    def test_apify_alias_and_injected_helpers_fail_closed(self) -> None:
        server = self.registry["servers"]["apify-research"]
        self.assertEqual({"APIFY_TOKEN": "APIFY_API_KEY"}, server["env_aliases"])
        self.assertEqual(
            "search-actors,fetch-actor-details,call-actor,search-apify-docs,fetch-apify-docs",
            server["arguments"][2],
        )
        self.assertIn("--telemetry-enabled=false", server["arguments"])
        self.assertIn("--ui=default", server["arguments"])
        self.assertTrue(set(server["denied_tools"]).isdisjoint(server["permitted_tools"]))
        self.assertEqual(
            {
                "get-actor-run",
                "get-dataset-items",
                "get-key-value-store-record",
                "abort-actor-run",
            },
            set(server["denied_tools"]),
        )

    def test_brightdata_is_catalogued_but_uninstalled_and_profileless(self) -> None:
        server = self.registry["servers"]["brightdata-research"]
        self.assertFalse(server["enabled"])
        self.assertEqual("catalogued_unverified", server["status"])
        self.assertEqual([], server["permitted_tools"])
        self.assertEqual([], server["capability_profiles"])
        self.assertEqual({"API_TOKEN": "BRIGHTDATA_API_KEY"}, server["env_aliases"])
        for profile in self.registry["capability_profiles"].values():
            self.assertNotIn("brightdata-research", profile["allowed_server_ids"])

    def test_output_schema_family_is_external(self) -> None:
        for server_id in [*ACTIVE, "brightdata-research"]:
            wiring = self.output_schema["servers"][server_id]
            self.assertEqual("stdio_envelope", wiring["adapter"])
            self.assertEqual("external", wiring["default_profile"])


if __name__ == "__main__":
    unittest.main()
