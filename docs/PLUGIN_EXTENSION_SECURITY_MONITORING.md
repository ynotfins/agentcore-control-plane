# Plugin And Extension Security Monitoring

Generated: 2026-06-26

AgentCore needs early warning when IDE plugins, MCP wrappers, skills, or extensions change outside source control.

## Scope

The monitor covers:

- Codex plugin cache and skills
- Cursor and VS Code extension roots
- OpenClaw plugin, skill, and wrapper roots
- MiniMax and Mavis MCP or extension roots where present
- local MCP wrappers used by AgentCore clients
- newly changed executable scripts in relevant user-owned roots

## Default Behavior

The scanner is report-only. It must not delete, quarantine, disable, patch, or rewrite plugins/extensions automatically.

It records:

- root scanned
- files inspected
- recent file changes
- suspicious pattern labels
- high-risk executable/script locations
- baseline availability
- next recommended action

It must not record:

- secret values
- auth blobs
- bearer tokens
- cookie contents
- private keys
- raw credential files

## High-Risk Indicators

Examples of indicators that require review:

- encoded command execution
- security-tool disabling commands
- recursive destructive deletes
- suspicious credential-file reads
- startup persistence changes
- broad process termination
- silent remote script download and execution
- unexpected executable changes inside plugin or extension roots

## Validation

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCorePluginExtensionSecurity.ps1
```

The first run may warn because no baseline exists yet. A warning is not a cleanup instruction; it is a prompt to review and approve a baseline once the surface is known-good.

## First-Pass Review Items

The first tuned scan currently reports two high review findings for PowerShell encoded command usage in:

- `C:\Users\ynotf\.mavis\bin\mavis-trash.js`
- `C:\Users\ynotf\.minimax\bin\mavis-trash.js`

These are not currently treated as proof of hostile behavior. They remain high review items until MiniMax/Mavis helper behavior is baseline-approved.
