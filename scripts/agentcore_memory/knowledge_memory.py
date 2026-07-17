"""Curated knowledge-memory adapter for M5.

Cognee is an additive semantic/relationship layer. AgentCore remains the
canonical evidence and retrieval authority in PostgreSQL; this module is the
only place the memory server knows how to detect Cognee.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

DEFAULT_COGNEE_ROOT = Path(r"H:\AgentRuntime\agentcore-memory\cognee")
DEFAULT_COGNEE_VENV = DEFAULT_COGNEE_ROOT / ".venv"
DEFAULT_COGNEE_VENV311 = DEFAULT_COGNEE_ROOT / ".venv311"
DISABLE_FLAG = "COGNEE_DISABLED.flag"


@dataclass(frozen=True)
class KnowledgeMemoryStatus:
    status: str
    backend: str
    version: str | None = None
    installation_path: str | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "status": self.status,
            "backend": self.backend,
        }
        if self.version:
            data["version"] = self.version
        if self.installation_path:
            data["installation_path"] = self.installation_path
        if self.detail:
            data["detail"] = self.detail
        return data


class KnowledgeMemoryPort:
    """Port boundary for curated Cognee memory.

    Retrieval rows are still ranked and returned by PostgreSQL. When this port
    is unavailable, callers must exclude Cognee-curated methods and return the
    best PostgreSQL-only result.
    """

    def __init__(self, runtime_root: Path | None = None) -> None:
        self.runtime_root = runtime_root or Path(os.environ.get("AGENTCORE_COGNEE_ROOT", str(DEFAULT_COGNEE_ROOT)))
        self.disable_flag = self.runtime_root / DISABLE_FLAG

    def status(self) -> KnowledgeMemoryStatus:
        if self.disable_flag.exists() or os.environ.get("AGENTCORE_COGNEE_DISABLED") == "1":
            return KnowledgeMemoryStatus(
                status="degraded_disabled",
                backend="cognee",
                detail="Cognee disabled by runtime outage marker; PostgreSQL retrieval remains active.",
            )

        self._add_venv_site_packages()
        try:
            module = importlib.import_module("cognee")
        except Exception as exc:  # noqa: BLE001 - status must never crash memory_status.
            subprocess_status = self._subprocess_status()
            if subprocess_status:
                return subprocess_status
            return KnowledgeMemoryStatus(status="degraded_unavailable", backend="cognee", detail=exc.__class__.__name__)

        try:
            version = metadata.version("cognee")
        except metadata.PackageNotFoundError:
            version = getattr(module, "__version__", None)

        installation_path = getattr(module, "__file__", None)
        return KnowledgeMemoryStatus(
            status="available",
            backend="cognee",
            version=version,
            installation_path=str(installation_path) if installation_path else None,
            detail="Native Windows package import succeeded; canonical retrieval remains PostgreSQL-backed.",
        )

    def enabled_methods(self, requested_methods: list[str] | None) -> list[str] | None:
        """Remove Cognee-curated retrieval when the adapter is unavailable."""

        methods = requested_methods[:] if requested_methods else None
        status = self.status()
        if status.status == "available":
            return methods
        if methods is None:
            return ["postgres_fts", "postgres_trigram", "pgvector_exact"]
        return [method for method in methods if method != "cognee_curated"]

    def _add_venv_site_packages(self) -> None:
        venv = Path(os.environ.get("AGENTCORE_COGNEE_VENV", str(DEFAULT_COGNEE_VENV)))
        candidates = [
            venv / "Lib" / "site-packages",
            venv / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages",
            DEFAULT_COGNEE_VENV311 / "Lib" / "site-packages",
        ]
        for candidate in candidates:
            if candidate.exists():
                candidate_text = str(candidate)
                if candidate_text not in sys.path:
                    sys.path.insert(0, candidate_text)

    def _subprocess_status(self) -> KnowledgeMemoryStatus | None:
        for venv in (Path(os.environ.get("AGENTCORE_COGNEE_VENV", str(DEFAULT_COGNEE_VENV))), DEFAULT_COGNEE_VENV311):
            python = venv / "Scripts" / "python.exe"
            if not python.exists():
                continue
            script = (
                "import cognee, importlib.metadata as m, json; "
                "print(json.dumps({'version': m.version('cognee'), 'path': getattr(cognee, '__file__', None)}))"
            )
            try:
                proc = subprocess.run(  # noqa: S603 - venv path is local configured runtime path.
                    [str(python), "-c", script],
                    capture_output=True,
                    text=True,
                    timeout=8,
                    check=False,
                    env=self._cognee_env(),
                )
            except Exception:  # noqa: BLE001
                continue
            if proc.returncode != 0:
                continue
            try:
                payload = json.loads(proc.stdout.strip().splitlines()[-1])
            except (IndexError, json.JSONDecodeError):
                continue
            return KnowledgeMemoryStatus(
                status="available",
                backend="cognee",
                version=payload.get("version"),
                installation_path=payload.get("path"),
                detail="Native Windows package import succeeded in isolated Cognee venv; canonical retrieval remains PostgreSQL-backed.",
            )
        return None

    def _cognee_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "DB_PROVIDER": "postgres",
                "DB_NAME": "cognee_core",
                "DB_HOST": "127.0.0.1",
                "DB_PORT": "55433",
                "DB_USERNAME": os.environ.get("AGENTCORE_COGNEE_DB_USERNAME", "postgres"),
                "VECTOR_DB_PROVIDER": "pgvector",
                "GRAPH_DATABASE_PROVIDER": "postgres",
                "CACHE_BACKEND": "postgres",
                "SYSTEM_ROOT_DIRECTORY": str(self.runtime_root / "system").replace("\\", "/"),
                "DATA_ROOT_DIRECTORY": str(self.runtime_root / "data").replace("\\", "/"),
            }
        )
        password = os.environ.get("AGENTCORE_COGNEE_DB_PASSWORD") or os.environ.get("AGENT_CORE_POSTGRES_PASSWORD")
        if password:
            env["DB_PASSWORD"] = password
        return env


def get_knowledge_memory_port() -> KnowledgeMemoryPort:
    return KnowledgeMemoryPort()
