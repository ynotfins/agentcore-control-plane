"""Sanitized check of MiniMax Code live mcp.json Authorization header (no secret printed)."""
import hashlib
import json
import os
from pathlib import Path

d = json.loads(Path(r"C:\Users\ynotf\.minimax\mcp\mcp.json").read_text(encoding="utf-8"))
auth = d["mcpServers"]["agentcore-gateway"]["headers"].get("Authorization", "")
print("starts_bearer:", auth.startswith("Bearer "))
print("contains_env_placeholder:", "${env:" in auth)
tok = auth[7:] if auth.startswith("Bearer ") else auth
print("token_len:", len(tok))
print("token_prefix8:", tok[:8])
vk = os.environ.get("BIFROST_MCP_VIRTUAL_KEY", "")
if vk:
    print("matches_user_vk:", tok == vk)
print("token_sha256:", hashlib.sha256(tok.encode()).hexdigest())
