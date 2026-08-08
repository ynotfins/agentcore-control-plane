from __future__ import annotations

import json
import subprocess
import sys

import mcp_output_schema_adapter as adapter
import render_bifrost_config as renderer


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


def test_repo_owned_stdio_upstreams_declare_their_required_secret_variables() -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)

    assert registry["servers"]["agentcore-memory"]["env_var_names"] == [
        "AGENT_CORE_POSTGRES_PASSWORD"
    ]
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
