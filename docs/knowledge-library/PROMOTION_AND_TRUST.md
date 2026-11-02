# Promotion and Trust Law — Knowledge Library

**Status:** operator-locked.  
**Approval:** `AUTH-2026-11-01-KNOWLEDGE-LIBRARY-AUTHORITY`

Agents trust the library because **only QA-passing, allowlisted files** reach `retrieval_documents`. Last-good always remains queryable.

---

## 1. Last-good wins

A failed, held, or partial sync never deletes or overwrites the previous good promoted tree or its index rows for files that did not pass.

Rollback owner: `ops/Invoke-AgentCoreKnowledgeCorpusSync.ps1 -Rollback <corpus-id>` restores the last-good SHA for that remote only.

---

## 2. What may promote

A file may be copied to `knowledge-corpus` and ingested when **all** are true:

- the remote is enrolled in `contracts/knowledge-corpus-catalog.json`
- the path matches that remote’s include globs
- Tree-sitter or Markdown QA passes
- the file is not secret-like, not a binary dump, and not an unexpected path
- the remote’s changed-file count is inside the catalog bound (first ingest of a brand-new remote may skip the file-count bound; it still cannot dump a whole framework repo)

A remote may stay enrolled and keep updating even if **some** files fail. Passing files promote. Failing files stay in hold evidence. One poisoned README must not freeze an entire enrolled framework.

**Hard-fail (holds that path / can hold the remote):** secrets, credentials, binaries, unexpected paths outside globs, whole-framework dumps.

**New remote or new framework:** operator AUTH plus catalog edit. First clone of a new remote stays hold-by-default until an authority-maintainer promotes it.

---

## 3. What must never enter the index

- Whole Next.js / Flutter / Android / Refine / FastAPI repositories
- Swarm trees, `H:`, `E:\Swarm`, Obsidian vaults, WhatsApp backups
- Live `.env`, credentials, mail-panel notes, `setup-nfa-secrets.ps1` bodies
- Cloud-agent inbound webhooks as the update path
- Cognee ingest of raw repos (Cognee stays curated promotions only)
- Cloud OpenAI embeddings as the required embedding path
- A second database or a second MCP server

---

## 4. Nightly update

| Fact | Value |
| --- | --- |
| Task | `\AgentCore\KnowledgeCorpusSync` |
| Script | `D:\agentcore-worktrees\agentcore-control-plane\main\ops\Invoke-AgentCoreKnowledgeCorpusSync.ps1 -Apply` |
| Default | hidden, logged, no desktop popup |
| Python | prefer `F:\AgentCore\runtime\knowledge-corpus\Scripts\python.exe` |
| Embeddings | local `nomic-embed-text-v1.5`, 768-d, cache `F:\AgentCore\runtime\models` |

The dirty checkout `D:\github\agentcore-control-plane` on `feat/raven-control-plane-enrollment` is **not** the nightly job. Do not point the task at it. Do not `git clean` it as part of library work.

Catalog remotes and globs may change with a normal PR. This trust law does not.

---

## 5. Ingest contract

- Ingest promoted folders (`--path` roots), not hundreds of file arguments (Windows argv limit).
- Re-ingest is idempotent on `chunk_id`.
- Full-text + trigram remain usable if the embedder is down. Do not take the library offline because dense embeddings failed; repair the F: runtime and re-ingest.
- `m5.002` is the live schema. Further live DDL needs AUTH.

---

## 6. Trust classes for answers

| Class | May answer agents? |
| --- | --- |
| Promoted + ingested | Yes |
| Quarantine clone (not promoted) | No — investigation only |
| Hold report | No — investigation only |
| Arabold exact pin | Yes for official API/version facts |
| Training memory / Context7 | No as durable library truth |
