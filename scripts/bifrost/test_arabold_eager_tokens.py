"""Unit tests for arabold eager-token measurement helpers (no live network)."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parent / "measure_arabold_eager_tokens.py"


def _load():
    spec = importlib.util.spec_from_file_location("measure_arabold_eager_tokens", HELPER)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestAraboldEagerTokenHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.m = _load()

    def test_is_arabold_tool_prefixes(self) -> None:
        self.assertTrue(self.m.is_arabold_tool("arabold_docs-search_docs"))
        self.assertTrue(self.m.is_arabold_tool("arabold-docs-find_version"))
        self.assertTrue(self.m.is_arabold_tool("search_docs"))
        self.assertFalse(self.m.is_arabold_tool("agentcore_memory-memory_status"))
        self.assertFalse(self.m.is_arabold_tool("listToolFiles"))

    def test_bounded_subset_filter(self) -> None:
        tools = [
            {"name": "arabold_docs-search_docs", "description": "s", "inputSchema": {}},
            {"name": "arabold_docs-remove_docs", "description": "r", "inputSchema": {}},
            {"name": "arabold_docs-scrape_docs", "description": "c", "inputSchema": {}},
        ]
        bounded = [
            t
            for t in tools
            if str(t["name"]).split("-", 1)[-1] in self.m.BOUNDED_SUBSET_SUFFIXES
        ]
        self.assertEqual(
            [t["name"] for t in bounded],
            ["arabold_docs-search_docs", "arabold_docs-scrape_docs"],
        )

    def test_decide_keeps_full_eager_for_modest_cost(self) -> None:
        before = {
            "compact_json": {"o200k_base": 1009},
            "tool_count": 10,
        }
        code_mode = {"compact_json": {"o200k_base": 0}, "tool_count": 0}
        bounded = {"compact_json": {"o200k_base": 639}, "tool_count": 5}
        total = {"compact_json": {"o200k_base": 7264}}
        decision = self.m.decide(before, code_mode, bounded, total)
        self.assertEqual(decision["recommendation"], "keep_full_eager")
        self.assertFalse(decision["apply_live"])


if __name__ == "__main__":
    unittest.main()
