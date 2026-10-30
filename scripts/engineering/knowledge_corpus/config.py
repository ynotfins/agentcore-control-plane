"""Paths and frozen embedding contract for the knowledge corpus."""

from __future__ import annotations

import os
from pathlib import Path

CORPUS_ROOT = Path(
    os.environ.get(
        "AGENTCORE_KNOWLEDGE_CORPUS_ROOT",
        r"E:\AgentCoreArchive\agentcore-memory\knowledge-corpus",
    )
)
MODEL_CACHE = Path(
    os.environ.get(
        "AGENTCORE_EMBEDDING_MODEL_CACHE",
        r"F:\AgentCore\runtime\models",
    )
)

# Frozen dense model for this plane (local-only).
EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1.5"
EMBEDDING_MODEL_SHORT = "nomic-embed-text-v1.5"
EMBEDDING_DIM = 768

ASSET_DIRS = {
    "docs": CORPUS_ROOT / "docs",
    "boilerplate": CORPUS_ROOT / "boilerplates",
    "agent_rule": CORPUS_ROOT / "agent-rules",
    "openapi": CORPUS_ROOT / "openapi",
}

SOURCE_KIND_BY_ASSET = {
    "docs": "official_document",
    "boilerplate": "boilerplate",
    "agent_rule": "agent_rule",
    "openapi": "openapi_spec",
}

# When m5.002 is not applied, map new kinds onto an allowed legacy kind.
LEGACY_SOURCE_KIND = {
    "boilerplate": "official_document",
    "agent_rule": "official_document",
    "openapi_spec": "official_document",
    "official_document": "official_document",
}

SKIP_DIR_NAMES = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "coverage",
}

SKIP_FILE_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".pyc",
    ".pyo",
    ".wasm",
    ".lock",
}

SKIP_FILE_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "uv.lock",
    "Cargo.lock",
    ".env",
    ".env.local",
}
