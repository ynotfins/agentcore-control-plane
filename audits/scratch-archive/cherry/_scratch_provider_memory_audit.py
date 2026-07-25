"""Sanitized dump of Cherry persist memory + llm provider/model health."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

CHERRY_PKG = Path(__file__).resolve().parent
DUMP_JS = CHERRY_PKG / "_node_workspace" / "_tmp_provider_memory_dump.js"

DUMP_JS.write_text(
    r"""
const path = require('path');
const { Level } = require('level');
const LDB = path.join(process.env.APPDATA, 'CherryStudio', 'Local Storage', 'leveldb');
function parseMaybe(x) {
  if (typeof x === 'string') {
    try { return JSON.parse(x); } catch { return x; }
  }
  return x;
}
function red(v) {
  if (typeof v === 'string' && v.length > 0) return `redacted_len=${v.length}`;
  return v;
}
(async () => {
  const db = new Level(LDB, { valueEncoding: 'binary' });
  await db.open();
  for await (const [k, v] of db.iterator()) {
    const keyStr = k.toString('utf8');
    if (!keyStr.includes('persist:cherry-studio')) continue;
    const body = v[0] === 0x00 ? v.slice(1) : v;
    const obj = JSON.parse(body.toString('utf16le'));
    const memory = parseMaybe(obj.memory) || {};
    const llm = parseMaybe(obj.llm) || {};
    const providers = Array.isArray(llm.providers) ? llm.providers : [];
    const providerSummary = providers.map((p) => ({
      id: p.id,
      name: p.name,
      type: p.type,
      enabled: p.enabled,
      isSystem: p.isSystem,
      apiHost: p.apiHost ? String(p.apiHost).slice(0, 80) : null,
      hasApiKey: Boolean(p.apiKey && String(p.apiKey).length > 0),
      apiKeyLen: p.apiKey ? String(p.apiKey).length : 0,
      modelCount: Array.isArray(p.models) ? p.models.length : 0,
      modelIdsSample: Array.isArray(p.models)
        ? p.models.slice(0, 8).map((m) => (typeof m === 'string' ? m : m?.id || m?.name || null))
        : [],
    }));
    const cherryin = providers.find((p) => p.id === 'cherryin' || p.name === 'cherryin');
    const openrouter = providers.find((p) => String(p.id || '').toLowerCase() === 'openrouter');
    const defaultModel = llm.defaultModel || llm.defaultModelId || null;
    // memory schema
    const memKeys = Object.keys(memory || {});
    const memProvider = memory.provider;
    const memModel = memory.model || memory.embeddingModel || memory.llmModel;
    console.log(JSON.stringify({
      redux_version: obj._persist && obj._persist.version,
      globalMemoryEnabled: memory.globalMemoryEnabled === true,
      memory_keys: memKeys,
      memory_provider_typeof: typeof memProvider,
      memory_provider: memProvider == null ? memProvider : {
        id: memProvider.id,
        name: memProvider.name,
        keys: Object.keys(memProvider),
        hasApiKey: Boolean(memProvider.apiKey),
      },
      memory_model_fields: {
        model: memory.model ?? null,
        embeddingModel: memory.embeddingModel ?? null,
        llmModel: memory.llmModel ?? null,
        dimensions: memory.dimensions ?? null,
      },
      llm_defaultModel: defaultModel,
      llm_provider_count: providers.length,
      providers: providerSummary,
      cherryin_present: Boolean(cherryin),
      cherryin_enabled: cherryin ? cherryin.enabled : null,
      cherryin_has_key: cherryin ? Boolean(cherryin.apiKey && String(cherryin.apiKey).length) : null,
      cherryin_models_sample: cherryin && Array.isArray(cherryin.models)
        ? cherryin.models.slice(0, 15).map((m) => (typeof m === 'string' ? m : m?.id || m?.name))
        : null,
      openrouter_present: Boolean(openrouter),
      openrouter_enabled: openrouter ? openrouter.enabled : null,
      target_agent_model: 'cherryin:agent/deepseek-v4-pro',
      target_model_base_in_cherryin: cherryin && Array.isArray(cherryin.models)
        ? cherryin.models.some((m) => {
            const id = typeof m === 'string' ? m : (m?.id || m?.name || '');
            return id === 'agent/deepseek-v4-pro' || id.includes('deepseek-v4-pro');
          })
        : false,
    }, null, 2));
  }
  await db.close();
})().catch((e) => { console.error(String(e)); process.exit(1); });
""",
    encoding="utf-8",
)

cwd = CHERRY_PKG / "_node_workspace"
if not (cwd / "node_modules" / "level").is_dir() and not (CHERRY_PKG / "node_modules" / "level").is_dir():
    print("WARN: level module may be missing", file=sys.stderr)

# Prefer _node_workspace then parent
run_cwd = cwd if (cwd / "node_modules").is_dir() else CHERRY_PKG
proc = subprocess.run(["node", str(DUMP_JS)], cwd=str(run_cwd), text=True, capture_output=True)
sys.stdout.write(proc.stdout)
sys.stderr.write(proc.stderr)
raise SystemExit(proc.returncode)
