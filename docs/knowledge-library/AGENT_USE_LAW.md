# Agent Use Law — Knowledge Library

**Status:** operator-locked. Every AgentCore / enrolled non-Swarm agent must obey this.  
**Approval:** `AUTH-2026-11-01-KNOWLEDGE-LIBRARY-AUTHORITY`

Agents may not invent architecture, UI structure, or boilerplate from training memory when this library or Arabold already holds the pattern.

---

## 1. Two searches, two jobs

| Question | Tool | Filters / pin |
| --- | --- | --- |
| Official library or API fact at a version | `arabold-docs` `search_docs` / `find_version` | exact `library@version` |
| How we scaffold or structure Flutter, Android Compose, Refine, Next.js/T3, React/shadcn, FastAPI | `agentcore-memory` `docs_search` or `retrieve_context` | `asset_type=boilerplate` + `framework=...` |
| This project’s decisions, evidence, chronology | `retrieve_context` / `expand_source` | project session — not a substitute for boilerplate |
| Missing official docs | `arabold-docs` `scrape_docs` then wait | do not keep working from memory |

Never invent a tool named `hybrid_retrieve_documents`. That name is a Postgres function. Agents only use `docs_search` and `retrieve_context`.

---

## 2. When the corpus query is mandatory

Before any of the following, call `docs_search` or `retrieve_context` with `asset_type` and `framework`:

- scaffolding a new app or feature in Flutter, Android Compose, Refine, Next.js, React, or FastAPI
- choosing folder layout, routing, theming, or starter files for those frameworks
- copying “typical” widget / Compose / Refine / T3 / shadcn patterns
- writing or changing ingest, QA, or promotion code for this library

If the query returns nothing, say `LIBRARY MISS: <framework> <asset_type>` and stop that sub-task. Do not fill the gap from training memory. The Library agent may then enroll or repair corpus coverage.

If Arabold misses an official pin, say `DOCS MISSING: <package>` and halt that sub-task. Context7 may bridge **this turn only** for a public library while a scrape runs. It never becomes the durable answer.

---

## 3. How to query

Preferred filters:

```text
framework=flutter|android|refine|nextjs|react|fastapi|agentcore
asset_type=boilerplate|docs|agent_rule|openapi
language=dart|kotlin|typescript|python|markdown|yaml
```

Examples:

- Flutter screen structure → `framework=flutter`, `asset_type=boilerplate`
- Jetpack Compose sample pattern → `framework=android`, `asset_type=boilerplate`
- Refine resource/data-provider layout → `framework=refine`, `asset_type=boilerplate`
- T3 / Next.js app router starter → `framework=nextjs`, `asset_type=boilerplate`
- shadcn/ui primitive usage → `framework=react`, `asset_type=boilerplate`
- FastAPI contract shape → `framework=fastapi`, `asset_type=openapi` or `docs`

Then apply the returned pattern. Do not “improve” it into a second architecture.

---

## 4. Trust

- Promoted corpus rows are the only operator-corpus answers that may be taught to later agents.
- Quarantine and hold files are investigation evidence. They must not be used as starter code.
- A failed or held nightly sync does not make the last-good index untrustworthy. Keep using last-good.
- Do not treat MiniMax `E:\TemplateLibrary`, Codex_Managed runs, or OpenClaw agent packets as this library.

---

## 5. Bifrost

Bifrost (`agentcore-gateway`) is how agents reach the library. It is not the library. Do not add a direct Arabold, Postgres, or “knowledge MCP” entry to an IDE to “make the library faster.”
