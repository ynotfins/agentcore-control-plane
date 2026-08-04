# Host and Runtime Adapters

One semantic contract does not imply one installation mechanism. Use the native mechanism proven for each host, then validate inside that host.

| Host or runtime | Delivery | Native skill claim |
| --- | --- | --- |
| Cursor | user skill plus generated always-on global rule and signed hooks | supported; restart/fresh task validation required |
| Codex | user open-standard skill plus global `AGENTS.md` and signed hooks | supported; fresh task validation required |
| Claude Code | user `.claude/skills` copy plus global `CLAUDE.md` and signed hooks | supported; native CLI validation required |
| MiniMax Code / Mavis | host skill directory when live host discovery proves it; generated rule remains baseline | installation is not validation |
| Claude Desktop | generated/manual global instructions | do not claim Claude Code filesystem-skill parity |
| Antigravity | generated rule only until native skill discovery is proven | unverified native skill support |
| Open Interpreter CLI | profile/system-message adapter | no native skill claim |
| Cherry Studio | governed agent prompt or its documented workspace skill store | UI/database import and native validation required |
| MiniMax Agent Classic | UI/system-prompt adapter | UI-only until proven otherwise |
| LangGraph production | hash-pinned capsule in Context Engine execution catalog | workflow adapter, not an IDE installation |
| LangGraph Studio | same graph policy in development-only runtime | never production-thread parity |
| SwarmClaw | separate Swarm-owned alignment adapter | never install this AgentCore skill as Swarm authority |

## Certification levels

- `source_ready`: repository skill and references validate.
- `installed_unverified`: exact files are present and hash-matched in the host's supported location.
- `configured_restart_required`: host must restart or open a fresh task.
- `live_validated`: the host invoked the skill and completed its required memory/tool checks.
- `manual_import_pending`, `UI_only_pending`, `unverified`, or `unsupported_with_reason`: accurate stopping states, not failures to conceal.

Do not claim PC-wide parity until every named host has its own evidence at the appropriate level.
