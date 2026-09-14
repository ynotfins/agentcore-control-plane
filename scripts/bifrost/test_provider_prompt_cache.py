"""Unit tests for scripts/bifrost/provider_prompt_cache.py.

No network calls. Verifies: deterministic stable prefix, correct per-provider
request fields, defensive usage extraction, the PASS rule, and that the
recorded policy never invents a live providers.*.prompt_cache field or a
static OpenRouter x-session-id.

Run: python scripts/bifrost/test_provider_prompt_cache.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO / "scripts" / "bifrost" / "provider_prompt_cache.py"


def load_module():
    spec = importlib.util.spec_from_file_location("provider_prompt_cache", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PPC = load_module()


class StablePrefixTests(unittest.TestCase):
    def test_system_prompt_deterministic(self) -> None:
        first = PPC.build_stable_system_prompt()
        second = PPC.build_stable_system_prompt()
        self.assertEqual(first, second)
        self.assertEqual(
            hashlib.sha256(first.encode("utf-8")).hexdigest(),
            hashlib.sha256(second.encode("utf-8")).hexdigest(),
        )

    def test_system_prompt_meets_minimum_length(self) -> None:
        text = PPC.build_stable_system_prompt()
        self.assertGreaterEqual(len(text), PPC.DEFAULT_MIN_PREFIX_CHARS)

    def test_system_prompt_no_dynamic_content(self) -> None:
        text = PPC.build_stable_system_prompt()
        # No timestamp-looking ISO date, no obvious secret markers.
        self.assertNotIn("T00:", text)
        self.assertNotRegex(text, r"\b202\d-\d{2}-\d{2}\b")
        self.assertNotIn("sk-", text)
        self.assertNotIn("Bearer ", text)

    def test_tools_are_deterministic_and_well_formed(self) -> None:
        first = PPC.build_stable_tools()
        second = PPC.build_stable_tools()
        self.assertEqual(first, second)
        names = {tool["function"]["name"] for tool in first}
        self.assertEqual(names, {"agentcore_cache_probe_lookup", "agentcore_cache_probe_status"})
        for tool in first:
            self.assertEqual(tool["type"], "function")
            self.assertIn("parameters", tool["function"])


class RequestBuilderTests(unittest.TestCase):
    def test_openai_request_has_retention_and_key_no_cache_control(self) -> None:
        body = PPC.build_chat_request(
            model="gpt-4o-mini",
            provider="openai",
            cache_key="agentcore-p1-openai",
            user_suffix="a",
        )
        self.assertEqual(body["model"], "gpt-4o-mini")
        self.assertEqual(body["prompt_cache_key"], "agentcore-p1-openai")
        self.assertEqual(body["prompt_cache_retention"], "in_memory")
        system = body["messages"][0]
        self.assertEqual(system["role"], "system")
        self.assertIsInstance(system["content"], str)  # plain string, no cache_control block

    def test_openrouter_request_has_cache_control_and_key_no_retention(self) -> None:
        body = PPC.build_chat_request(
            model="openrouter/openai/gpt-4o-mini",
            provider="openrouter",
            cache_key="agentcore-p1-openrouter",
            user_suffix="b",
        )
        self.assertEqual(body["prompt_cache_key"], "agentcore-p1-openrouter")
        self.assertNotIn("prompt_cache_retention", body)
        system = body["messages"][0]
        self.assertEqual(system["role"], "system")
        self.assertIsInstance(system["content"], list)
        block = system["content"][0]
        self.assertEqual(block["cache_control"], {"type": "ephemeral"})

    def test_same_prefix_different_suffix_across_two_calls(self) -> None:
        first = PPC.build_chat_request(
            model="gpt-4o-mini", provider="openai", cache_key="k", user_suffix="first"
        )
        second = PPC.build_chat_request(
            model="gpt-4o-mini", provider="openai", cache_key="k", user_suffix="second"
        )
        self.assertEqual(first["messages"][0], second["messages"][0])  # identical system prefix
        self.assertEqual(first["tools"], second["tools"])  # identical tools prefix
        self.assertNotEqual(first["messages"][1], second["messages"][1])  # differing user tail

    def test_unsupported_provider_raises(self) -> None:
        with self.assertRaises(ValueError):
            PPC.build_chat_request(
                model="x", provider="anthropic", cache_key="k", user_suffix="s"
            )


class UsageExtractionTests(unittest.TestCase):
    def test_extracts_cached_tokens_and_hash_cache_hit_false(self) -> None:
        payload = {
            "usage": {
                "prompt_tokens": 1500,
                "completion_tokens": 3,
                "prompt_tokens_details": {"cached_tokens": 1280, "cache_write_tokens": 0},
            },
            "extra_fields": {"cache_debug": {"cache_hit": False}},
            "choices": [{"message": {"content": "OK"}}],
        }
        evidence = PPC.extract_usage_evidence(payload)
        self.assertEqual(evidence["cached_tokens"], 1280)
        self.assertIsNone(evidence["cached_read_tokens"])
        self.assertEqual(evidence["hash_cache_hit"], False)
        self.assertTrue(evidence["has_choices"])
        self.assertNotIn("content", json.dumps(evidence))

    def test_extracts_alternate_cached_read_tokens_field(self) -> None:
        payload = {"usage": {"prompt_tokens": 1500, "cached_read_tokens": 1280}}
        evidence = PPC.extract_usage_evidence(payload)
        self.assertEqual(evidence["cached_read_tokens"], 1280)
        self.assertIsNone(evidence["cached_tokens"])

    def test_handles_missing_or_malformed_payload(self) -> None:
        for bad in (None, {}, {"usage": "not-a-dict"}, {"usage": {"prompt_tokens_details": None}}):
            evidence = PPC.extract_usage_evidence(bad)
            self.assertIsNone(evidence["cached_tokens"])
            self.assertIsNone(evidence["hash_cache_hit"])
            self.assertFalse(evidence["has_choices"])


class RoutePassesTests(unittest.TestCase):
    def test_passes_on_cached_tokens_without_hash_hit(self) -> None:
        evidence = {"cached_tokens": 1280, "cached_read_tokens": None, "hash_cache_hit": False}
        self.assertTrue(PPC.route_passes(evidence))

    def test_passes_on_cached_read_tokens_without_hash_hit(self) -> None:
        evidence = {"cached_tokens": None, "cached_read_tokens": 1280, "hash_cache_hit": None}
        self.assertTrue(PPC.route_passes(evidence))

    def test_fails_when_hash_cache_hit_is_true_even_with_tokens(self) -> None:
        evidence = {"cached_tokens": 1280, "cached_read_tokens": None, "hash_cache_hit": True}
        self.assertFalse(PPC.route_passes(evidence))

    def test_fails_when_no_cache_token_signal(self) -> None:
        evidence = {"cached_tokens": 0, "cached_read_tokens": None, "hash_cache_hit": False}
        self.assertFalse(PPC.route_passes(evidence))

    def test_fails_when_tokens_none(self) -> None:
        evidence = {"cached_tokens": None, "cached_read_tokens": None, "hash_cache_hit": False}
        self.assertFalse(PPC.route_passes(evidence))


class PolicyContentTests(unittest.TestCase):
    def test_policy_has_no_secret_like_strings(self) -> None:
        blob = json.dumps(PPC.agentcore_meta_policy())
        for forbidden in ("sk-", "sk-or-v1-", "Bearer "):
            self.assertNotIn(forbidden, blob)
        # A bare prose mention of the anti-goal ("No static OpenRouter
        # x-session-id") is fine; an actual injected header/value is not.
        self.assertNotIn('"x-session-id":', blob)
        self.assertIn("No static OpenRouter x-session-id", blob)

    def test_policy_documents_both_routes_and_pass_rule(self) -> None:
        policy = PPC.agentcore_meta_policy()
        self.assertIn("openai_direct", policy["routes"])
        self.assertIn("openrouter_openai", policy["routes"])
        self.assertIn("pass_rule", policy)
        self.assertIn("non_goals", policy)

    def test_policy_does_not_claim_live_provider_toggle(self) -> None:
        policy = PPC.agentcore_meta_policy()
        blob = json.dumps(policy)
        self.assertIn("no provider-level prompt-cache toggle", policy["note"])
        self.assertNotIn('"prompt_cache":', blob)


if __name__ == "__main__":
    unittest.main()
