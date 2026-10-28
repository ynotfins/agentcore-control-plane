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
    "zed": r"{userprofile}\.agents\skills\agentcore-project-lifecycle",
    "eigent": r"{userprofile}\.eigent\skills\agentcore-project-lifecycle",
    "cursor": r"{userprofile}\.cursor\skills\agentcore-project-lifecycle",
    "codex": r"{userprofile}\.agents\skills\agentcore-project-lifecycle",
    "claude-code": r"{userprofile}\.claude\skills\agentcore-project-lifecycle",
    "minimax": r"{userprofile}\.minimax\skills\agentcore-project-lifecycle",
    "mavis": r"{userprofile}\.mavis\skills\agentcore-project-lifecycle",
}
CERTIFICATION_STATES = {
    "source_ready",
    "installed_unverified",
    "configured_restart_required",
    "live_validated",
    "manual_import_pending",
    "UI_only_pending",
    "unverified",
    "unsupported_with_reason",
}
INSTALLED_CERTIFICATIONS = {
    "installed_unverified",
    "configured_restart_required",
    "live_validated",
}
REQUIRED_HOSTS = {
    "zed",
    "eigent",
    "cursor",
    "codex",
    "claude-code",
    "claude-desktop",
    "minimax",
    "mavis",
    "minimax-classic",
    "antigravity",
    "open-interpreter",
    "cherry-studio",
    "zoo-code",
    "devin",
    "reasonix",
    "opencode",
    "open-design",
    "autogpt",
    "agent-orchestrator",
    "lobehub",
    "openhands",
    "zcode",
    "openclaw",
    "clawx",
    "langgraph-production",
    "langgraph-studio",
    "swarmclaw",
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


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    if not root.is_dir():
        return "missing"
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def installed_skill_hash_errors(
    manifest: dict,
    source_root: Path = SKILL_ROOT,
    *,
    userprofile: Path | None = None,
) -> list[str]:
    """Verify live bytes only for hosts whose certification claims installation."""
    errors: list[str] = []
    profile_root = userprofile or Path.home()
    source_hash = tree_digest(source_root)
    if source_hash == "missing":
        return [f"canonical skill source missing: {source_root}"]

    for entry in manifest.get("hosts", []):
        certification = entry.get("certification")
        if certification not in INSTALLED_CERTIFICATIONS:
            continue
        host = entry.get("host", "<unknown>")
        if not str(entry.get("delivery", "")).startswith("native_skill"):
            errors.append(
                f"{host}: certification {certification} requires native_skill delivery for hash parity"
            )
            continue
        raw_target = entry.get("target")
        declared_hash = entry.get("installed_sha256")
        if not isinstance(raw_target, str) or not raw_target:
            errors.append(f"{host}: installed certification requires an exact target")
            continue
        if not isinstance(declared_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", declared_hash):
            errors.append(f"{host}: installed certification requires installed_sha256")
            continue
        target = Path(raw_target.replace("{userprofile}", str(profile_root)))
        actual_hash = tree_digest(target)
        if declared_hash != source_hash or actual_hash != source_hash:
            errors.append(
                f"{host}: installed skill hash mismatch "
                f"declared={declared_hash} actual={actual_hash} source={source_hash}"
            )
    return errors


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
    assert manifest.get("schema_version") == 2
    assert set(manifest.get("certification_states", [])) == CERTIFICATION_STATES
    hosts = manifest["hosts"]
    host_names = [host["host"] for host in hosts]
    assert len(host_names) == len(set(host_names)), "duplicate host manifest entry"
    assert REQUIRED_HOSTS.issubset(host_names), f"missing hosts: {sorted(REQUIRED_HOSTS - set(host_names))}"
    for host in hosts:
        assert host.get("certification") in CERTIFICATION_STATES, (
            f"invalid certification for {host['host']}: {host.get('certification')!r}"
        )
    for host, target in APPROVED_TARGETS.items():
        entry = next(item for item in hosts if item["host"] == host)
        assert entry["target"] == target, f"unapproved exact target for {host}"
        assert Path(target).name == "agentcore-project-lifecycle"
    swarm = next(host for host in hosts if host["host"] == "swarmclaw")
    assert swarm["delivery"] == "foreign_swarm_adapter"
    assert swarm["validation"] == "swarm_owned_no_agentcore_install"
    assert swarm["ownership"] == "foreign_swarm"
    openclaw = next(host for host in hosts if host["host"] == "openclaw")
    assert openclaw["ownership"] == "agentcore"
    assert openclaw["governed_product_root"] == r"D:\github\open--claw"
    assert openclaw["windows_operations_root"] == r"D:\openclaw"
    assert openclaw["excluded_live_state_root"] == r"C:\Users\ynotf\.openclaw"
    clawx = next(host for host in hosts if host["host"] == "clawx")
    assert clawx["ownership"] == "agentcore"
    assert clawx["installer_root"] == r"C:\Program Files\ClawX"

    for host in hosts:
        source = host.get("source")
        if source and not re.match(r"^[A-Za-z]:\\", source):
            assert (REPO_ROOT / source).exists(), f"missing adapter source for {host['host']}: {source}"

    hash_errors = installed_skill_hash_errors(manifest)
    assert not hash_errors, "; ".join(hash_errors)

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    capsule = catalog["skill_capsules"][metadata["name"]]
    assert capsule["sha256"] == skill_sha256(), "execution catalog skill hash is stale"
    assert metadata["name"] in catalog["role_skills"]["operator-composer"]
    assert metadata["name"] in catalog["role_skills"]["context-steward"]

    print("PASS agentcore alignment skill")
    print(f"skill_sha256={skill_sha256()}")
    installed_claims = sum(h["certification"] in INSTALLED_CERTIFICATIONS for h in hosts)
    print(
        f"hosts={len(hosts)} native={sum(h['delivery'].startswith('native_skill') for h in hosts)} "
        f"installed_hash_claims={installed_claims}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
