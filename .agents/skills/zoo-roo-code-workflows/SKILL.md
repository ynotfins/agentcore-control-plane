---
name: zoo-roo-code-workflows
description: Use when installing or configuring Zoo Code/Roo Code, Zoo Gateway, or workflows that extend Zoo/Roo behavior across development hosts.
---

# Zoo/Roo Code Workflows

Treat Zoo Code/Roo Code as a VS Code-family client extension. It is neither a Bifrost upstream nor a standalone STDIO or HTTP MCP server.

## Route by host capability

- Install the extension directly only after the exact host proves VS Code extension or VSIX compatibility. Cursor is currently proven.
- Do not claim that Codex, Zed, LobeHub, OpenHands, Eigent, Reasonix, Cherry, Open Interpreter, or an unknown Zcode host can install the extension.
- For other hosts, provide the existing `agentcore-gateway` tools plus this workflow skill or generated host rules. This transfers workflow guidance only; it does not reproduce Zoo/Roo UI, modes, provider or account state, or the side panel.
- Treat Zoo Gateway as model inference and provider routing, not as an MCP server.

Preserve exactly one `agentcore-gateway` entry. Never invent a Zoo endpoint, add duplicate MCP entries, expose a public tunnel, access NFA, or route through Swarm. Use Code Mode for shared heavy MCP tools exposed through Bifrost discovery rather than adding direct per-tool MCP entries.

## Proof checklist

Before reporting an installation or cross-host workflow as working, capture:

- exact host identity and version;
- exact extension ID and version;
- successful extension activation in that host;
- successful execution in a fresh task, not only the current session;
- persistence after a full host restart.

If any item is unproven, report it as unverified and stop before claiming installation or parity.
