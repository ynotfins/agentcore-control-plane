import hashlib
import json
from pathlib import Path

DOCS = [
    ("PROJECT_ANCHOR.md", 1, "Constitution (Immutable)"),
    ("DOC_AUTHORITY.md", 2, "Authority Classification & Index"),
    ("BLUEPRINT.md", 3, "Locked Implementation Blueprint"),
    ("CONTEXT_BLOCK.md", 4, "Current Mutable System State"),
    ("MILESTONES.md", 5, "Locked Milestones Outcome & Exit Criteria"),
    ("AGENTS.md", 6, "Agent Operating Contract"),
    ("CLAUDE.md", 6, "Agent Specific Guidelines (Claude)"),
    ("MASTER_CONFIG_AND_PROMPT.md", 7, "Universal Setup & Prompt Guide"),
    ("contracts/global-agent-policy.yaml", 7, "Global Agent Policy Contract"),
    ("docs/handoffs/AGENTCORE_FULL_CHAT_HANDOFF_2026-07-22.md", 8, "Current State Handoff"),
    # Historical
    ("VALIDATION_REPORT.md", 99, "Historical Evidence"),
    ("CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md", 99, "Historical Evidence (Swarm)"),
    ("ECOSYSTEM_ARCHITECTURE.md", 99, "Historical Evidence")
]

base = Path(r"d:\github\agentcore-control-plane")

manifest = []
for rel_path, level, desc in DOCS:
    p = base / rel_path
    if p.exists():
        content = p.read_bytes()
        h = hashlib.sha256(content).hexdigest()
        manifest.append({
            "absolute_path": str(p.resolve()),
            "relative_path": rel_path,
            "sha256": h,
            "authority_level": level,
            "description": desc
        })

manifest_file = base / ".agentcore" / "runtime" / "authority-manifest.json"
manifest_file.parent.mkdir(parents=True, exist_ok=True)
manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

print("Authority Manifest generated:")
print(json.dumps(manifest, indent=2))
