"""Sanitized dump of Cherry persist:cherry-studio MCP/settings (no secrets)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

NODE = Path(__file__).resolve().parents[1] / "cherry" / "_node_workspace"
SCRIPT = NODE / "_tmp_dump.js"

JS = r"""
const path = require('path');
const { Level } = require('level');
const LDB = path.join(process.env.APPDATA, 'CherryStudio', 'Local Storage', 'leveldb');
function parseMaybe(x) {
  if (typeof x === 'string') {
    try { return JSON.parse(x); } catch { return x; }
  }
  return x;
}
(async () => {
  const db = new Level(LDB, { valueEncoding: 'binary' });
  await db.open();
  for await (const [k, v] of db.iterator()) {
    const keyStr = k.toString('utf8');
    if (!keyStr.includes('persist:cherry-studio')) continue;
    const body = v[0] === 0x00 ? v.slice(1) : v;
    const obj = JSON.parse(body.toString('utf16le'));
    const mcp = parseMaybe(obj.mcp) || {};
    const settings = parseMaybe(obj.settings) || {};
    const memory = parseMaybe(obj.memory);
    const assistants = parseMaybe(obj.assistants);
    const agents = parseMaybe(obj.agents);
    const llm = parseMaybe(obj.llm);
    const servers = Array.isArray(mcp.servers) ? mcp.servers : [];
    const out = {
      top_keys: Object.keys(obj).filter((x) => x !== '_persist'),
      mcp_servers: servers.map((s) => {
        const auth = (s.headers && (s.headers.Authorization || s.headers.authorization)) || '';
        return {
          id: s.id,
          name: s.name,
          type: s.type,
          url: s.baseUrl || s.url || null,
          active: s.isActive,
          timeout: s.timeout,
          has_auth_header: !!auth,
          auth_is_env_placeholder: String(auth).includes('${env:'),

          auth_bearer_len: auth ? String(auth).length : 0,
          provider: s.provider || null,
          disabledTools: s.disabledTools || [],
        };
      }),
      memory_related_settings: Object.fromEntries(
        Object.entries(settings).filter(([k]) => /memory|knowledge|trace|developer|mcp/i.test(k))
      ),
      settings_sample_keys: Object.keys(settings).slice(0, 100),
      memory_type: memory == null ? null : Array.isArray(memory) ? 'array:' + memory.length : typeof memory,
      assistants_summary: summarizeAssistants(assistants),
      agents_summary: summarizeAgents(agents),
      llm_provider_ids: llm && llm.providers ? Object.keys(llm.providers || {}).slice(0, 40) : null,
    };
    console.log(JSON.stringify(out, null, 2));
  }
  await db.close();
})().catch((e) => { console.error(e); process.exit(1); });

function summarizeAssistants(a) {
  if (a == null) return null;
  if (Array.isArray(a)) {
    return a.slice(0, 30).map((x) => ({
      id: x.id, name: x.name, type: x.type,
      mcpServers: x.mcpServers || x.mcp || x.enabledMCPs || null,
      knowledgeIds: x.knowledgeIds || null,
      prompt_len: typeof x.prompt === 'string' ? x.prompt.length : (typeof x.systemPrompt === 'string' ? x.systemPrompt.length : null),
    }));
  }
  if (typeof a === 'object') {
    const arr = a.assistants || a.items || null;
    if (Array.isArray(arr)) return summarizeAssistants(arr);
    return { keys: Object.keys(a).slice(0, 40) };
  }
  return typeof a;
}

function summarizeAgents(a) {
  if (a == null) return null;
  if (Array.isArray(a)) {
    return a.slice(0, 30).map((x) => ({
      id: x.id, name: x.name, type: x.type,
      mcpServers: x.mcpServers || x.mcp || x.enabledMCPs || null,
      skills: x.skills || x.enabledSkills || null,
      prompt_len: typeof x.prompt === 'string' ? x.prompt.length : (typeof x.systemPrompt === 'string' ? x.systemPrompt.length : null),
    }));
  }
  if (typeof a === 'object') {
    const arr = a.agents || a.items || null;
    if (Array.isArray(arr)) return summarizeAgents(arr);
    return { keys: Object.keys(a).slice(0, 40) };
  }
  return typeof a;
}
"""

def main() -> int:
    SCRIPT.write_text(JS, encoding="utf-8")
    env = os.environ.copy()
    r = subprocess.run(
        ["node", str(SCRIPT)],
        cwd=str(NODE),
        env=env,
        capture_output=True,
        text=True,
    )
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
