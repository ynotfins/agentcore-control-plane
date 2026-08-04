from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from agentcore import workflow_cli
from agentcore_workflow.runtime_attestation import build_runtime_attestation


def _init_repo(path: Path) -> str:
    path.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    (path / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=AgentCore Test",
            "-c",
            "user.email=test@agentcore.invalid",
            "commit",
            "-m",
            "fixture",
        ],
        cwd=path,
        check=True,
        capture_output=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_runtime_attestation_binds_installed_release_and_git_bytes(tmp_path: Path) -> None:
    control_plane = tmp_path / "control-plane"
    context_engine = tmp_path / "context-engine"
    control_sha = _init_repo(control_plane)
    context_sha = _init_repo(context_engine)

    artifact = context_engine / "release" / "0.2.3" / "engine.whl"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"sealed-wheel")
    artifact_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "release": "0.2.3",
        "artifacts": [
            {"file": artifact.name, "bytes": artifact.stat().st_size, "sha256": artifact_sha}
        ],
    }
    (artifact.parent / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    catalog = {
        "schema_version": 1,
        "catalog_version": "test-catalog",
        "portable_catalog": {
            "package": "agentcore-context-engine",
            "version": "0.2.3",
            "source": str(context_engine),
        },
    }
    catalog_path = control_plane / "contracts" / "context-engine-execution-catalog.json"
    catalog_path.parent.mkdir()
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    detail = build_runtime_attestation(
        repo_root=control_plane,
        catalog_path=catalog_path,
        topology_sha256="topology-sha",
        python_executable="python-fixture.exe",
        installed_version=lambda _package: "0.2.3",
    )

    assert detail["schema_version"] == 1
    assert detail["context_engine"]["installed_version"] == "0.2.3"
    assert detail["context_engine"]["source_commit"] == context_sha
    assert detail["context_engine"]["artifacts"][0]["sha256"] == artifact_sha
    assert detail["control_plane_commit"] == control_sha
    assert detail["topology_fingerprint_sha256"] == "topology-sha"
    assert detail["python_executable"] == str(Path("python-fixture.exe").resolve())


def test_runtime_attestation_fails_closed_on_installed_version_drift(tmp_path: Path) -> None:
    control_plane = tmp_path / "control-plane"
    context_engine = tmp_path / "context-engine"
    _init_repo(control_plane)
    _init_repo(context_engine)
    release = context_engine / "release" / "0.2.3"
    release.mkdir(parents=True)
    (release / "manifest.json").write_text(
        json.dumps({"schema_version": 1, "release": "0.2.3", "artifacts": []}),
        encoding="utf-8",
    )
    catalog_path = control_plane / "contracts" / "context-engine-execution-catalog.json"
    catalog_path.parent.mkdir()
    catalog_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "catalog_version": "test-catalog",
                "portable_catalog": {
                    "package": "agentcore-context-engine",
                    "version": "0.2.3",
                    "source": str(context_engine),
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="installed Context Engine version drift"):
        build_runtime_attestation(
            repo_root=control_plane,
            catalog_path=catalog_path,
            topology_sha256="topology-sha",
            installed_version=lambda _package: "0.2.2",
        )


def test_workflow_runtime_attestation_is_recorded_as_system_verified(monkeypatch) -> None:
    detail = {
        "context_engine": {"installed_version": "0.2.3"},
        "topology_fingerprint_sha256": "topology-sha",
    }
    captured: dict = {}
    monkeypatch.setattr(workflow_cli, "build_runtime_attestation", lambda **_kwargs: detail)
    monkeypatch.setattr(workflow_cli, "build_topology", lambda: object())
    monkeypatch.setattr(workflow_cli, "topology_fingerprint", lambda _value: "topology-sha")

    def _record(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return "evidence-id"

    monkeypatch.setattr(workflow_cli.wf_db, "record_evidence", _record)

    evidence_id = workflow_cli._record_runtime_attestation("run-id", "project-id", "M6")

    assert evidence_id == "evidence-id"
    assert captured["args"][3] == "runtime_attestation"
    assert captured["args"][5] == detail
    assert captured["kwargs"]["trust_class"] == "system_verified"
