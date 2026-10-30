# Knowledge corpus ingest (PG18 + pgvector)

Extends AgentCore M5 `agentcore.retrieval_documents`. **Does not** install LanceDB or Qdrant.

## Cold roots

```text
E:\AgentCoreArchive\agentcore-memory\knowledge-corpus\
  docs\
  boilerplates\
  agent-rules\
  openapi\
```

## Migration (gated)

- `migrations/m5/002_up_knowledge_corpus.sql` — chunk identity, embedding lock, metadata indexes, hybrid metadata filter
- **Do not apply** without explicit operator AUTH + backup/restore gate

Ingest still works before m5.002 by mapping `boilerplate` / `agent_rule` / `openapi_spec` → `official_document` and storing `asset_type` in metadata.

## Run ingest

```powershell
$env:AGENTCORE_EMBEDDING_FORCE = "hash"   # offline stub; omit for real nomic
cd D:\agentcore-worktrees\agentcore-control-plane\local-agent-knowledge
python -m scripts.engineering.knowledge_corpus --dry-run
python -m scripts.engineering.knowledge_corpus --asset-type boilerplate --framework fastapi
```

Real embeddings require `sentence-transformers` + `nomic-ai/nomic-embed-text-v1.5` (cache under `F:\AgentCore\runtime\models`). Catalog promotion + Depwire required before treating them as approved runtime deps.

## Tests

```powershell
pytest scripts/engineering/knowledge_corpus/tests -q
```
