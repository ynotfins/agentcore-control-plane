"""Switch project-scoped Bifrost upstreams to direct stdio launchers.

Wrappers remain available for future process pooling; Bifrost gets reliable
direct executables. Project router still owns active-project.json.
"""
from __future__ import annotations

import json
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
reg_path = repo / "contracts" / "bifrost-upstream-mcp-registry.json"
reg = json.loads(reg_path.read_text(encoding="utf-8"))

direct = {
    "serena": {
        "connection_type": "stdio",
        "executable_or_url": r"C:\Users\ynotf\AppData\Roaming\uv\tools\serena-agent\Scripts\serena.exe",
        "arguments": ["start-mcp-server", "--transport", "stdio", "--context", "ide"],
        "wrapper_script": None,
        "notes": [
            "Launched directly under Bifrost for reliability on Windows.",
            "Project activation remains via agentcore-project-router + Serena tools.",
            "Wrapper scripts under scripts/project_router/wrappers remain available for pooling experiments.",
        ],
    },
    "depwire": {
        "connection_type": "stdio",
        "executable_or_url": r"C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd",
        "arguments": ["mcp"],
        "wrapper_script": None,
        "notes": [
            "Direct depwire-cli MCP. connect_repo with verified local path before graph queries.",
            "Telemetry remains enabled; do not set DEPWIRE_NO_TELEMETRY.",
        ],
    },
    "tentra": {
        "connection_type": "stdio",
        "executable_or_url": r"C:\Program Files\nodejs\npx.cmd",
        "arguments": ["-y", "tentra-mcp@1.3.3", "--local"],
        "wrapper_script": None,
        "env_var_names": ["TENTRA_DATA_DIR"],
        "notes": [
            "Local mode only. Do not run tentra-mcp init or init --hook.",
            "Data path expected under H:\\AgentRuntime\\tentra\\data via TENTRA_DATA_DIR.",
        ],
    },
    "context-fabric": {
        "connection_type": "stdio",
        "executable_or_url": r"C:\Program Files\nodejs\node.EXE",
        "arguments": [
            r"C:\Users\ynotf\.cursor\vendor\context-fabric-mcp\node_modules\context-fabric\dist\index.js"
        ],
        "wrapper_script": None,
    },
    "filesystem": {
        "connection_type": "stdio",
        "executable_or_url": r"C:\Program Files\nodejs\npx.cmd",
        "arguments": [
            "-y",
            "@modelcontextprotocol/server-filesystem@2026.7.10",
            r"D:\github",
        ],
        "wrapper_script": None,
        "notes": [
            "Bounded to D:\\github only (no whole-drive roots).",
            "Further narrowing via project router wrappers remains optional.",
        ],
    },
    "mcp-debugger": {
        "executable_or_url": r"C:\Program Files\nodejs\npx.cmd",
        "arguments": ["-y", "mcp-debugger@0.0.78"],
        "notes": [
            "Pinned mcp-debugger@0.0.78. Deny attach tools in reviewer profile.",
        ],
    },
}

for cid, patch in direct.items():
    server = reg["servers"][cid]
    for k, v in patch.items():
        if v is None:
            server.pop(k, None)
        else:
            server[k] = v
    server["enabled"] = True

# Artiforge stays enabled but may be disconnected when PAT inactive — note it.
reg["servers"]["artiforge"]["notes"] = list(reg["servers"]["artiforge"].get("notes") or []) + [
    "If upstream returns 401 User is inactive, treat as deferred until ARTIFORGE_PAT is refreshed.",
]

reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
print("updated direct launchers for", sorted(direct))
