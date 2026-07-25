"""Generate a Cherry Studio 1.9.x provider import JSON for all present env-var keys.

This script is the FIRST half of the AgentCore canonical pattern for
configuring Cherry Studio's LLM providers from Windows env vars. It
generates an import JSON that follows the same shape as Cherry's
redux-persist LlmState.providers slice (see
src/renderer/src/store/llm.ts and src/renderer/src/config/providers.ts
in the cloned cherry-studio source).

The companion script `inject_cherry_providers.js` (Node.js, `level`
package) consumes the same JSON and writes it directly into Cherry's
Local Storage leveldb under the `persist:cherry-studio` key, replacing
the `llm` slice.

Default routing (per agentcore-control-plane policy):
- defaultModel         = minimax:MiniMax-M3     (PRIMARY chat)
- topicNamingModel     = minimax:MiniMax-M2.7-highspeed  (cheap)
- translateModel       = minimax:MiniMax-M3     (PRIMARY)
- quickModel           = deepseek:deepseek-v4-flash  (cheap)
- second-enabled model = deepseek:deepseek-v4-pro     (V4 Pro per user)

The user can also pick any other enabled provider/model from the UI.

Security:
- Reads env values via os.environ / winreg fallback. NEVER prints the
  key values to stdout or to the import JSON as a debug field. The
  import JSON is written with normal apiKey fields only.
- Backs up the existing Data dir + leveldb to E:\\AgentCore-Backups\\
  before generating the import artifact.
- Does not modify any file under CherryStudio\\; it only WRITES the
  import JSON to Data\\agentcore-cherry-providers-import.json. The
  actual LDB write is the companion Node script's job.

Usage (from PowerShell, after `cd` into the cherry scripts dir):
    uv run setup_cherry_providers.py                 # dry-run + write import JSON
    uv run setup_cherry_providers.py --print-models  # also print catalog of models

Exit codes:
    0 success
    2 CherryStudio AppData not found
    3 no providers could be built (no env keys)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from hashlib import sha256
from pathlib import Path

CHERRY_ROOT = Path(os.environ.get("APPDATA", "")) / "CherryStudio"
DATA_DIR = CHERRY_ROOT / "Data"
LEVELDB = CHERRY_ROOT / "Local Storage" / "leveldb"
IMPORT_ARTIFACT = DATA_DIR / "agentcore-cherry-providers-import.json"
BACKUP_ROOT = Path(r"E:\AgentCore-Backups")

# --- Canonical provider catalog (mirrors SYSTEM_PROVIDERS_CONFIG in
# cherry-studio/src/renderer/src/config/providers.ts and the
# SYSTEM_MODELS map in cherry-studio/src/renderer/src/config/models/default.ts).
# Only providers that map to real Windows env vars are included; the
# script silently skips providers whose env var is not set.
PROVIDER_CATALOG = {
    "minimax": {
        "env_var": "MINIMAX_API_KEY",
        "type": "openai",
        "name": "Minimax",
        "apiHost": "https://api.minimax.chat/v1",
        "anthropicApiHost": "https://api.minimax.chat/anthropic",
        "isAnthropicModel": False,
        "authType": "none",
        "enabled": True,
        "models": [
            {"id": "MiniMax-M3",          "name": "MiniMax M3",          "group": "M3",   "owned_by": "MiniMax", "capabilities": [{"type": "text"}, {"type": "function_calling"}]},
            {"id": "MiniMax-M2.7",        "name": "MiniMax M2.7",        "group": "M2.7", "owned_by": "MiniMax", "capabilities": [{"type": "text"}, {"type": "function_calling"}]},
            {"id": "MiniMax-M2.7-highspeed", "name": "MiniMax M2.7 highspeed", "group": "M2.7", "owned_by": "MiniMax", "capabilities": [{"type": "text"}]},
        ],
        "default_model_id": "MiniMax-M3",
    },
    "deepseek": {
        "env_var": "DEEPSEEK_API_KEY",
        "type": "openai",
        "name": "deepseek",
        "apiHost": "https://api.deepseek.com",
        "anthropicApiHost": "https://api.deepseek.com/anthropic",
        "isAnthropicModel": False,
        "authType": "none",
        "enabled": True,
        "models": [
            {"id": "deepseek-v4-pro",  "name": "DeepSeek V4 Pro",  "group": "DeepSeek", "owned_by": "deepseek", "capabilities": [{"type": "text"}, {"type": "function_calling"}]},
            {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "group": "DeepSeek", "owned_by": "deepseek", "capabilities": [{"type": "text"}]},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner (R1)", "group": "DeepSeek", "owned_by": "deepseek", "capabilities": [{"type": "text"}, {"type": "reasoning"}]},
        ],
        "default_model_id": "deepseek-v4-pro",
    },
    "openai": {
        "env_var": "OPENAI_API_KEY",
        "type": "openai",
        "name": "OpenAI",
        "apiHost": "https://api.openai.com/v1",
        "anthropicApiHost": "",
        "isAnthropicModel": False,
        "authType": "none",
        "enabled": False,
        "models": [
            {"id": "gpt-5",          "name": "GPT 5",          "group": "gpt-5",  "owned_by": "openai",   "capabilities": [{"type": "text"}, {"type": "function_calling"}]},
            {"id": "gpt-5-mini",     "name": "GPT 5 mini",     "group": "gpt-5",  "owned_by": "openai",   "capabilities": [{"type": "text"}, {"type": "function_calling"}]},
            {"id": "gpt-4.1",        "name": "GPT 4.1",        "group": "gpt-4.1","owned_by": "openai",   "capabilities": [{"type": "text"}, {"type": "function_calling"}]},
            {"id": "gpt-4o",         "name": "GPT 4o",         "group": "gpt-4o", "owned_by": "openai",   "capabilities": [{"type": "text"}, {"type": "vision"}, {"type": "function_calling"}]},
            {"id": "o3",             "name": "o3",             "group": "o3",     "owned_by": "openai",   "capabilities": [{"type": "text"}, {"type": "reasoning"}]},
            {"id": "o4-mini",        "name": "o4-mini",        "group": "o4",     "owned_by": "openai",   "capabilities": [{"type": "text"}, {"type": "reasoning"}]},
        ],
        "default_model_id": "gpt-5",
    },
    "openrouter": {
        "env_var": "OPENROUTER_API_KEY",
        "type": "openai",
        "name": "OpenRouter",
        "apiHost": "https://openrouter.ai/api/v1",
        "anthropicApiHost": "",
        "isAnthropicModel": False,
        "authType": "none",
        "enabled": False,
        "models": [
            {"id": "google/gemini-2.5-pro",     "name": "Gemini 2.5 Pro (OR)",     "group": "google",   "owned_by": "google",    "capabilities": [{"type": "text"}, {"type": "function_calling"}]},
            {"id": "google/gemini-2.5-flash",   "name": "Gemini 2.5 Flash (OR)",   "group": "google",   "owned_by": "google",    "capabilities": [{"type": "text"}, {"type": "function_calling"}]},
            {"id": "deepseek/deepseek-chat",    "name": "DeepSeek V3 (OR)",        "group": "deepseek", "owned_by": "deepseek",  "capabilities": [{"type": "text"}]},
            {"id": "anthropic/claude-sonnet-4-5","name": "Claude Sonnet 4.5 (OR)", "group": "anthropic","owned_by": "anthropic", "capabilities": [{"type": "text"}, {"type": "function_calling"}]},
        ],
        "default_model_id": "google/gemini-2.5-flash",
    },
    "gemini": {
        "env_var": "GEMINI_API_KEY",
        "type": "gemini",
        "name": "Gemini",
        "apiHost": "https://generativelanguage.googleapis.com",
        "anthropicApiHost": "",
        "isAnthropicModel": False,
        "authType": "none",
        "enabled": False,
        "models": [
            {"id": "gemini-2.5-pro",   "name": "Gemini 2.5 Pro",   "group": "Gemini 2.5", "owned_by": "google", "capabilities": [{"type": "text"}, {"type": "vision"}, {"type": "function_calling"}]},
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "group": "Gemini 2.5", "owned_by": "google", "capabilities": [{"type": "text"}, {"type": "vision"}, {"type": "function_calling"}]},
        ],
        "default_model_id": "gemini-2.5-flash",
    },
    "grok": {
        "env_var": "XAI_API_KEY",
        "type": "openai",
        "name": "Grok",
        "apiHost": "https://api.x.ai/v1",
        "anthropicApiHost": "",
        "isAnthropicModel": False,
        "authType": "none",
        "enabled": False,
        "models": [
            {"id": "grok-4",   "name": "Grok 4",   "group": "Grok", "owned_by": "xai", "capabilities": [{"type": "text"}, {"type": "function_calling"}]},
            {"id": "grok-3",   "name": "Grok 3",   "group": "Grok", "owned_by": "xai", "capabilities": [{"type": "text"}]},
            {"id": "grok-3-mini", "name": "Grok 3 Mini", "group": "Grok", "owned_by": "xai", "capabilities": [{"type": "text"}]},
        ],
        "default_model_id": "grok-4",
    },
    "github": {
        "env_var": "GITHUB_TOKEN",
        "type": "openai",
        "name": "GitHub Models",
        "apiHost": "https://models.inference.ai.azure.com",
        "anthropicApiHost": "",
        "isAnthropicModel": False,
        "authType": "none",
        "enabled": False,
        "models": [
            {"id": "gpt-4o", "name": "OpenAI GPT-4o", "group": "OpenAI", "owned_by": "openai", "capabilities": [{"type": "text"}, {"type": "vision"}]},
        ],
        "default_model_id": "gpt-4o",
    },
    # ---- Local gateway / aggregator providers (no upstream key in env) ----
    "new-api": {
        # Canonical new-api (QuantumNous/new-api) provider. The user
        # generates the token in the new-api admin UI after
        # Start-NewAPI.ps1 has started the stack; the token lands in
        # Windows User env as NEWAPI_API_KEY. Models are pulled
        # dynamically from new-api's /v1/models, so the catalog
        # intentionally has no model list.
        "env_var": "NEWAPI_API_KEY",
        "type": "new-api",
        "name": "New API",
        "apiHost": "http://127.0.0.1:3000",
        "anthropicApiHost": "http://127.0.0.1:3000",
        "isAnthropicModel": False,
        "authType": "none",
        "enabled": False,
        "models": [],
        "default_model_id": "",
        "dynamic_models": True,
    },
}


def user_env(name: str) -> str:
    """Read an env var, falling back to the Windows User registry hive.

    Returns '' when the var is unset in both process env and the User
    registry. NEVER raises.
    """
    val = os.environ.get(name) or ""
    if val:
        return val
    if os.name == "nt":
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
                val, _ = winreg.QueryValueEx(k, name)
                return str(val or "")
        except OSError:
            return ""
    return ""


def backup_cherry() -> Path:
    """Snapshot Data/ and the LDB so a botched injection can be rolled back."""
    ts = time.strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_ROOT / f"cherry-providers-{ts}"
    dest.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []
    for src in (
        CHERRY_ROOT / "config.json",
        CHERRY_ROOT / "Local State",
        CHERRY_ROOT / "Preferences",
        DATA_DIR / "agents.db",
    ):
        if not src.exists():
            continue
        target = dest / src.name
        if src.is_dir():
            shutil.copytree(src, target, dirs_exist_ok=True)
        else:
            shutil.copy2(src, target)
        digest = sha256(target.read_bytes() if target.is_file() else b"<dir>").hexdigest()
        manifest.append({"path": str(src), "backup": str(target), "sha256": digest, "bytes": target.stat().st_size if target.is_file() else None})
    if LEVELDB.exists():
        shutil.copytree(LEVELDB, dest / "leveldb", dirs_exist_ok=True)
    (dest / "SHA256MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return dest


def build_provider(provider_id: str, spec: dict) -> dict:
    """Build a Cherry Provider object using the v1.9.12 schema.

    The schema mirrors src/renderer/src/types/provider.ts Provider:
      {id, type, name, apiKey, apiHost, anthropicApiHost,
       isAnthropicModel, models[], enabled, isSystem, authType, notes}
    """
    models = []
    for m in spec["models"]:
        models.append(
            {
                "id": m["id"],
                "name": m["name"],
                "provider": provider_id,
                "group": m["group"],
                "owned_by": m.get("owned_by", provider_id),
                "capabilities": m.get("capabilities", [{"type": "text"}]),
            }
        )
    return {
        "id": provider_id,
        "type": spec["type"],
        "name": spec["name"],
        "apiKey": "",  # filled in by the injector, never written to disk here
        "apiHost": spec["apiHost"],
        "anthropicApiHost": spec.get("anthropicApiHost", ""),
        "isAnthropicModel": spec.get("isAnthropicModel", False),
        "models": models,
        "enabled": spec.get("enabled", True),
        "isSystem": True,
        "authType": spec.get("authType", "none"),
        "notes": {
            "agentcore_import": {
                "env_var": spec["env_var"],
                "default_model_id": spec.get("default_model_id", ""),
                "imported_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }
        },
    }


def build_env_resolver() -> dict[str, str]:
    """Map provider_id -> env var name ONLY for present keys. NO values."""
    present: dict[str, str] = {}
    for provider_id, spec in PROVIDER_CATALOG.items():
        if user_env(spec["env_var"]):
            present[provider_id] = spec["env_var"]
    return present


def build_payload(present_keys: dict[str, str]) -> dict:
    """Build the canonical import payload.

    The shape mirrors Cherry's llm slice exactly (see
    src/renderer/src/store/llm.ts) so the Node injector can merge
    directly into the existing `persist:cherry-studio.llm` object.
    """
    providers: list[dict] = []
    api_keys: dict[str, str] = {}  # provider_id -> env_var; values resolved at inject time
    for provider_id in present_keys.keys():
        spec = PROVIDER_CATALOG[provider_id]
        providers.append(build_provider(provider_id, spec))
        api_keys[provider_id] = present_keys[provider_id]

    # Default model routing per agentcore policy.
    primary = "minimax" if "minimax" in present_keys else next(iter(present_keys.keys()), "")
    secondary = "deepseek" if "deepseek" in present_keys else None
    if not primary:
        raise RuntimeError("no present_keys passed")

    primary_default = PROVIDER_CATALOG[primary]["default_model_id"]
    secondary_default = PROVIDER_CATALOG[secondary]["default_model_id"] if secondary else ""

    return {
        "schema": "agentcore.cherry.providers.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "cherry_version_target": "1.9.12",
        "persist_key": "persist:cherry-studio",
        "slice": "llm",
        "providers": providers,
        "api_keys_env": api_keys,
        "defaultModel": f"{primary}:{primary_default}",
        "topicNamingModel": f"{primary}:{PROVIDER_CATALOG[primary]['models'][2]['id'] if len(PROVIDER_CATALOG[primary]['models']) > 2 else PROVIDER_CATALOG[primary]['models'][0]['id']}",
        "translateModel": f"{primary}:{primary_default}",
        "quickModel": (f"{secondary}:{PROVIDER_CATALOG[secondary]['models'][1]['id']}" if secondary else f"{primary}:{PROVIDER_CATALOG[primary]['models'][0]['id']}"),
        "policy_notes": {
            "primary_provider": primary,
            "primary_model": primary_default,
            "secondary_provider": secondary or "",
            "secondary_model": secondary_default,
            "rule": "All MCP traffic flows through agentcore-gateway; native Cherry RAG enabled; native Cherry memory disabled.",
        },
    }


def cherry_running() -> bool:
    lock = CHERRY_ROOT / "lockfile"
    if lock.exists():
        return True
    if os.name == "nt":
        import subprocess

        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq Cherry Studio.exe"],
            text=True,
            errors="replace",
        )
        return "Cherry Studio.exe" in out
    return False


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--print-models", action="store_true", help="print the catalog of model IDs after writing the import artifact")
    args = p.parse_args()

    if not CHERRY_ROOT.is_dir():
        print("ERROR: CherryStudio AppData root not found:", CHERRY_ROOT)
        return 2
    if cherry_running():
        print("ERROR: Cherry Studio is running. Fully quit it, then re-run this script.")
        return 3

    backup = backup_cherry()
    print(f"backup={backup}")

    present = build_env_resolver()
    if not present:
        print("ERROR: no provider API keys present in Windows User env. Set at least MINIMAX_API_KEY.")
        return 4

    payload = build_payload(present)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMPORT_ARTIFACT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote_import_artifact={IMPORT_ARTIFACT}")
    print(f"providers={list(present.keys())}")
    print(f"defaultModel={payload['defaultModel']}")
    print(f"topicNamingModel={payload['topicNamingModel']}")
    print(f"translateModel={payload['translateModel']}")
    print(f"quickModel={payload['quickModel']}")
    if secondary := payload["policy_notes"]["secondary_provider"]:
        print(f"secondary={secondary}:{payload['policy_notes']['secondary_model']}  (available via the model dropdown)")
    if args.print_models:
        for pid in present.keys():
            print(f"  {pid}: {[m['id'] for m in PROVIDER_CATALOG[pid]['models']]}")
    print()
    print("NEXT STEP: run the companion injector to write the providers into Cherry's Local Storage leveldb:")
    print(r"  cd D:\github\agentcore-control-plane\scripts\cherry\_node_workspace")
    print("  node ..\\inject_cherry_providers.js --confirm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
