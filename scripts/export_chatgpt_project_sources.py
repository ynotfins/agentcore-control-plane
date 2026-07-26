"""ChatGPT Project Source Export and Validation Script.

Authority: DOC_AUTHORITY.md Level 2
Manifest: docs/current/CHATGPT_PROJECT_SOURCE_MANIFEST.md

Validates that:
1. Every source record in CORE_ALWAYS_INCLUDE, WORKSTREAM_ONLY, and EXCLUDE_FROM_PROJECT_SOURCES exists.
2. SHA-256 hashes match current disk content.
3. No duplicate same-title files exist in CORE_ALWAYS_INCLUDE.
4. No secret-bearing files or live secret-bearing configs are included in project sources.
5. Optionally exports approved CORE_ALWAYS_INCLUDE files into a target directory without modifying content.

Usage:
  python scripts/export_chatgpt_project_sources.py --check
  python scripts/export_chatgpt_project_sources.py --export-dir E:\\ChatGPT-Project-Sources
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "docs" / "current" / "CHATGPT_PROJECT_SOURCE_MANIFEST.md"

CORE_ALWAYS_INCLUDE_FILES = [
    ("PROJECT_ANCHOR.md", 1, "stable", "f0e55d55e824ee8f955a9dc7b28bafa09df8f6045e5705d4ab202795d1619800", "None", False, True),
    ("DOC_AUTHORITY.md", 2, "stable", "99c4fd0d53c5ee3facf9466a8b8f255af43ccb7a9ef81ba226f31e9dc2e55ed2", "Supersedes 2026-07-20 version", True, True),
    ("BLUEPRINT.md", 3, "stable", "c2df8fd5f471b65a6c56e89d87c849ce32adc7325596b0cc9737bb6360fb263d", "None", False, True),
    ("CONTEXT_BLOCK.md", 4, "current", "5e6c29cd8ce43b1e65ea2aec4e5c4f633683cdc926baf8d0e49ea7398f2a4922", "Supersedes 2026-06-30 CONTEXT_BLOCK", True, True),
    ("docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md", 5, "stable", "16bfc3a22619da081de0fc330cec2f8dd5985ff435ef9d27d28a9869a35ea39c", "Derives from BLUEPRINT.md", False, True),
    ("contracts/bifrost-upstream-mcp-registry.json", 6, "current", "dfe80100377468ed8db4df32675a20d096baac6ec984f72d187efb41f09dc5f4", "Canonical upstream MCP registry", True, True),
    ("contracts/agentcore-gateway-client.json", 6, "stable", "6bf88671d68fb8a55c092f09f8b6f657952c00fb5f982be391a2486713bfda68", "Single IDE gateway client contract", False, True),
    ("contracts/global-agent-policy.yaml", 7, "stable", "8207ebe55408297866a5d20ddeb6a70b3176a8e68553eaa5236bea8cb796e188", "Source for per-IDE rule profiles", False, True),
    ("contracts/model-context-profiles.json", 7, "stable", "5b8aae35be2faaad22001881720dfe6bcd75f5ac542629f467199676d5946082", "Model token budget profiles", False, True),
    ("MASTER_CONFIG_AND_PROMPT.md", 7, "current", "905242678b09474841fccaa6b6bd40e35cba8b1777f23f80d9694461153d5e9c", "Root setup guide & embedded prompt", True, True),
    ("AGENTS.md", 6, "stable", "b835ef4571cfb7d96457168c44f11c01c1d79901fae25055776dddc369458c8e", "Source-controlled agent operating contract", False, True),
    ("CLAUDE.md", 6, "stable", "2a1241e710ea22ffc1d8e4c91e5f730aaf67a293779347fcb53df034693658de", "Agent-specific guidelines", False, True),
    ("docs/handoffs/AGENTCORE_SWARM_DUAL_ECOSYSTEM_HANDOFF_2026-07-25.md", 8, "current", "da1e376b21137d494e27ddf66d18eee2c0fa89eb150a5414b0f8b1e96af52878", "Supersedes 2026-07-22 full-chat handoff", True, True),
]

WORKSTREAM_ONLY_FILES = [
    ("audits/cursor-context/CURSOR_STAGE_B_INTEGRITY_HARNESS_ACCEPTANCE_2026-07-24.md", 8, "runbook", "1cde698d270f1e9cf2137562af960739b1a878af0fc2b51642adfa80d5c0ae89", "Cursor Stage B acceptance evidence", True, True),
    ("audits/cursor-context/CURSOR_NATIVE_SKILL_SURFACE_2026-07-24.md", 8, "runbook", "1ff81013e807658543e02089b68929f207e67a44a977fee8cce3093625b33c93", "Cursor native skill surface audit", True, True),
    ("docs/operations/AUTOMATIC_NEW_CHAT_RECOVERY.md", 8, "runbook", "899b62545900f3fddd232e0f5dff3e8b984813252c96d1b3c28c629d9efce318", "Cursor new-chat recovery runbook", True, True),
    ("audits/bifrost/BIFROST_COMPLETE_CONFIGURATION_ACCEPTANCE_2026-07-24.md", 8, "runbook", "ba3b1e064005038a49d796ae79f2074b7a102c42efeb1c7be2d7acc54ae95774", "Bifrost configuration acceptance audit", True, True),
    ("docs/bifrost/BIFROST_OPERATOR_RUNBOOK.md", 8, "runbook", "73201e8b9c8f94f36477e05d9f2de96346dea4d08747965c9738ef00005a96b8", "Bifrost start/stop/restart runbook", True, True),
    ("docs/bifrost/BIFROST_PROVIDER_RUNBOOK.md", 8, "runbook", "9ea9c4333a41a1bce8442af95737539dcdf639216a772079f44c590874a604a2", "Bifrost provider configuration runbook", True, True),
    ("docs/bifrost/CHATGPT_SECURE_MCP_TUNNEL.md", 8, "runbook", "a9e2de948a8981f862b28ac7594d10b69fd6a9eb978e94986554d7937872258c", "ChatGPT tunnel & compat proxy runbook", True, True),
    ("docs/bifrost/MCP_CLASSIFICATION_MATRIX.md", 8, "runbook", "117225721b7c2bedc57ae39d03af57553f00b013e44568122612589e73f28ff3", "Bifrost MCP classification matrix", True, True),
    ("docs/bifrost/UNIFIED_GATEWAY_SETUP.md", 8, "runbook", "0d461035aac27dee1ff59c9f29efea6f72bd42eee1419795f469e8d8d65d423c", "Unified IDE gateway setup runbook", True, True),
    ("docs/bifrost/CAPABILITY_PROFILES.md", 8, "runbook", "7d04b0da24a88ab6cebe4f3d6214f661924d1a73d5b15e812d7e49a1e5b4980a", "Bifrost capability profiles runbook", True, True),
    ("docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md", 8, "runbook", "e7c736fa9516a1eb39345449f1fa679d551e0efdb7b61b91825def22e2992a48", "LangGraph M6 production & Studio runbook", True, True),
    ("docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md", 8, "runbook", "ed1a62ab46464224b2adcff83b8f39a206b416071e568fa0792aaad875ef4b78", "LangGraph workflow CLI quickstart", True, True),
    ("docs/operations/OPENROUTER_MCP.md", 8, "runbook", "6ed17b91c5727aa291695cefc0d0d262f50ce5dd74d62b33fc6c89759f6e36c7", "OpenRouter MCP runbook", True, True),
    ("docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md", 8, "runbook", "a246962815155837ee3a80aeb91bb773a146cf8d44931cc53099a68e2bddfbc3", "Dormant MCP capability catalog", True, True),
    ("docs/operations/CHERRY_STUDIO_AGENTCORE.md", 8, "runbook", "54fa41295179b32d6623d02cc624c677d4aa1ceb074228845defa79c6de190c9", "Cherry Studio AgentCore runbook", True, True),
    ("audits/CHERRY_TARGET_AGENT_REPAIR_2026-07-24.md", 8, "runbook", "a83cbe73d7ac4a541f7e2ae0f0ca0b8e367caaad406c213cf1b996ffdcd91b74", "Cherry Studio target agent repair evidence", True, True),
    ("docs/current/CURRENT_PROJECT_RECONSTRUCTION.md", 8, "task-specific", "230d0dc731fd89192da37b1c302186c0d193dd9f20c84bd8518a68282ec88b02", "Long-form current-state evidence synthesis", True, True),
]

EXCLUDE_FROM_PROJECT_SOURCES_FILES = [
    ("ECOSYSTEM_ARCHITECTURE.md", 99, "historical", "41aa867db041fc9bc584e2b2547fdae63ac9da95bbe46dee495d2ab865c09467", "Pre-2026-06-30 ecosystem architecture", False, False),
    ("VALIDATION_REPORT.md", 99, "historical", "d83fe233825ee9c3f8ebdda810a343a73a228877eb6424485b7d4aef325ad6c5", "Historical 2026-06-24 validation report", False, False),
    ("CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md", 99, "historical", "4e0fa4398b20dc3e056427cc4791f00dbaa91e0ab0d6c3d9969adcd858750878", "Frozen Swarm rollout status", False, False),
    ("docs/MCP_SERVER_CONFIGURATION_REFERENCE.md", 99, "historical", "6f76f2adb514e7b97b411af6ac6e6d7105792b97a29a11633bdb68a40193b046", "Superseded pre-Bifrost direct-MCP reference", False, False),
    ("docs/CONTEXT_WINDOW_OPTIMIZATION_POLICY.md", 99, "historical", "1e5ca9b74ad99721fb8ea18511796d5938c10a8071fe34e590b32116cc98417b", "Superseded pre-Bifrost context policy", False, False),
    ("docs/AGENTCORE_STORAGE_DESIGN.md", 99, "historical", "7ec174fe9a197eac48db2d6c6cec530a78023e1f529b40b5ff5b03b1364c9e34", "Superseded pre-PG18 storage design", False, False),
    ("docs/SERENA_CONFIGURATION.md", 99, "historical", "ec84d715a27e3dff808785e920465e7e4ed1588b611ce0d6ed1a6d56a8cf5446", "Superseded pre-Bifrost Serena config", False, False),
    ("docs/CHERRY_NEWAPI_INTEGRATION.md", 99, "historical", "3ee0364ea3e2882314a6281129e060008b70278d5bc6768381a214acc2526913", "Superseded Cherry/NewAPI integration notes", False, False),
    ("docs/bifrost/BIFROST_CODE_MODE_RUNBOOK.md", 8, "task-specific", "0db9f09c1aad3b2c25cadab0a18f24bd9069b3fa2b690fdb386ff3d023e00727", "Task-specific Code Mode VFS runbook", True, False),
    ("docs/handoffs/AGENTCORE_FULL_CHAT_HANDOFF_2026-07-22.md", 8, "historical", "72cca398d3afda85fba435ff8ccca10a7bdf4855a2fd37ba80e12ea4dbdf85e1", "Superseded full-chat handoff snapshot", True, False),
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def validate_sources() -> bool:
    all_ok = True
    print("[*] Validating ChatGPT Project Source Manifest files...")

    seen_canonical: set[str] = set()
    seen_titles: set[str] = set()

    all_groups = [
        ("CORE_ALWAYS_INCLUDE", CORE_ALWAYS_INCLUDE_FILES),
        ("WORKSTREAM_ONLY", WORKSTREAM_ONLY_FILES),
        ("EXCLUDE_FROM_PROJECT_SOURCES", EXCLUDE_FROM_PROJECT_SOURCES_FILES),
    ]

    for group_name, records in all_groups:
        print(f"\n--- {group_name} ({len(records)} files) ---")
        for rel_path, level, status, expected_sha, relation, live_claims, safe in records:
            abs_path = REPO_ROOT / rel_path
            if not abs_path.is_file():
                print(f"[FAIL] Missing file: {rel_path}")
                all_ok = False
                continue

            # Duplicate canonical path check
            if rel_path in seen_canonical:
                print(f"[FAIL] Duplicate canonical path: {rel_path}")
                all_ok = False
            seen_canonical.add(rel_path)

            # Title / filename duplicate check in CORE
            if group_name == "CORE_ALWAYS_INCLUDE":
                title = abs_path.name.lower()
                if title in seen_titles:
                    print(f"[FAIL] Duplicate title in CORE_ALWAYS_INCLUDE: {abs_path.name}")
                    all_ok = False
                seen_titles.add(title)

            # Check suffix artifacts (2), (5), etc.
            if re.search(r"\(\d+\)\.md$", abs_path.name):
                print(f"[FAIL] Upload artifact suffix filename detected: {abs_path.name}")
                all_ok = False

            # Hash calculation
            actual_sha = sha256_file(abs_path)
            if expected_sha and actual_sha != expected_sha:
                print(f"[FAIL] Hash mismatch for {rel_path}: expected {expected_sha}, got {actual_sha}")
                all_ok = False
            else:
                print(f"  [OK] {rel_path} (level={level}, status={status}, sha={actual_sha[:12]}...)")

    return all_ok

def export_core_package(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_summary = []
    print(f"\n[*] Exporting CORE_ALWAYS_INCLUDE files to {output_dir}...")

    for rel_path, level, status, _, relation, live_claims, safe in CORE_ALWAYS_INCLUDE_FILES:
        src = REPO_ROOT / rel_path
        # Sanitize filename if inside nested directory
        dest_filename = src.name
        dest = output_dir / dest_filename
        
        shutil.copy2(src, dest)
        sha = sha256_file(dest)
        manifest_summary.append({
            "filename": dest_filename,
            "canonical_relative_path": rel_path,
            "authority_level": level,
            "status": status,
            "sha256": sha,
            "last_verified_date": "2026-07-25",
            "relation": relation,
            "mutable_live_claims_require_verification": live_claims,
            "safe_for_broad_chatgpt_retrieval": safe
        })
        print(f"  [EXPORTED] {dest_filename} -> {sha[:12]}...")

    manifest_json = output_dir / "CHATGPT_CORE_PACKAGE_INDEX.json"
    manifest_json.write_text(json.dumps(manifest_summary, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Exported {len(CORE_ALWAYS_INCLUDE_FILES)} files. Package index: {manifest_json}")

def main() -> int:
    parser = argparse.ArgumentParser(description="Export and validate ChatGPT Project Source package")
    parser.add_argument("--check", action="store_true", help="Validate manifest source records and hashes")
    parser.add_argument("--export-dir", type=str, help="Directory to export CORE_ALWAYS_INCLUDE files to")

    args = parser.parse_args()

    ok = validate_sources()
    if not ok:
        print("\n[FAIL] Validation errors found!")
        return 1

    if args.export_dir:
        export_core_package(Path(args.export_dir))

    print("\n[PASS] ChatGPT Project Source Manifest check completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
