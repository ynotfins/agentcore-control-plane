#!/usr/bin/env python3
"""Add Repomix to bifrost-upstream-mcp-registry.json and capability_profiles.builder.allowed_server_ids."""
from __future__ import annotations
import json
import re
from pathlib import Path

REGISTRY = Path(r"D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json")

REPOMIX_ENTRY = {
    "canonical_id": "repomix",
    "display_name": "Repomix MCP",
    "purpose": "Pack entire repositories (or directories) into a single AI-friendly file and grep the packed output for repo-wide awareness in agent context.",
    "owner": "agentcore",
    "pinned_version": "1.16.1",
    "connection_type": "stdio",
    "executable_or_url": "C:\\Program Files\\nodejs\\npx.cmd",
    "arguments": ["-y", "repomix@1.16.1", "--mcp"],
    "env_var_names": [],
    "timeout_seconds": 300,
    "health_check_type": "mcp_ping",
    "project_scope": "global",
    "write_classification": "bounded_write",
    "permitted_tools": ["*"],
    "denied_tools": [],
    "capability_profiles": ["builder"],
    "logging_policy": {
        "log_invocations": True,
        "log_content": False,
        "redact_secrets": True,
    },
    "retry_policy": {
        "max_attempts": 1,
        "backoff_seconds": 2,
        "retry_on": ["spawn_failure"],
    },
    "rollback_route": "Disable repomix client; outputs land in OS temp by default and never persist into the gateway process.",
    "enabled": True,
    "bifrost_client_name": "repomix",
    "status": "active",
    "notes": [
        "Authoritative source: yamadashy/repomix (npm: repomix).",
        "npx launcher with --mcp flag is the canonical invocation confirmed via 'npx -y repomix --help' (v1.16.1).",
        "Provides pack_codebase, pack_remote_repository, pack_directory, read_repomix_output, grep_repomix_output, file_system_read_file/directory/list_directory, search_files, run_slash_command (live inventory captured at first MCP ping).",
        "Repomix is read-mostly for the gateway (bounded_write to OS temp). Never write to D:\\github\\agentcore-control-plane or other registered worktrees from this server.",
        "Bounded to OS-temp output by default; agent must not pass D:\\github\\agentcore-control-plane\\STATE or contracts paths as targets.",
    ],
}


def main() -> int:
    raw = REGISTRY.read_text(encoding="utf-8")
    # Preserve original line endings
    has_crlf = "\r\n" in raw
    nl = "\r\n" if has_crlf else "\n"
    data = json.loads(raw)

    if "repomix" in data["servers"]:
        print("repomix already in servers; skipping insertion")
    else:
        data["servers"]["repomix"] = REPOMIX_ENTRY
        print(f"Inserted repomix server. Total servers: {len(data['servers'])}")

    # Add repomix to builder capability profile
    builder = data["capability_profiles"]["builder"]
    if "repomix" in builder["allowed_server_ids"]:
        print("repomix already in builder.allowed_server_ids; skipping")
    else:
        builder["allowed_server_ids"].append("repomix")
        print("Added repomix to builder.allowed_server_ids")

    # Write back with same line endings
    new_text = json.dumps(data, indent=2, ensure_ascii=False)
    if has_crlf:
        new_text = new_text.replace("\n", "\r\n")
    REGISTRY.write_text(new_text, encoding="utf-8", newline="")
    print(f"Wrote {REGISTRY} ({len(new_text)} bytes, {'CRLF' if has_crlf else 'LF'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
