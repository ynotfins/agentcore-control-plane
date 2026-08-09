from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

import mcp_output_schema_adapter as adapter
import render_bifrost_config as renderer


MEMORY_RUNTIME_ENV_SOURCES = (
    Path("scripts/agentcore_memory/server.py"),
    Path("scripts/agentcore_memory/knowledge_memory.py"),
    Path("scripts/agentcore_memory/neutral_recall.py"),
    Path("scripts/agentcore_memory/device_identity.py"),
    Path("scripts/agentcore_project_boundary.py"),
    Path("scripts/agentcore_memory/recovery.py"),
)
LEGACY_MEMORY_ENV_ALIASES = {
    "SWARMRECALL_API_KEY",
    "SWARMRECALL_API_URL",
}


def _source_environment_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    constants = {
        target.id: node.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        for target in node.targets
        if isinstance(target, ast.Name)
    }

    def is_os_environ(node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and node.attr == "environ"
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
        )

    def resolve_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return constants.get(node.id)
        return None

    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and is_os_environ(node.func.value)
            and node.args
        ):
            name = resolve_name(node.args[0])
            if name:
                names.add(name)
        if isinstance(node, ast.Subscript) and is_os_environ(node.value):
            name = resolve_name(node.slice)
            if name:
                names.add(name)
    return names


def test_child_environment_excludes_unrelated_user_secret_and_keeps_reviewed_values() -> None:
    parent_env = {
        "SYSTEMROOT": r"C:\\Windows",
        "WINDIR": r"C:\\Windows",
        "COMSPEC": r"C:\\Windows\\System32\\cmd.exe",
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "PATH": r"C:\\Windows\\System32",
        "TEMP": r"C:\\Temp",
        "TMP": r"C:\\Temp",
        "USERPROFILE": r"C:\\Users\\agentcore",
        "APPDATA": r"C:\\Users\\agentcore\\AppData\\Roaming",
        "LOCALAPPDATA": r"C:\\Users\\agentcore\\AppData\\Local",
        "DECLARED_TEST_SECRET": "reviewed-value",
        "UNRELATED_USER_SECRET": "must-not-reach-child",
    }

    child_env = adapter.build_child_environment(
        parent_env,
        declared_env_names=["DECLARED_TEST_SECRET"],
        static_env={"STATIC_NONSECRET": "approved"},
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, os; print(json.dumps(dict(os.environ)))",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=child_env,
    )
    observed = json.loads(result.stdout)

    assert observed["DECLARED_TEST_SECRET"] == "reviewed-value"
    assert observed["STATIC_NONSECRET"] == "approved"
    assert "UNRELATED_USER_SECRET" not in observed
    for required_name in adapter.WINDOWS_REQUIRED_ENV_NAMES:
        assert observed[required_name] == parent_env[required_name]


def test_rendered_stdio_launches_pass_only_registry_environment_policy() -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)
    wiring = renderer.OutputSchemaWiring(registry)
    config = renderer.build_bifrost_config(registry, {}, output_schema=wiring)
    rendered_by_name = {client["name"]: client for client in config["mcp"]["client_configs"]}

    for server in registry["servers"].values():
        if not (server.get("enabled") and server["connection_type"] in {"stdio", "router"}):
            continue
        stdio_config = rendered_by_name[server["bifrost_client_name"]]["stdio_config"]
        args = stdio_config["args"]

        assert stdio_config["command"] == wiring.interpreter
        rendered_names = [
            args[index + 1]
            for index, arg in enumerate(args[:-1])
            if arg == "--allow-env"
        ]
        assert rendered_names == server["env_var_names"]
        assert stdio_config["envs"] == []


def test_agentcore_memory_declarations_cover_its_runtime_source_inventory() -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)
    declared = set(registry["servers"]["agentcore-memory"]["env_var_names"])
    source_inventory = set().union(
        *(_source_environment_names(path) for path in MEMORY_RUNTIME_ENV_SOURCES)
    )
    required = source_inventory - LEGACY_MEMORY_ENV_ALIASES

    assert declared == required
    assert not declared & LEGACY_MEMORY_ENV_ALIASES


def test_agentcore_project_router_declares_its_required_secret_variable() -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)
    assert registry["servers"]["agentcore-project-router"]["env_var_names"] == [
        "BIFROST_ADMIN_KEY"
    ]


def test_default_config_build_cannot_bypass_stdio_environment_isolation() -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)
    config = renderer.build_bifrost_config(registry, {})

    for client in config["mcp"]["client_configs"]:
        stdio_config = client.get("stdio_config")
        if stdio_config is None:
            continue
        assert "mcp_output_schema_adapter.py" in " ".join(stdio_config["args"])


def test_raw_stdio_cannot_render_when_isolation_wiring_is_absent() -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)
    registry.pop("output_schema_adapter")

    with pytest.raises(ValueError, match="stdio environment isolation adapter is required"):
        renderer.build_bifrost_config(registry, {})


def test_adapter_launches_the_upstream_with_the_filtered_environment() -> None:
    parent_env = {
        "SYSTEMROOT": r"C:\\Windows",
        "WINDIR": r"C:\\Windows",
        "COMSPEC": r"C:\\Windows\\System32\\cmd.exe",
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "PATH": r"C:\\Windows\\System32",
        "TEMP": r"C:\\Temp",
        "TMP": r"C:\\Temp",
        "USERPROFILE": r"C:\\Users\\agentcore",
        "APPDATA": r"C:\\Users\\agentcore\\AppData\\Roaming",
        "LOCALAPPDATA": r"C:\\Users\\agentcore\\AppData\\Local",
        "DECLARED_TEST_SECRET": "reviewed-value",
        "UNRELATED_USER_SECRET": "must-not-reach-child",
    }
    proc = adapter.launch_upstream(
        [sys.executable, "-c", "import json, os; print(json.dumps(dict(os.environ)))"],
        declared_env_names=["DECLARED_TEST_SECRET"],
        static_env={},
        parent_env=parent_env,
    )
    stdout, _ = proc.communicate(timeout=10)

    assert proc.returncode == 0
    observed = json.loads(stdout)
    assert observed["DECLARED_TEST_SECRET"] == "reviewed-value"
    assert "UNRELATED_USER_SECRET" not in observed


def test_explicit_empty_parent_environment_never_falls_back_to_process_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv("PATH", "process-only-path")

    proc = adapter.launch_upstream(
        [sys.executable, "-c", "import os; print(os.getenv('PATH', ''))"],
        declared_env_names=[],
        static_env={},
        parent_env={},
    )
    stdout, _ = proc.communicate(timeout=10)

    assert proc.returncode == 0
    assert stdout.strip() == ""
