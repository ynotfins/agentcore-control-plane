"""Unit tests for knowledge-corpus chunkers (no DB / no model download)."""

from __future__ import annotations

from pathlib import Path

from scripts.engineering.knowledge_corpus.chunkers import (
    chunk_code,
    chunk_markdown,
    chunk_openapi,
)


def test_markdown_header_chunks(tmp_path: Path) -> None:
    p = tmp_path / "guide.md"
    text = "# Intro\nHello\n\n## Details\nMore\n"
    chunks = chunk_markdown(p, text)
    titles = [c.title for c in chunks]
    assert "Intro" in titles
    assert "Details" in titles
    assert all(c.chunk_id for c in chunks)


def test_openapi_splits_operations(tmp_path: Path) -> None:
    p = tmp_path / "openapi.yaml"
    text = """
openapi: 3.0.3
info:
  title: Demo API
  version: 1.0.0
paths:
  /health:
    get:
      operationId: getHealth
      summary: Health check
      responses:
        "200":
          description: ok
  /items/{id}:
    get:
      operationId: getItem
      summary: Get item
      responses:
        "200":
          description: ok
"""
    chunks = chunk_openapi(p, text)
    assert any("overview" in c.title.lower() for c in chunks)
    assert any("GET /health" in c.title for c in chunks)
    assert any("GET /items/{id}" in c.title for c in chunks)


def test_python_code_chunks_functions(tmp_path: Path) -> None:
    p = tmp_path / "app.py"
    text = '''
"""Module doc."""

def greet(name: str) -> str:
    return f"hi {name}"

class Greeter:
    def run(self) -> str:
        return greet("world")
'''
    chunks = chunk_code(p, text)
    symbols = [c.extra_metadata.get("symbol") for c in chunks]
    assert "greet" in symbols or any("greet" in c.title for c in chunks)
    assert any(c.body.strip() for c in chunks)
