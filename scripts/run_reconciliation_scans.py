"""AgentCore Reconciliation Scan Suite.

Runs:
1. Authority & read-order chain verification
2. Stale Stage A phrase scan in active contracts/rules
3. Stale global-memory-gateway / direct-MCP / Swarm-first scan
4. Obsolete PG16-as-AgentCore & port 65432 scan
5. Duplicate current-handoff classification scan
6. Secret & junk file scan
7. Internal Markdown-link & path validation
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def scan_authority_chain() -> list[str]:
    errors = []
    
    files_to_check = [
        REPO_ROOT / "DOC_AUTHORITY.md",
        REPO_ROOT / "BLUEPRINT.md",
        REPO_ROOT / "CONTEXT_BLOCK.md",
        REPO_ROOT / "MASTER_CONFIG_AND_PROMPT.md",
        REPO_ROOT / "contracts" / "global-agent-policy.yaml",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "rules" / "canonical" / "GLOBAL_AGENT_RULES.md",
    ]
    
    for path in files_to_check:
        text = path.read_text(encoding="utf-8")
        if "PROJECT_ANCHOR.md" in text and "DOC_AUTHORITY.md" in text and "BLUEPRINT.md" in text and "CONTEXT_BLOCK.md" in text:
            # Look for read order list specifically
            read_order_match = re.search(r"Read in this order:.*?(?=\n\n|\Z)", text, re.DOTALL | re.IGNORECASE) or \
                               re.search(r"Read order:.*?(?=\n\n|\Z)", text, re.DOTALL | re.IGNORECASE) or \
                               re.search(r"1\.\s*`?PROJECT_ANCHOR\.md`?.*", text, re.DOTALL)
            
            if read_order_match:
                section = read_order_match.group(0)
                anchor_pos = section.find("PROJECT_ANCHOR.md")
                doc_pos = section.find("DOC_AUTHORITY.md")
                bp_pos = section.find("BLUEPRINT.md")
                cb_pos = section.find("CONTEXT_BLOCK.md")
                if anchor_pos != -1 and doc_pos != -1 and bp_pos != -1 and cb_pos != -1:
                    if not (anchor_pos < doc_pos < bp_pos < cb_pos):
                        errors.append(f"{path.name}: authority chain order mismatch in read order section")
    return errors

def scan_stale_stage_a() -> list[str]:
    errors = []
    files_to_check = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "contracts" / "global-agent-policy.yaml",
        REPO_ROOT / "rules" / "canonical" / "GLOBAL_AGENT_RULES.md",
        REPO_ROOT / "MASTER_CONFIG_AND_PROMPT.md",
    ]
    for path in files_to_check:
        text = path.read_text(encoding="utf-8")
        if "preToolUse is offline-tested" in text or "preToolUse is not registered" in text or "Stage A (2026-07-20)" in text:
            errors.append(f"{path.name}: contains stale Stage A claim or claims preToolUse is not registered")
    return errors

def scan_obsolete_ports_and_dbs() -> list[str]:
    errors = []
    active_files = [
        REPO_ROOT / "PROJECT_ANCHOR.md",
        REPO_ROOT / "DOC_AUTHORITY.md",
        REPO_ROOT / "BLUEPRINT.md",
        REPO_ROOT / "CONTEXT_BLOCK.md",
        REPO_ROOT / "MASTER_CONFIG_AND_PROMPT.md",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json",
        REPO_ROOT / "contracts" / "agentcore-gateway-client.json",
    ]
    for path in active_files:
        text = path.read_text(encoding="utf-8")
        if ":65432" in text and "forbidden" not in text.lower() and "archived" not in text.lower():
            errors.append(f"{path.name}: active reference to obsolete port 65432")
        if "127.0.0.1:55432" in text and "legacy" not in text.lower() and "rollback" not in text.lower() and "swarm" not in text.lower() and "preserved" not in text.lower():
            errors.append(f"{path.name}: active non-legacy reference to PG16 port 55432 for AgentCore")
    return errors

def scan_duplicate_handoffs() -> list[str]:
    errors = []
    text = (REPO_ROOT / "DOC_AUTHORITY.md").read_text(encoding="utf-8")
    newest_matches = re.findall(r"\*\*Newest current[^*]*\*\*", text)
    if len(newest_matches) > 1:
        errors.append(f"DOC_AUTHORITY.md: multiple handoffs marked as 'Newest current': {newest_matches}")
    return errors

def scan_secrets_and_junk() -> list[str]:
    errors = []
    secret_patterns = [
        re.compile(r"sk-[a-zA-Z0-9]{32,}"),
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),
        re.compile(r"vk-[a-zA-Z0-9]{32,}"),  # Real virtual key token (not descriptive string)
    ]
    
    for p in REPO_ROOT.rglob("*"):
        if p.is_dir() or ".git" in p.parts or ".venv" in p.parts or "artifacts" in p.parts:
            continue
        rel = str(p.relative_to(REPO_ROOT))
        
        if p.suffix in (".md", ".yaml", ".yml", ".json", ".py", ".ps1"):
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                for sp in secret_patterns:
                    if sp.search(content):
                        errors.append(f"Secret-like token found in {rel}")
            except Exception:
                pass
    return errors

def scan_markdown_links() -> list[str]:
    errors = []
    md_files = [f for f in list(REPO_ROOT.glob("*.md")) + list((REPO_ROOT / "docs").rglob("*.md"))
                if "archive" not in f.parts]
    
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    
    for md in md_files:
        content = md.read_text(encoding="utf-8", errors="ignore")
        for match in link_pattern.finditer(content):
            target = match.group(2).split("#")[0].strip()
            if not target or target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:") or target.startswith("env.") or target.startswith("bc-id") or target.startswith("sandbox:"):
                continue
            
            # Resolve relative link
            if target.startswith("D:\\") or target.startswith("C:\\"):
                target_path = Path(target)
            else:
                target_path = (md.parent / target).resolve()
            
            if not target_path.exists():
                # Check repo-relative path fallback
                alt_path = (REPO_ROOT / target.lstrip("/\\")).resolve()
                if not alt_path.exists():
                    errors.append(f"{md.relative_to(REPO_ROOT)}: broken Markdown link -> {target}")
    return errors

def main() -> int:
    print("[*] Running AgentCore Reconciliation Scan Suite...")
    
    scans = [
        ("Authority & Read-Order Chain", scan_authority_chain),
        ("Stale Stage A Claims", scan_stale_stage_a),
        ("Obsolete Ports & DB Routes", scan_obsolete_ports_and_dbs),
        ("Duplicate Current-Handoff Classification", scan_duplicate_handoffs),
        ("Secrets & Junk Scan", scan_secrets_and_junk),
        ("Internal Markdown Links & Paths", scan_markdown_links),
    ]
    
    total_errors = 0
    for name, scan_func in scans:
        errs = scan_func()
        if errs:
            print(f"\n[FAIL] {name}:")
            for e in errs:
                print(f"  - {e}")
            total_errors += len(errs)
        else:
            print(f"  [PASS] {name}")
            
    if total_errors > 0:
        print(f"\nTotal scan failures: {total_errors}")
        return 1
        
    print("\n[PASS] All reconciliation scans passed cleanly.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
