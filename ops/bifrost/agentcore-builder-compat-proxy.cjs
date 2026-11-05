'use strict';

const http = require('node:http');
const path = require('node:path');
const { execFile } = require('node:child_process');
const { timingSafeEqual } = require('node:crypto');

const host = '127.0.0.1';
const port = Number(process.env.AGENTCORE_BUILDER_COMPAT_PORT || '18082');
const target = new URL('http://127.0.0.1:8080');
const virtualKey = process.env.BIFROST_MCP_VIRTUAL_KEY;
const resolver = path.join(__dirname, 'Resolve-AgentCoreBuilderCaller.ps1');
const powershell = 'C:\\Program Files\\PowerShell\\7\\pwsh.exe';
const socketIdentities = new WeakMap();

if (!virtualKey) {
  process.stderr.write('[builder-compat-proxy] required User-scope gateway identity is unavailable\n');
  process.exit(1);
}

function cleanHeaders(headers) {
  const result = { ...headers };
  for (const name of ['connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailer', 'transfer-encoding', 'upgrade']) {
    delete result[name];
  }
  delete result.authorization;
  result.authorization = `Bearer ${virtualKey}`;
  result.host = target.host;
  return result;
}

function hasValidAuthorization(headers) {
  const provided = headers.authorization;
  if (typeof provided !== 'string') return false;
  const expected = `Bearer ${virtualKey}`;
  const providedBytes = Buffer.from(provided, 'utf8');
  const expectedBytes = Buffer.from(expected, 'utf8');
  return providedBytes.length === expectedBytes.length && timingSafeEqual(providedBytes, expectedBytes);
}

function resolveSocketIdentity(socket) {
  const existing = socketIdentities.get(socket);
  if (existing) return existing;
  const identity = new Promise((resolve, reject) => {
    const remoteAddress = socket.remoteAddress;
    const clientPort = Number(socket.remotePort);
    if ((remoteAddress !== '127.0.0.1' && remoteAddress !== '::ffff:127.0.0.1') || !Number.isInteger(clientPort)) {
      reject(new Error('non_loopback_or_invalid_peer'));
      return;
    }
    execFile(
      powershell,
      ['-NoProfile', '-NonInteractive', '-File', resolver, '-ServerPort', String(port), '-ClientPort', String(clientPort)],
      { windowsHide: true, timeout: 5000, maxBuffer: 16 * 1024, encoding: 'utf8' },
      (error, stdout) => {
        if (error) {
          reject(new Error('caller_identity_unresolved'));
          return;
        }
        try {
          const result = JSON.parse(stdout);
          if (result.allowed !== true || typeof result.client !== 'string') throw new Error('invalid_result');
          resolve(result);
        } catch {
          reject(new Error('caller_identity_invalid'));
        }
      },
    );
  });
  socketIdentities.set(socket, identity);
  return identity;
}

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url || '/', `http://${host}:${port}`);
  if (request.method === 'GET' && url.pathname === '/healthz') {
    response.writeHead(200, { 'content-type': 'text/plain' });
    response.end('ok');
    return;
  }
  if (url.pathname !== '/mcp') {
    response.writeHead(403, { 'content-type': 'text/plain' });
    response.end('forbidden');
    return;
  }
  if (!hasValidAuthorization(request.headers)) {
    try {
      const identity = await resolveSocketIdentity(request.socket);
      process.stderr.write(
        `[builder-compat-proxy] admitted client=${identity.client} client_pid=${identity.client_pid} matched_pid=${identity.matched_pid}\n`,
      );
    } catch {
      response.writeHead(403, { 'content-type': 'text/plain' });
      response.end('caller identity denied');
      return;
    }
  }
  const upstream = http.request({
    protocol: target.protocol,
    hostname: target.hostname,
    port: target.port,
    method: request.method,
    path: `${url.pathname}${url.search}`,
    headers: cleanHeaders(request.headers),
  }, (upstreamResponse) => {
    response.writeHead(upstreamResponse.statusCode || 502, upstreamResponse.headers);
    upstreamResponse.pipe(response);
  });
  upstream.on('error', () => {
    if (!response.headersSent) response.writeHead(502, { 'content-type': 'text/plain' });
    response.end('gateway unavailable');
  });
  request.on('aborted', () => upstream.destroy());
  request.pipe(upstream);
});

server.listen(port, host, () => process.stderr.write(`[builder-compat-proxy] listening ${host}:${port}\n`));
