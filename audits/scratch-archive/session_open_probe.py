import json, os, urllib.request, urllib.error, winreg, re, sys

def vk():
    v = os.environ.get("BIFROST_MCP_VIRTUAL_KEY") or ""
    if v:
        return v
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
        return str(winreg.QueryValueEx(k, "BIFROST_MCP_VIRTUAL_KEY")[0])

URL = "http://127.0.0.1:8080/mcp"
session = None

def post(payload, timeout=30):
    global session
    body = json.dumps(payload).encode()
    h = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer " + vk(),
    }
    if session:
        h["Mcp-Session-Id"] = session
    req = urllib.request.Request(URL, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            hdr = {k.lower(): v for k, v in r.headers.items()}
            code = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        hdr = {k.lower(): v for k, v in e.headers.items()}
        code = e.code
    except Exception as e:
        return 0, {"exception": type(e).__name__, "msg": str(e)[:200]}
    if hdr.get("mcp-session-id"):
        session = hdr["mcp-session-id"]
    data = None
    if raw.strip().startswith("{"):
        data = json.loads(raw)
    else:
        for line in raw.splitlines():
            if line.startswith("data:"):
                chunk = line[5:].strip()
                if chunk and chunk != "[DONE]":
                    try:
                        data = json.loads(chunk)
                    except Exception:
                        pass
    return code, data

post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe2","version":"0"}}})
post({"jsonrpc":"2.0","method":"notifications/initialized"})

variants = [
  {"project_key":"agentcore-control-plane"},
  {"project_key":"agentcore-control-plane","client_key":"cursor","agent_key":"cursor-agent","session_key":"cherry-probe-cursor-style","branch_name":"main","context_profile":"standard-context","canonical_repo_path":r"D:\github\agentcore-control-plane","worktree_path":r"D:\github\agentcore-control-plane"},
  {"project_key":"agentcore-control-plane","client_key":"cherry-studio","agent_key":"cherry-studio-assistant","session_key":"cherry-probe-full","branch_name":"main","context_profile":"standard-context","canonical_repo_path":r"D:\github\agentcore-control-plane","worktree_path":r"D:\github\agentcore-control-plane","repo_key":"agentcore-control-plane"},
]
for i, args in enumerate(variants):
    code, data = post({"jsonrpc":"2.0","id":10+i,"method":"tools/call","params":{"name":"agentcore_memory-session_open","arguments":args}}, timeout=45)
    s = json.dumps(data)[:800]
    s = re.sub(r"Bearer [A-Za-z0-9_\\-\\.]+", "Bearer ***", s)
    print("--- variant", i, "code", code)
    print(s)
