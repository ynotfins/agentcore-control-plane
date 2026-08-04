"""Validate the canonical AgentCore lifecycle skill and every delivery adapter."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "agentcore-project-lifecycle"
SKILL = SKILL_ROOT / "SKILL.md"
MANIFEST = REPO_ROOT / "contracts" / "agentcore-alignment-skill-hosts.json"
CATALOG = REPO_ROOT / "contracts" / "context-engine-execution-catalog.json"
REQUIRED_REFERENCES = {
    "references/TOOL_ROUTING.md",
    "references/MEMORY_AND_STATE.md",
    "references/HOST_AND_RUNTIME_ADAPTERS.md",
    "references/PROJECT_GATES.md",
}
REQUIRED_SKILL_TERMS = {
    "agentcore-gateway",
    "agentcore-memory",
    "swarm_project_refused",
    "sequential-thinking",
    "arabold-docs",
    "Serena",
    "Depwire",
    "Tentra",
    "Context Fabric",
    "STATE.md",
    "PostgreSQL 18",
    "SwarmClaw",
}
APPROVED_TARGETS = {
    "cursor": r"{userprofile}\.cursor\skills\agentcore-project-lifecycle",
    "codex": r"{userprofile}\.agents\skills\agentcore-project-lifecycle",
    "claude-code": r"{userprofile}\.claude\skills\agentcore-project-lifecycle",
    "minimax": r"{userprofile}\.minimax\skills\agentcore-project-lifecycle",
    "mavis": r"{userprofile}\.mavis\skills\agentcore-project-lifecycle",
}
FORBIDDEN_PATTERNS = {
    r"Document architectural decisions in `?\.agentcore/DECISIONS\.md": "direct projection edit",
    r"project_activate": "ordinary machine-global router activation",
    r"raw SwarmRecall MCP": "raw Recall route",
    r"(?:edit|write|patch|update) (?:the )?(?:generated )?`?\.agentcore/(?:STATE|DECISIONS|CONTEXT_INDEX)\.md": "direct generated projection mutation",
    r"enable (?:the )?shared (?:Bifrost )?Serena": "shared implicit-project Serena enablement",
}


def skill_sha256() -> str:
    return hashlib.sha256(SKILL.read_bytes()).hexdigest()


def parse_frontmatter(text: str) -> dict:
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not match:
        raise AssertionError("SKILL.md frontmatter missing")
    metadata = yaml.safe_load(match.group(1))
    if set(metadata) != {"name", "description"}:
        raise AssertionError(f"frontmatter keys must be name+description only: {sorted(metadata)}")
    return metadata


def main() -> int:
    text = SKILL.read_text(encoding="utf-8")
    metadata = parse_frontmatter(text)
    assert metadata["name"] == "agentcore-project-lifecycle"
    assert 1 <= len(metadata["description"]) <= 1024

    missing_terms = sorted(term for term in REQUIRED_SKILL_TERMS if term not in text)
    assert not missing_terms, f"missing required terms: {missing_terms}"
    instruction_parts = [text]
    for reference in REQUIRED_REFERENCES:
        assert (SKILL_ROOT / reference).is_file(), f"missing {reference}"
        assert reference in text, f"SKILL.md does not route to {reference}"
        instruction_parts.append((SKILL_ROOT / reference).read_text(encoding="utf-8"))
    instruction_surface = "\n".join(instruction_parts)
    for pattern, label in FORBIDDEN_PATTERNS.items():
        assert not re.search(pattern, instruction_surface, re.IGNORECASE), f"forbidden {label}"

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hosts = manifest["hosts"]
    host_names = [host["host"] for host in hosts]
    assert len(host_names) == len(set(host_names)), "duplicate host manifest entry"
    assert {"cursor", "codex", "claude-code", "minimax", "langgraph-production", "swarmclaw"}.issubset(host_names)
    for host, target in APPROVED_TARGETS.items():
        entry = next(item for item in hosts if item["host"] == host)
        assert entry["target"] == target, f"unapproved exact target for {host}"
        assert Path(target).name == "agentcore-project-lifecycle"
    swarm = next(host for host in hosts if host["host"] == "swarmclaw")
    assert swarm["delivery"] == "foreign_swarm_adapter"
    assert swarm["validation"] == "swarm_owned_no_agentcore_install"

    for host in hosts:
        source = host.get("source")
        if source and not re.match(r"^[A-Za-z]:\\", source):
            assert (REPO_ROOT / source).exists(), f"missing adapter source for {host['host']}: {source}"

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    capsule = catalog["skill_capsules"][metadata["name"]]
    assert capsule["sha256"] == skill_sha256(), "execution catalog skill hash is stale"
    assert metadata["name"] in catalog["role_skills"]["operator-composer"]
    assert metadata["name"] in catalog["role_skills"]["context-steward"]

    print("PASS agentcore alignment skill")
    print(f"skill_sha256={skill_sha256()}")
    print(f"hosts={len(hosts)} native={sum(h['delivery'].startswith('native_skill') for h in hosts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
