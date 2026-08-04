"""Fail-closed production runtime attestation for AgentCore workflows."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from importlib import metadata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "contracts" / "context-engine-execution-catalog.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build_runtime_attestation(
    *,
    topology_sha256: str,
    repo_root: Path = REPO_ROOT,
    catalog_path: Path = CATALOG_PATH,
    python_executable: str = sys.executable,
    installed_version: Callable[[str], str] = metadata.version,
) -> dict:
    """Bind one workflow run to verified package, Git, topology, and wheel bytes."""
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != 1:
        raise RuntimeError("unsupported Context Engine execution catalog schema")

    portable = catalog["portable_catalog"]
    package = str(portable["package"])
    expected_version = str(portable["version"])
    actual_version = installed_version(package)
    if actual_version != expected_version:
        raise RuntimeError(
            "installed Context Engine version drift: "
            f"expected {expected_version}, found {actual_version}"
        )

    context_source = Path(str(portable["source"])).resolve()
    release_root = (context_source / "release" / expected_version).resolve()
    manifest_path = release_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or str(manifest.get("release")) != expected_version:
        raise RuntimeError("Context Engine release manifest does not match the execution catalog")

    artifacts: list[dict] = []
    for entry in manifest.get("artifacts", []):
        filename = str(entry["file"])
        if Path(filename).name != filename:
            raise RuntimeError(f"unsafe Context Engine artifact name: {filename}")
        artifact = release_root / filename
        actual_sha = _sha256(artifact)
        expected_sha = str(entry["sha256"]).lower()
        actual_bytes = artifact.stat().st_size
        if actual_sha != expected_sha or actual_bytes != int(entry["bytes"]):
            raise RuntimeError(f"Context Engine artifact drift: {filename}")
        artifacts.append(
            {"file": filename, "bytes": actual_bytes, "sha256": actual_sha}
        )
    if not artifacts:
        raise RuntimeError("Context Engine release manifest contains no artifacts")

    return {
        "schema_version": 1,
        "catalog_version": str(catalog["catalog_version"]),
        "catalog_sha256": _sha256(catalog_path),
        "control_plane_commit": _git_head(repo_root),
        "topology_fingerprint_sha256": topology_sha256,
        "python_executable": str(Path(python_executable).resolve()),
        "context_engine": {
            "package": package,
            "installed_version": actual_version,
            "source_commit": _git_head(context_source),
            "release_manifest_sha256": _sha256(manifest_path),
            "artifacts": artifacts,
        },
    }
