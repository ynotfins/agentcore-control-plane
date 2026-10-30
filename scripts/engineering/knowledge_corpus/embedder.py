"""Local dense embeddings for knowledge corpus (nomic-embed-text-v1.5)."""

from __future__ import annotations

import hashlib
import os
from typing import Protocol

from .config import EMBEDDING_DIM, EMBEDDING_MODEL, EMBEDDING_MODEL_SHORT, MODEL_CACHE


class Embedder(Protocol):
    model_id: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashEmbedder:
    """Deterministic offline stub for tests / when SentenceTransformers is absent.

    Not for production semantic quality — FTS/trgm remain primary fallback.
    """

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self.model_id = "local_hash_v1"
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            # Nomic document prefix convention mirrored for stub consistency
            payload = f"search_document: {text}"
            digest = hashlib.sha256(payload.encode("utf-8")).digest()
            vals: list[float] = []
            seed = digest
            while len(vals) < self.dim:
                seed = hashlib.sha256(seed).digest()
                for b in seed:
                    vals.append((b / 127.5) - 1.0)
                    if len(vals) >= self.dim:
                        break
            # L2 normalize
            norm = sum(v * v for v in vals) ** 0.5 or 1.0
            out.append([v / norm for v in vals])
        return out


class NomicEmbedder:
    """SentenceTransformers wrapper for nomic-embed-text-v1.5."""

    def __init__(self) -> None:
        self.model_id = EMBEDDING_MODEL_SHORT
        self.dim = EMBEDDING_DIM
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        MODEL_CACHE.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", str(MODEL_CACHE))
        os.environ.setdefault("HF_HOME", str(MODEL_CACHE / "hf"))
        from sentence_transformers import SentenceTransformer  # type: ignore

        self._model = SentenceTransformer(
            EMBEDDING_MODEL,
            trust_remote_code=True,
            cache_folder=str(MODEL_CACHE),
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._load()
        assert self._model is not None
        # Nomic v1.5 expects task prefixes
        prefixed = [f"search_document: {t}" for t in texts]
        vectors = self._model.encode(
            prefixed,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [list(map(float, row)) for row in vectors]


def get_embedder(*, allow_hash_fallback: bool = True) -> Embedder:
    force = os.environ.get("AGENTCORE_EMBEDDING_FORCE", "").strip().lower()
    if force in {"hash", "local_hash_v1", "stub"}:
        return HashEmbedder()
    try:
        return NomicEmbedder()
    except Exception:
        if not allow_hash_fallback:
            raise
        return HashEmbedder()
