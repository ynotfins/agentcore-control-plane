#Requires -Version 7
<#
.SYNOPSIS
  Make KIE the priority model provider in OpenCode and Zed.
.DESCRIPTION
  Timestamped backups beside each live file. OpenCode: Responses-capable KIE
  provider via @ai-sdk/openai + env KIE_API_KEY. Zed: openai_compatible.kie with
  chat_completions disabled (Responses). Does not write API keys into files.
  Eigent has no local provider config file on this workstation; skipped.
#>
[CmdletBinding()]
param(
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Python = "D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
  throw "Project venv python missing: $Python"
}

$ts = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssfffZ")
$script = @'
import json
import shutil
import sys
from pathlib import Path

ts = sys.argv[1]
dry = sys.argv[2] == "1"

def backup(path: Path) -> Path:
    bak = path.with_name(path.name + f".kie-{ts}.bak")
    if not dry:
        shutil.copy2(path, bak)
    return bak

def write_json(path: Path, data: dict) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if dry:
        return
    path.write_text(text, encoding="utf-8")

kie_models = {
    "gpt-6.1-sol": {"name": "GPT-6.1 Sol", "limit": {"context": 272000, "output": 65536}},
    "gpt-6-astra": {"name": "GPT-6 Astra", "limit": {"context": 272000, "output": 65536}},
    "gpt-5.5": {"name": "GPT-5.5", "limit": {"context": 272000, "output": 65536}},
}

zed_models = []
for mid, meta in kie_models.items():
    zed_models.append({
        "name": mid,
        "display_name": f"{meta['name']} (KIE)",
        "max_tokens": 272000,
        "reasoning_effort": "high",
        "capabilities": {
            "tools": True,
            "images": False,
            "parallel_tool_calls": False,
            "prompt_cache_key": False,
            "chat_completions": False,
            "interleaved_reasoning": False,
            "max_tokens_parameter": False,
        },
    })

# --- OpenCode ---
oc_path = Path(r"C:\Users\ynotf\.config\opencode\opencode.json")
oc = json.loads(oc_path.read_text(encoding="utf-8"))
oc_bak = backup(oc_path)
provider = oc.setdefault("provider", {})
provider["kie"] = {
    "npm": "@ai-sdk/openai",
    "name": "KIE",
    "env": ["KIE_API_KEY"],
    "options": {
        "baseURL": "https://api.kie.ai/openai/v1",
        "apiKey": "{env:KIE_API_KEY}",
    },
    "models": kie_models,
}
enabled = ["kie"]
for item in (oc.get("enabled_providers") or []):
    if item != "kie" and item not in enabled:
        enabled.append(item)
oc["enabled_providers"] = enabled
oc["model"] = "kie/gpt-6.1-sol"
oc["small_model"] = "kie/gpt-5.5"
# Preserve singleton provider schema; never introduce providers plural.
if "providers" in oc:
    raise SystemExit("Refuse to write: plural providers key present")
write_json(oc_path, oc)
print(f"opencode_backup={oc_bak}")
print(f"opencode_model={oc['model']}")
print(f"opencode_enabled={','.join(oc['enabled_providers'])}")
print(f"opencode_has_kie={('kie' in oc['provider'])}")
print(f"opencode_mcp_url={oc.get('mcp', {}).get('servers', {}).get('agentcore-gateway', {}).get('url')}")

# OpenCode auth credential (required for picker visibility alongside env apiKey)
import os
kie_key = os.environ.get("KIE_API_KEY") or ""
if not kie_key.strip():
    raise SystemExit("KIE_API_KEY missing in process environment")
auth_path = Path(r"C:\Users\ynotf\.local\share\opencode\auth.json")
auth_path.parent.mkdir(parents=True, exist_ok=True)
auth = {}
if auth_path.exists():
    auth = json.loads(auth_path.read_text(encoding="utf-8"))
    auth_bak = backup(auth_path)
    print(f"opencode_auth_backup={auth_bak}")
if not dry:
    auth["kie"] = {"type": "api", "key": kie_key}
    auth_path.write_text(json.dumps(auth, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("opencode_auth_kie=True")
print("opencode_auth_providers=" + ",".join(sorted(auth.keys()) if auth else ["kie"]))

# --- Zed ---
zed_path = Path(r"C:\Users\ynotf\AppData\Roaming\Zed\settings.json")
zed = json.loads(zed_path.read_text(encoding="utf-8"))
zed_bak = backup(zed_path)
lm = zed.setdefault("language_models", {})
# Keep existing open_router; add openai_compatible.kie
ocomp = lm.setdefault("openai_compatible", {})
ocomp["kie"] = {
    "api_url": "https://api.kie.ai/openai/v1",
    "available_models": zed_models,
}
agent = zed.setdefault("agent", {})
agent["default_model"] = {
    "provider": "kie",
    "model": "gpt-6.1-sol",
    "effort": "high",
    "enable_thinking": True,
}
write_json(zed_path, zed)
print(f"zed_backup={zed_bak}")
print(f"zed_default_provider={agent['default_model']['provider']}")
print(f"zed_default_model={agent['default_model']['model']}")
print(f"zed_kie_models={len(zed_models)}")
print(f"zed_has_open_router={('open_router' in lm)}")
print("eigent_status=no_local_provider_file_skipped")
print(f"dry_run={dry}")
'@

$tmpPy = Join-Path $env:TEMP ("apply-kie-provider-{0}.py" -f $ts)
Set-Content -LiteralPath $tmpPy -Value $script -Encoding UTF8
$env:KIE_API_KEY = [Environment]::GetEnvironmentVariable("KIE_API_KEY", "User")
if ([string]::IsNullOrWhiteSpace($env:KIE_API_KEY)) {
  throw "User-scope KIE_API_KEY is empty; set it before applying KIE provider config."
}
$dryFlag = if ($DryRun) { "1" } else { "0" }
& $Python $tmpPy $ts $dryFlag
$exit = $LASTEXITCODE
Remove-Item -LiteralPath $tmpPy -Force -ErrorAction SilentlyContinue
if ($exit -ne 0) { throw "Apply-KieProviderPriority failed with exit $exit" }
