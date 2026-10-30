"""AgentCore knowledge-corpus ingest for retrieval_documents (PG18 + pgvector).

Does not introduce LanceDB/Qdrant. Writes only to agent_core via psycopg.
"""

from .config import CORPUS_ROOT, EMBEDDING_DIM, EMBEDDING_MODEL, MODEL_CACHE
from .ingest import ingest_paths

__all__ = [
    "CORPUS_ROOT",
    "EMBEDDING_DIM",
    "EMBEDDING_MODEL",
    "MODEL_CACHE",
    "ingest_paths",
]
