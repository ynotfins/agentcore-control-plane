# AgentCore core rules (all modes)

- Repo-root `AGENTS.md` wins. Read it first. Never create a nested AGENTS.md.
- Tools: one MCP server only, `agentcore-gateway`. Memory, docs, code navigation, Graphify, and
  database reads all go through it. Never connect to PostgreSQL directly and never ask for a
  database password.
- Library/API facts: `arabold-docs` via the gateway at the exact pinned version. Missing docs:
  run `scrape_docs`, wait for real `search_docs` hits, then answer.
- Secrets: Windows User environment variables only. Never write a key, token, or password into a
  file, log, or chat. No `.env` files.
- Models: all inference goes through OmniRoute at `http://127.0.0.1:20128/v1`. Do not add other
  providers.
- Locked docs (`PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, `BLUEPRINT.md`, `AGENTS.md`, `CLAUDE.md`)
  change only after the operator types `UNLOCK <filename>`. Otherwise write
  `governance/proposals/<date>-<slug>.md` and continue.
- After every completed Code or Debug task, hand off to `doc-master` with the list of changed files.
- Operator is non-technical: report in plain language; never ask them to read code.
