# Proposal: catalog under_review for knowledge-corpus embedding + AST chunking

**Date:** 2026-10-29  
**Status:** applied 2026-10-29 (operator AUTH install SentenceTransformers + Tree-sitter)  
**Related:** `scripts/engineering/knowledge_corpus/`, `migrations/m5/002_up_knowledge_corpus.sql`  
**Runtime venv:** `F:\AgentCore\runtime\knowledge-corpus`

## Applied packages

| Package | Status | Notes |
| --- | --- | --- |
| `sentence-transformers` 3.4.1 | approved | Model `nomic-ai/nomic-embed-text-v1.5` (768-d); cache `F:\AgentCore\runtime\models` |
| `einops` | installed (transitive) | Required for nomic `trust_remote_code` |
| `tree-sitter` 0.24.0 | approved | AST chunking |
| `tree-sitter-python` / `tree-sitter-typescript` | approved | Python 3.13 wheels; replace `tree-sitter-languages` |
| `tree-sitter-languages` | rejected | No Python 3.13 wheels on this workstation |

## Rejected (do not re-open without ADR)

- `lancedb`, `qdrant-client` — already rejected; BLUEPRINT forbids second vector store

## Depwire gate

Run Depwire against the knowledge_corpus package cwd before merging catalog status to `approved`.
