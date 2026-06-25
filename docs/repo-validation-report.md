# Repo Validation Report

Generated: 2026-06-25T00:59:36.4614872Z
Root: `D:\MCP-Control-Plane`
Overall: PASS

- PASS - core governance files: missing=none
- PASS - json parse: all json parsed
- PASS - no hard-coded secrets: no secret-like literals found
- PASS - correct env references only: all placeholder env vars are allowlisted
- PASS - Context7 retired from managed routing: context7 is not active or emitted
- PASS - correct Artiforge naming: artiforge is the only current managed name
- PASS - Composio quarantined: supervisor and registry lifecycle are quarantined; renderers do not emit composio
- PASS - global-memory-gateway primary: gateway is critical/active and raw Mem0 is quarantined
- PASS - critical tool set: missing=none
- PASS - vendored MCP installs: arabold-docs and context-fabric entrypoints exist
- PASS - managed files re-locked: all managed files are read-only
