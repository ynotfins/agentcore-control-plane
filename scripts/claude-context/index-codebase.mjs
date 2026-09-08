#!/usr/bin/env node
/**
 * One-shot MCP client: call index_codebase on @zilliz/claude-context-mcp.
 * Secrets come only from process environment / Windows User EVs (via launcher).
 */
import { spawn } from 'node:child_process';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { existsSync } from 'node:fs';

const root = process.argv[2] || process.cwd();
const launcher = join(homedir(), '.agentcore', 'claude-context-mcp-launch.cmd');
const cmd = existsSync(launcher) ? launcher : 'npx';
const args = existsSync(launcher) ? [] : ['-y', '@zilliz/claude-context-mcp@latest'];

function encode(msg) {
  const body = Buffer.from(JSON.stringify(msg), 'utf8');
  return Buffer.concat([
    Buffer.from('Content-Length: ' + body.length + '\r\n\r\n', 'utf8'),
    body,
  ]);
}

function createFramedReader(stream, onMessage) {
  let buf = Buffer.alloc(0);
  stream.on('data', (chunk) => {
    buf = Buffer.concat([buf, chunk]);
    while (true) {
      const headerEnd = buf.indexOf('\r\n\r\n');
      if (headerEnd < 0) return;
      const header = buf.slice(0, headerEnd).toString('utf8');
      const match = /Content-Length:\s*(\d+)/i.exec(header);
      if (!match) {
        buf = buf.slice(headerEnd + 4);
        continue;
      }
      const len = Number(match[1]);
      const start = headerEnd + 4;
      if (buf.length < start + len) return;
      const body = buf.slice(start, start + len).toString('utf8');
      buf = buf.slice(start + len);
      onMessage(JSON.parse(body));
    }
  });
}

const child = spawn(cmd, args, { stdio: ['pipe', 'pipe', 'inherit'], env: process.env, shell: true });
let nextId = 1;
const pending = new Map();

createFramedReader(child.stdout, (msg) => {
  if (msg.id != null && pending.has(msg.id)) {
    const { resolve } = pending.get(msg.id);
    pending.delete(msg.id);
    resolve(msg);
  }
});

function request(method, params) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error('timeout ' + method)), 600000);
    pending.set(id, { resolve: (m) => { clearTimeout(t); resolve(m); } });
    child.stdin.write(encode({ jsonrpc: '2.0', id, method, params }));
  });
}

function notify(method, params) {
  child.stdin.write(encode({ jsonrpc: '2.0', method, params }));
}

async function main() {
  console.log('[index] starting for', root);
  await request('initialize', {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: { name: 'agentcore-claude-context-indexer', version: '1.0.0' },
  });
  notify('notifications/initialized');
  const result = await request('tools/call', {
    name: 'index_codebase',
    arguments: { path: root },
  });
  console.log(JSON.stringify(result, null, 2));
  child.stdin.end();
  child.kill();
}

main().catch((err) => {
  console.error(String(err && err.stack || err));
  process.exit(1);
});
