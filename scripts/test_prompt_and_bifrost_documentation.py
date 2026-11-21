from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class PromptAndBifrostDocumentationTests(unittest.TestCase):
    def test_canonical_policy_keeps_prompts_open_and_mutations_closed(self) -> None:
        policy = read("contracts/global-agent-policy.yaml")
        required = (
            "beforeSubmitPrompt must always return continue=true",
            "workspace resolution, gateway, memory, continuity",
            "malformed input, or dispatcher work fails",
            "revokes authorization inherited from the prior turn",
            "Write-capable tools and",
            "mutating or ambiguous shell commands fail closed",
            "current workspace, session, conversation, and generation_id",
            "Read-only tools and shell commands",
        )
        for phrase in required:
            self.assertIn(phrase, policy)

    def test_cursor_recovery_runbook_explains_the_interlock(self) -> None:
        runbook = read("docs/operations/AUTOMATIC_NEW_CHAT_RECOVERY.md")
        for phrase in (
            "Always `continue: true`",
            "must never stop",
            "workspace root",
            "session id",
            "conversation id",
            "`generation_id`",
            "write-capable tools",
            "mutating or ambiguously classified shell commands",
            "read-only tools and commands remain usable",
        ):
            self.assertIn(phrase, runbook)
        self.assertNotIn("Prompt capture spools", runbook)
        self.assertIn("Failed prompt capture is not currently spooled", runbook)

    def test_bifrost_docs_match_lifecycle_and_proxy_behavior(self) -> None:
        documents = (
            "GATEWAY_AND_BIFROST_DEVELOPER_GUIDE.md",
            "docs/bifrost/BIFROST_OPERATOR_RUNBOOK.md",
            "docs/bifrost/UNIFIED_GATEWAY_SETUP.md",
        )
        for relative in documents:
            with self.subTest(document=relative):
                text = read(relative)
                normalized = " ".join(text.split())
                for phrase in (
                    "AtLogOn",
                    "Interactive",
                    "Limited",
                    "two consecutive failed probes",
                    "60-second",
                    "maintenance marker",
                    "BUILDER_COMPAT_PROXY_DEGRADED",
                    ":18082",
                    ":8080",
                ):
                    self.assertIn(phrase, normalized)
                self.assertRegex(normalized, r"120(?:-second| seconds)")
                self.assertIn("pre-login", normalized)
                self.assertRegex(normalized, r"(?i)(?:does not guarantee|not guaranteed)")

    def test_rendered_ide_rules_inherit_prompt_and_mutation_policy(self) -> None:
        rendered = sorted((ROOT / "ide-profiles").glob("*/GLOBAL_RULES.md"))
        self.assertTrue(rendered)
        for path in rendered:
            with self.subTest(profile=path.parent.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("beforeSubmitPrompt must always return continue=true", text)
                self.assertIn("mutating or ambiguous shell commands fail closed", text)
                self.assertIn("current workspace, session, conversation, and generation_id", text)


if __name__ == "__main__":
    unittest.main()
