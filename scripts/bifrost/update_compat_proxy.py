#!/usr/bin/env python3
"""Update C:\\Users\\ynotf\\.config\\tunnel-client\\agentcore-mcp-compat-proxy.cjs to enforce BIFROST_MCP_VK_CHATGPT."""

from pathlib import Path

PROXY_PATH = Path(r"C:\Users\ynotf\.config\tunnel-client\agentcore-mcp-compat-proxy.cjs")

PROXY_CODE = """const http = require("node:http");

const listenHost = process.env.AGENTCORE_COMPAT_HOST || "127.0.0.1";
const listenPort = Number(process.env.AGENTCORE_COMPAT_PORT || "18081");
const targetBase = new URL(process.env.AGENTCORE_BIFROST_TARGET || "http://127.0.0.1:8080");
const publicBase = process.env.AGENTCORE_COMPAT_PUBLIC_BASE || `http://${listenHost}:${listenPort}`;

// === PATH ALLOWLIST: Only these paths are permitted from the ChatGPT tunnel ===
// Anything else returns 403 Forbidden.
const ALLOWED_PATHS = [
  "/mcp",
  "/.well-known/oauth-protected-resource",
  "/.well-known/oauth-protected-resource/mcp",
  "/.well-known/oauth-authorization-server",
  "/.well-known/openid-configuration",
  "/healthz",
  "/readyz",
];

// Prefixes that are ALWAYS denied (even if matching an allowed path)
const DENIED_PREFIXES = [
  "/api/",
  "/workspace/",
  "/logs",
  "/admin",
  "/dashboard",
  "/v1/",            // LLM provider inference endpoints
  "/ui/",
  "/internal/",
];

function isAllowed(pathname) {
  // Check denied prefixes first (overrides)
  for (const prefix of DENIED_PREFIXES) {
    if (pathname.startsWith(prefix)) return false;
  }
  // Must be exactly in allowlist
  return ALLOWED_PATHS.includes(pathname);
}

const protectedResourceMetadata = {
  resource: `${publicBase}/mcp`,
  authorization_servers: [publicBase],
  scopes_supported: [],
  bearer_methods_supported: ["header"],
};

const authorizationServerMetadata = {
  issuer: publicBase,
  authorization_endpoint: `${publicBase}/oauth/authorize`,
  token_endpoint: `${publicBase}/oauth/token`,
  registration_endpoint: `${publicBase}/oauth/register`,
  response_types_supported: ["code"],
  grant_types_supported: ["authorization_code", "refresh_token"],
  code_challenge_methods_supported: ["S256"],
};

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    "content-type": "application/json",
    "content-length": Buffer.byteLength(body),
    "cache-control": "no-store",
  });
  res.end(body);
}

function sendText(res, status, text) {
  res.writeHead(status, {
    "content-type": "text/plain; charset=utf-8",
    "content-length": Buffer.byteLength(text),
    "cache-control": "no-store",
  });
  res.end(text);
}

function stripHopByHopHeaders(headers) {
  const clean = { ...headers };
  for (const key of [
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailer", "transfer-encoding", "upgrade",
  ]) {
    delete clean[key];
  }
  // Caller credentials are never eligible for forwarding. The proxy has one
  // dedicated least-privilege identity and fails closed if it is unavailable.
  delete clean.authorization;
  clean.host = targetBase.host;

  // STRICT ENFORCEMENT: Always use BIFROST_MCP_VK_CHATGPT.
  // Never fall back to BIFROST_MCP_VIRTUAL_KEY, builder, operator, or any other virtual key.
  const vkChatGPT = process.env.BIFROST_MCP_VK_CHATGPT;
  if (vkChatGPT) {
    clean.authorization = `Bearer ${vkChatGPT}`;
  } else {
    console.error(JSON.stringify({ level: "error", message: "CRITICAL: BIFROST_MCP_VK_CHATGPT missing from environment!" }));
    return null;
  }

  return clean;
}

const server = http.createServer((req, res) => {
  const requestUrl = new URL(req.url || "/", publicBase);
  const pathname = requestUrl.pathname;

  // Serve well-known metadata locally (no proxy needed)
  if (req.method === "GET" && (
    pathname === "/.well-known/oauth-protected-resource" ||
    pathname === "/.well-known/oauth-protected-resource/mcp"
  )) {
    return sendJson(res, 200, protectedResourceMetadata);
  }

  if (req.method === "GET" && (
    pathname === "/.well-known/oauth-authorization-server" ||
    pathname === "/.well-known/openid-configuration"
  )) {
    return sendJson(res, 200, authorizationServerMetadata);
  }

  if (pathname.startsWith("/oauth/")) {
    return sendText(res, 501, "OAuth endpoints are metadata-only for this no-auth ChatGPT tunnel.");
  }

  // Synthetic health endpoints
  if (req.method === "GET" && pathname === "/healthz") {
    return sendText(res, 200, "ok");
  }
  if (req.method === "GET" && pathname === "/readyz") {
    return process.env.BIFROST_MCP_VK_CHATGPT
      ? sendText(res, 200, "ok")
      : sendText(res, 503, "not ready");
  }

  // Enforce path allowlist
  if (!isAllowed(pathname)) {
    console.error(JSON.stringify({ level: "warn", path: pathname, action: "denied", reason: "not_in_allowlist" }));
    return sendText(res, 403, "Forbidden: this path is not permitted through the AgentCore ChatGPT compatibility proxy.");
  }

  // Forward allowed paths to Bifrost
  const targetUrl = new URL(req.url || "/", targetBase);
  const upstreamHeaders = stripHopByHopHeaders(req.headers);
  if (!upstreamHeaders) {
    return sendText(res, 503, "ChatGPT gateway identity is unavailable.");
  }
  const proxyRequest = http.request(
    {
      protocol: targetUrl.protocol,
      hostname: targetUrl.hostname,
      port: targetUrl.port || 80,
      method: req.method,
      path: targetUrl.pathname,
      headers: upstreamHeaders,
    },
    (proxyResponse) => {
      res.writeHead(proxyResponse.statusCode || 502, proxyResponse.headers);
      proxyResponse.pipe(res);
    },
  );

  proxyRequest.on("error", (error) => {
    sendText(res, 502, `AgentCore MCP proxy upstream error: ${error.message}`);
  });

  req.pipe(proxyRequest);
});

server.listen(listenPort, listenHost, () => {
  console.log(JSON.stringify({
    status: "listening",
    listen: `${listenHost}:${listenPort}`,
    target: targetBase.toString(),
    metadata: `${publicBase}/.well-known/oauth-protected-resource/mcp`,
    allowed_paths: ALLOWED_PATHS,
    denied_prefixes: DENIED_PREFIXES,
  }));
});
"""

def main() -> None:
    PROXY_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROXY_PATH.write_text(PROXY_CODE, encoding="utf-8")
    print(f"Updated {PROXY_PATH}")

if __name__ == "__main__":
    main()
