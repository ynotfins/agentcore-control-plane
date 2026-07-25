"""Deeper sanitized inspection of Cherry memory/openclaw/knowledge/assistants MCP fields."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

NODE = Path(__file__).resolve().parents[1] / "cherry" / "_node_workspace"
SCRIPT = NODE / "_tmp_dump2.js"

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
function summarizeDeep(val, depth) {
  if (val == null) return val;
  if (typeof val !== 'object') return typeof val === 'string' && val.length > 120 ? `str:${val.length}` : val;
  if (Array.isArray(val)) {
    return { type: 'array', length: val.length, sample: val.slice(0, 3).map((x) => summarizeDeep(x, depth + 1)) };
  }
  if (depth > 2) return { type: 'object', keys: Object.keys(val).slice(0, 40) };
  const out = {};
  for (const [k, v] of Object.entries(val)) {
    if (/key|token|secret|password|auth|bearer|api/i.test(k) && typeof v === 'string' && v.length > 0) {
      out[k] = `redacted_len=${v.length}`;
      continue;
    }
    out[k] = summarizeDeep(v, depth + 1);
  }
  return out;
}
(async () => {
  const db = new Level(LDB, { valueEncoding: 'binary' });
  await db.open();
  for await (const [k, v] of db.iterator()) {
    const keyStr = k.toString('utf8');
    if (!keyStr.includes('persist:cherry-studio')) continue;
    const body = v[0] === 0x00 ? v.slice(1) : v;
    const obj = JSON.parse(body.toString('utf16le'));
    const memory = parseMaybe(obj.memory);
    const openclaw = parseMaybe(obj.openclaw);
    const knowledge = parseMaybe(obj.knowledge);
    const settings = parseMaybe(obj.settings) || {};
    const assistants = parseMaybe(obj.assistants);
    // Find any assistant with MCP fields
    let assistList = [];
    if (Array.isArray(assistants)) assistList = assistants;
    else if (assistants && Array.isArray(assistants.assistants)) assistList = assistants.assistants;
    const mcpFieldScan = assistList.slice(0, 5).map((a) => ({
      id: a.id,
      name: a.name,
      keys: Object.keys(a).filter((x) => /mcp|tool|skill|memory|knowledge|prompt|model/i.test(x)),
      mcpServers: a.mcpServers,
      mcpServerIds: a.mcpServerIds,
      enableMCP: a.enableMCP,
      knowledgeRecognition: a.knowledgeRecognition,
    }));
    // settings keys containing memory
    const allSettingsKeys = Object.keys(settings);
    const memKeys = allSettingsKeys.filter((x) => /memory|Memory|global/i.test(x));
    console.log(JSON.stringify({
      memory: summarizeDeep(memory, 0),
      openclaw: summarizeDeep(openclaw, 0),
      knowledge: summarizeDeep(knowledge, 0),
      settings_memory_keys: Object.fromEntries(memKeys.map((k) => [k, settings[k]])),
      settings_has_globalMemoryEnabled: Object.prototype.hasOwnProperty.call(settings, 'globalMemoryEnabled'),
      defaultAgent: settings.defaultAgent,
      assistant_mcp_scan: mcpFieldScan,
      assistant_keys_union: Array.from(new Set(assistList.flatMap((a) => Object.keys(a)))).sort(),
    }, null, 2));
  }
  await db.close();
})().catch((e) => { console.error(e); process.exit(1); });
"""


def main() -> int:
    SCRIPT.write_text(JS, encoding="utf-8")
    r = subprocess.run(["node", str(SCRIPT)], cwd=str(NODE), capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
