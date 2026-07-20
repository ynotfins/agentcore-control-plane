# Cursor Extension → MCP Replacement Matrix

**Date:** 2026-07-19  
**Scope:** Installed Cursor extensions under `%USERPROFILE%\.cursor\extensions`  
**Policy:** Recommendations only — **no uninstalls performed**  
**Security monitor:** `ops/Test-AgentCorePluginExtensionSecurity.ps1` → report-only (`critical=0`, `high=2` outside Cursor extensions: mavis-trash.js encoded-command patterns)

## Classification legend

| Class | Meaning |
| -- | -- |
| `preserve` | Editor/language/debugger/remote/test/DB UI capability; keep |
| `partial` | Some overlap with AgentCore MCP/gateway tools; keep editor UX, prefer MCP for agent work |
| `full_candidate` | Strong MCP/gateway substitute exists; candidate for future removal after operator review |
| `review` | Duplicate, conflicting, or Swarm/OpenClaw-adjacent; do not auto-remove |
| `no_replacement` | No AgentCore MCP equivalent |

## Python / type-check conflict audit

| Extension | Version | Conflict note | Recommendation |
| -- | -- | -- | -- |
| `ms-python.python` | 2025.6.1 | Core Python language support | **preserve** |
| `ms-python.debugpy` | 2026.6.0 | Debugger UI | **preserve** |
| `anysphere.cursorpyright` | 1.0.10/1.0.12 | Cursor-bundled Pyright | **preserve** (primary typecheck in Cursor) |
| `charliermarsh.ruff` | 2026.62.0 | Lint/format; complements Pyright | **preserve** |
| Pylance | not installed | — | No Pylance/Pyright dual-install conflict detected |

Do **not** install Microsoft Pylance alongside `anysphere.cursorpyright` without an explicit conflict test.

## Matrix (installed)

| Extension ID | Version | Class | AgentCore / MCP substitute | Recommendation |
| -- | -- | -- | -- | -- |
| `aaron-bond.better-comments` | 3.0.2 | no_replacement | — | preserve |
| `ai-dl.enlighter` | 1.0.5 | review | learning overlay; not AgentCore authority | keep unless unused |
| `anysphere.cursorpyright` | 1.0.12 | preserve | — | preserve |
| `anysphere.remote-containers` | 1.0.37 | preserve | — | preserve |
| `anysphere.remote-ssh` | 1.1.11 | preserve | — | preserve |
| `anysphere.remote-wsl` | 1.0.13 | preserve | — | preserve |
| `atom8n.openclaw-atom` | 3.25.58 | review | OpenClaw adjacent; **outside** non-Swarm baseline | do not add to Bifrost; optional uninstall later |
| `bradlc.vscode-tailwindcss` | 0.14.28 | preserve | — | preserve |
| `ChakrounAnas.turbo-console-log` | 3.26.0 | no_replacement | — | preserve if used |
| `charliermarsh.ruff` | 2026.62.0 | preserve | — | preserve |
| `christian-kohler.path-intellisense` | 2.8.0 | no_replacement | — | preserve |
| `cweijan.dbclient-jdbc` / `cweijan.vscode-database-client2` | 1.4.2 / 9.0.2 | preserve | AgentCore forbids normal IDE Postgres credentials; UI client is operator-only | preserve UI; never wire AgentCore DB creds into IDE |
| `DavidAnson.vscode-markdownlint` | 0.61.2 | preserve | — | preserve |
| `dbaeumer.vscode-eslint` | 3.0.34 | preserve | — | preserve |
| `dsznajder.es7-react-js-snippets` | 4.4.3 | no_replacement | — | preserve |
| `EditorConfig.EditorConfig` | 0.18.2 | preserve | — | preserve |
| `esbenp.prettier-vscode` | 12.4.0 | preserve | — | preserve |
| `expo.vscode-expo-tools` | 1.6.3 | preserve | — | preserve |
| `formulahendry.auto-rename-tag` | 0.1.10 | no_replacement | — | preserve |
| `gguf.openclaw` | 0.2.2 | review | OpenClaw; Swarm-exclusion adjacent | do not route AgentCore through it |
| `giga-ai.giga-ai` | 1.13.0 + 1.15.1 | review | Competing memory/context manager vs `agentcore-memory` | **do not uninstall now**; prefer AgentCore memory; consider disable later |
| `github.vscode-github-actions` | 0.32.3 | partial | `github-mcp` deferred in registry | preserve Actions UI |
| `GitHub.vscode-pull-request-github` | 0.120.2 | partial | `github-mcp` deferred | preserve PR UI |
| `google.geminicodeassist` | 2.54.0 + 2.84.0 | review | Competing assistant vs gateway agents | keep for now; do not duplicate MCP |
| `Gruntfuggly.todo-tree` | 0.0.215 | no_replacement | — | preserve |
| `hediet.vscode-drawio` | 1.6.6 | no_replacement | — | preserve |
| `humao.rest-client` | 0.25.0 | partial | HTTP probes via scripts/ops | preserve |
| `lokalise.i18n-ally` | 2.13.1 | preserve | — | preserve |
| `mathiasfrohlich.Kotlin` | 1.7.1 | preserve | — | preserve |
| `mechatroner.rainbow-csv` | 3.24.1 | preserve | — | preserve |
| `mikestead.dotenv` | 1.0.1 | review | AgentCore forbids `.env` secrets; highlighter only | preserve UI; do not create `.env` |
| `ms-azuretools.vscode-containers` / `vscode-docker` | 2.4.5 / 2.0.0 | preserve | Docker mutation remains approval-gated | preserve |
| `ms-playwright.playwright` | 1.1.19 | partial | Bifrost `playwright` MCP active | preserve Test UI; prefer gateway Playwright for agents |
| `ms-python.debugpy` / `ms-python.python` | 2026.6.0 / 2025.6.1 | preserve | — | preserve |
| `ms-vscode.powershell` | 2025.4.0 | preserve | — | preserve |
| `ms-vscode.vscode-typescript-next` | nightly | review | Nightly TS may drift | consider stable TS instead later |
| `msjsdiag.vscode-react-native` | 1.13.0 | preserve | — | preserve |
| `naumovs.color-highlight` | 2.8.0 | no_replacement | — | preserve |
| `PKief.material-icon-theme` | 5.37.0 | no_replacement | — | preserve |
| `px39n.obsidianpreview` | 1.0.19 | partial | Bifrost `obsidian-vault` MCP | preserve preview; vault writes via governed MCP |
| `qwtel.sqlite-viewer` | 26.2.5 | preserve | — | preserve |
| `rangav.vscode-thunder-client` | 2.40.12 | preserve | — | preserve |
| `redhat.java` + Java pack/debug/test/maven/gradle/dependency | various | preserve | — | preserve Java toolchain |
| `redhat.vscode-yaml` | 1.24.0 | preserve | — | preserve |
| `sleistner.vscode-fileutils` | 3.10.3 | no_replacement | filesystem MCP is project-scoped | preserve editor utils |
| `SonarSource.sonarlint-vscode` | 4.33.0 | preserve | — | preserve |
| `streetsidesoftware.code-spell-checker` | 4.5.6 | preserve | — | preserve |
| `usernamehw.errorlens` | 3.26.0 | preserve | — | preserve |
| `vincaslt.highlight-matching-tag` | 0.10.1 | no_replacement | — | preserve |
| `vitest.explorer` | 1.50.4 | preserve | — | preserve |
| `wayou.vscode-todo-highlight` | 1.0.5 | no_replacement | overlaps Todo Tree | optional consolidate later |
| `wix.vscode-import-cost` | 3.3.0 | no_replacement | — | preserve |
| `YoavBls.pretty-ts-errors` | 0.8.7 | preserve | — | preserve |
| `yzhang.markdown-all-in-one` | 3.6.2 | preserve | — | preserve |

## AgentCore MCP coverage (for agents, not editor replacement)

Prefer via `agentcore-gateway`: `agentcore-memory`, `agentcore-project-router`, `serena`, `depwire`, `arabold-docs`, `sequential-thinking`, `context-fabric`, `filesystem` (bounded), `obsidian-vault`, `playwright`, `tentra`. Dormant/deferred: `openrouter`, `github-mcp`.

## Actions taken

- None uninstall/disable.
- Inventory + recommendations only (Gate E).
