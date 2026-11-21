from __future__ import annotations

import copy
import json
import queue
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

import render_bifrost_config as renderer
import validate_contracts as contract_validator


REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER_PATH = REPO_ROOT / "ops" / "bifrost" / "wrappers" / "Start-AgentCoreClaspMcp.ps1"
CLASP_COMMAND = r"C:\Users\ynotf\AppData\Roaming\npm\clasp.cmd"
APPS_SCRIPT_ROOT = r"D:\github\apps-script"
PERMITTED_CLASP_TOOLS: list[str] = []
DENIED_CLASP_TOOLS = [
    "create_project",
    "push_files",
    "pull_files",
    "clone_project",
    "list_projects",
]


def _read_json_line(stream: Any, timeout: float = 20.0) -> dict[str, Any]:
    completed: queue.Queue[str] = queue.Queue(maxsize=1)
    threading.Thread(
        target=lambda: completed.put(stream.readline()),
        daemon=True,
    ).start()
    try:
        line = completed.get(timeout=timeout)
    except queue.Empty as exc:
        raise AssertionError("timed out waiting for clasp MCP JSON-RPC output") from exc
    assert line, "clasp MCP closed stdout before returning a JSON-RPC response"
    try:
        return json.loads(line)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"clasp wrapper emitted non-JSON stdout: {line!r}") from exc


def _stop_process_tree(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    subprocess.run(
        ["taskkill.exe", "/PID", str(proc.pid), "/T", "/F"],
        check=False,
        capture_output=True,
        text=True,
    )


def test_clasp_registry_exposes_only_the_approved_builder_surface() -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)
    server = registry["servers"]["clasp-mcp"]

    assert server["pinned_version"] == "3.4.1"
    assert server["connection_type"] == "stdio"
    assert server["executable_or_url"] == r"C:\Program Files\PowerShell\7\pwsh.EXE"
    assert server["arguments"] == [
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-File",
        str(WRAPPER_PATH),
    ]
    assert server["env_var_names"] == []
    assert server["permitted_tools"] == PERMITTED_CLASP_TOOLS
    assert server["denied_tools"] == DENIED_CLASP_TOOLS
    assert server["capability_profiles"] == []
    assert server["enabled"] is False
    assert server["status"] == "quarantine"
    assert server["is_code_mode_client"] is False
    assert server["tool_groups"]["clasp-remote-write"]["tools"] == ["push_files"]
    assert server["tool_groups"]["clasp-remote-write"]["access_policy"] == "operator_scope"
    assert server["tool_groups"]["clasp-remote-write"]["lease_defaults"][
        "requires_approval"
    ] is True
    assert server["tool_groups"]["clasp-source-sync"]["tools"] == [
        "pull_files",
        "clone_project",
    ]
    assert server["tool_groups"]["clasp-source-sync"]["lease_defaults"][
        "requires_approval"
    ] is True
    assert "clasp-mcp" not in registry["capability_profiles"]["builder"][
        "allowed_server_ids"
    ]
    assert "clasp-mcp" not in registry["capability_profiles"]["operator"][
        "allowed_server_ids"
    ]
    assert server["admission_evidence"]["authentication"]["status"] == "verified"
    assert server["admission_evidence"]["storage"]["status"] == "rejected"


def test_rendered_clasp_client_is_wrapped_and_auto_execution_stays_disabled() -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)
    config = renderer.build_bifrost_config(registry, {})
    clients = {item["name"]: item for item in config["mcp"]["client_configs"]}

    assert config["client"]["mcp_disable_auto_tool_inject"] is True
    assert config["mcp"]["tool_manager_config"]["disable_auto_tool_inject"] is True
    assert "clasp_mcp" not in clients

    builder = next(
        key for key in config["governance"]["virtual_keys"] if key["name"] == "builder"
    )
    builder_clients = {
        item["mcp_client_name"]: item["tools_to_execute"]
        for item in builder["mcp_configs"]
    }
    assert "clasp_mcp" not in builder_clients
    operator = next(
        key for key in config["governance"]["virtual_keys"] if key["name"] == "operator"
    )
    operator_clients = {
        item["mcp_client_name"]: item["tools_to_execute"]
        for item in operator["mcp_configs"]
    }
    assert "clasp_mcp" not in operator_clients


def test_validator_rejects_approval_required_tools_in_permanent_profiles() -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)
    unsafe = copy.deepcopy(registry)
    server = unsafe["servers"]["clasp-mcp"]
    server["permitted_tools"].append("push_files")
    server["denied_tools"].remove("push_files")
    server["tool_groups"]["clasp-remote-write"]["access_policy"] = "default_profile"
    server["enabled"] = True
    server["status"] = "active"
    server["capability_profiles"] = ["operator"]
    unsafe["capability_profiles"]["operator"]["allowed_server_ids"].append(
        "clasp-mcp"
    )

    errors = contract_validator.semantic_registry_checks(unsafe)

    assert any(
        "approval-required tool 'push_files' cannot be granted permanently"
        in error
        for error in errors
    )


@pytest.mark.parametrize(
    "tool_name",
    ["list_projects", "pull_files", "clone_project", "create_project", "push_files"],
)
def test_validator_rejects_clasp_tools_without_an_isolation_adapter(
    tool_name: str,
) -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)
    unsafe = copy.deepcopy(registry)
    server = unsafe["servers"]["clasp-mcp"]
    if tool_name not in server["permitted_tools"]:
        server["permitted_tools"].append(tool_name)
    server["denied_tools"] = [
        tool for tool in server["denied_tools"] if tool != tool_name
    ]

    errors = contract_validator.semantic_registry_checks(unsafe)

    assert any(
        f"clasp tool {tool_name!r} requires an isolation adapter" in error
        for error in errors
    )


def test_pipedream_sheets_candidate_stays_disabled_and_zero_profile() -> None:
    registry = renderer.load_json(renderer.REGISTRY_PATH)
    server = registry["servers"]["pipedream-google-sheets"]

    assert server["executable_or_url"] == "https://mcp.pipedream.net/v2"
    assert server["connection_type"] == "http"
    assert server["auth_type"] == "oauth"
    assert server["status"] == "developer_preview_oauth_pending"
    assert server["enabled"] is False
    assert server["permitted_tools"] == []
    assert server["denied_tools"] == []
    assert server["capability_profiles"] == []
    for profile in registry["capability_profiles"].values():
        assert "pipedream-google-sheets" not in profile["allowed_server_ids"]

    config = renderer.build_bifrost_config(registry, {})
    rendered_names = {item["name"] for item in config["mcp"]["client_configs"]}
    assert "pipedream_google_sheets" not in rendered_names
    assert "google_sheets_mcp" not in rendered_names


def test_output_schema_contract_covers_clasp_and_pipedream() -> None:
    contract = renderer.load_json(renderer.OUTPUT_SCHEMA_CONTRACT_PATH)

    assert contract["servers"]["clasp-mcp"] == {
        "adapter": "stdio_envelope",
        "default_profile": "fs_artifact",
        "tool_profiles": {"list_projects": "external"},
    }
    assert contract["servers"]["pipedream-google-sheets"]["adapter"] == "unsupported"


def test_clasp_wrapper_starts_exact_official_mcp_inventory_without_routine_stdout() -> None:
    assert WRAPPER_PATH.is_file()
    assert Path(CLASP_COMMAND).is_file()
    assert Path(APPS_SCRIPT_ROOT).is_dir()

    proc = subprocess.Popen(
        [
            r"C:\Program Files\PowerShell\7\pwsh.EXE",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(WRAPPER_PATH),
        ],
        cwd=REPO_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "agentcore-clasp-test", "version": "1.0"},
                },
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ]
        assert proc.stdin is not None
        for request in requests:
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.flush()

        initialize = _read_json_line(proc.stdout)
        tools_list = _read_json_line(proc.stdout)
        assert initialize["id"] == 1
        assert initialize["result"]["serverInfo"]["version"] == "3.4.1"
        assert tools_list["id"] == 2
        observed = [tool["name"] for tool in tools_list["result"]["tools"]]
        assert observed == PERMITTED_CLASP_TOOLS
    finally:
        if proc.stdin is not None:
            proc.stdin.close()
        _stop_process_tree(proc)


def _load_guard() -> Any:
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "bifrost"))
    import clasp_mcp_guard

    return clasp_mcp_guard


def test_guard_denies_path_tools_even_for_paths_inside_the_authorized_root(
    tmp_path: Path,
) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "nested" / "project"
    project.mkdir(parents=True)

    for tool_name, arguments in (
        ("pull_files", {"projectDir": str(project)}),
        ("pull_files", {"projectDir": str(project).upper()}),
        ("pull_files", {"projectDir": "nested/./project"}),
        ("clone_project", {"projectDir": "nested/new-project"}),
        (
            "clone_project",
            {"projectDir": str(project), "sourceDir": "src\\server/handlers"},
        ),
    ):
        with pytest.raises(guard.GuardViolation) as exc_info:
            guard.validate_tool_call(tool_name, arguments, root)
        assert exc_info.value.code == "tool_denied"


@pytest.mark.parametrize(
    "candidate",
    [
        "..\\escape",
        "nested/../../escape",
        r"C:\Users\ynotf\outside",
        r"E:\outside",
        r"C:drive-relative",
        r"\\server\share\project",
        r"\\?\D:\github\apps-script\project",
        r"\\.\D:\github\apps-script\project",
        r"~\outside",
        r"nested\name:stream",
    ],
)
def test_guard_rejects_project_path_escape_classes(
    tmp_path: Path, candidate: str
) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    root.mkdir()

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call("pull_files", {"projectDir": candidate}, root)


@pytest.mark.parametrize(
    "source_dir",
    [
        "../escape",
        r"nested\..\..\escape",
        r"C:\Users\ynotf\outside",
        r"E:drive-relative",
        r"\\server\share",
        r"\\?\D:\outside",
        r"nested\name:stream",
    ],
)
def test_guard_rejects_source_dir_escape_classes(
    tmp_path: Path, source_dir: str
) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    project.mkdir(parents=True)

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call(
            "clone_project",
            {"projectDir": str(project), "sourceDir": source_dir},
            root,
        )


def test_guard_rejects_junction_escape_and_nonexistent_child(
    tmp_path: Path,
) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    nested = root / "nested"
    nested.mkdir()
    junction = nested / "linked-outside"
    result = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(junction), str(outside)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"junction creation unavailable: {result.stderr.strip()}")

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call("pull_files", {"projectDir": str(junction)}, root)
    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call(
            "clone_project", {"projectDir": str(junction / "new-child")}, root
        )


def test_guard_rejects_source_dir_through_nested_junction(tmp_path: Path) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    outside = tmp_path / "outside"
    project.mkdir(parents=True)
    outside.mkdir()
    junction = project / "nested-link"
    result = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(junction), str(outside)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"junction creation unavailable: {result.stderr.strip()}")

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call(
            "clone_project",
            {"projectDir": str(project), "sourceDir": "nested-link/new-child"},
            root,
        )


def test_guard_denies_path_tools_with_valid_clasp_configuration(tmp_path: Path) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    content = project / "src"
    content.mkdir(parents=True)
    (project / ".clasp.json").write_text(
        json.dumps({"scriptId": "test-id", "srcDir": "src", "allowSymlinks": False}),
        encoding="utf-8",
    )
    (project / ".claspignore").write_text("**/.git/**\n", encoding="utf-8")

    with pytest.raises(guard.GuardViolation) as exc_info:
        guard.validate_tool_call("pull_files", {"projectDir": str(project)}, root)
    assert exc_info.value.code == "tool_denied"


def test_guard_rejects_clasp_configured_junction_escape(tmp_path: Path) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    outside = tmp_path / "outside"
    project.mkdir(parents=True)
    outside.mkdir()
    junction = project / "linked-outside"
    result = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(junction), str(outside)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"junction creation unavailable: {result.stderr.strip()}")
    (project / ".clasp.json").write_text(
        json.dumps(
            {
                "scriptId": "test-id",
                "rootDir": "linked-outside",
                "allowSymlinks": False,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call("pull_files", {"projectDir": str(project)}, root)


@pytest.mark.parametrize("allow_symlinks", [True, 1, "false", [], {}])
def test_guard_rejects_allow_symlinks_before_nested_remote_paths(
    tmp_path: Path, allow_symlinks: Any
) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    project.mkdir(parents=True)
    (project / ".clasp.json").write_text(
        json.dumps({"scriptId": "test-id", "allowSymlinks": allow_symlinks}),
        encoding="utf-8",
    )

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call("pull_files", {"projectDir": str(project)}, root)


def test_guard_rejects_clasp_config_symlink_outside_project(tmp_path: Path) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    outside = tmp_path / "outside.clasp.json"
    project.mkdir(parents=True)
    outside.write_text(json.dumps({"scriptId": "test-id"}), encoding="utf-8")
    try:
        (project / ".clasp.json").symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"file symlink creation unavailable: {exc}")

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call("pull_files", {"projectDir": str(project)}, root)


def test_guard_rejects_claspignore_symlink_outside_project(tmp_path: Path) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    outside = tmp_path / "outside.claspignore"
    project.mkdir(parents=True)
    (project / ".clasp.json").write_text(
        json.dumps({"scriptId": "test-id"}), encoding="utf-8"
    )
    outside.write_text("**/private/**\n", encoding="utf-8")
    try:
        (project / ".claspignore").symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"file symlink creation unavailable: {exc}")

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call("pull_files", {"projectDir": str(project)}, root)


def test_guard_rejects_hardlinked_files_before_destructive_sync(tmp_path: Path) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    outside = tmp_path / "outside.js"
    project.mkdir(parents=True)
    (project / ".clasp.json").write_text(
        json.dumps({"scriptId": "test-id"}), encoding="utf-8"
    )
    outside.write_text("outside", encoding="utf-8")
    try:
        (project / "Code.js").hardlink_to(outside)
    except OSError as exc:
        pytest.skip(f"hard-link creation unavailable: {exc}")

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call("pull_files", {"projectDir": str(project)}, root)


def test_guard_rejects_configured_root_junction(tmp_path: Path) -> None:
    guard = _load_guard()
    outside = tmp_path / "outside"
    project = outside / "project"
    project.mkdir(parents=True)
    root = tmp_path / "apps-script"
    result = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(root), str(outside)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"junction creation unavailable: {result.stderr.strip()}")

    with pytest.raises(guard.GuardViolation) as exc_info:
        guard.validate_tool_call("pull_files", {"projectDir": "project"}, root)
    assert exc_info.value.code == "tool_denied"


def test_guard_rejects_configured_root_below_junction_ancestor(tmp_path: Path) -> None:
    guard = _load_guard()
    outside = tmp_path / "outside-parent"
    root_target = outside / "apps-script"
    project = root_target / "project"
    project.mkdir(parents=True)
    linked_parent = tmp_path / "linked-parent"
    result = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(linked_parent), str(outside)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"junction creation unavailable: {result.stderr.strip()}")

    with pytest.raises(guard.GuardViolation) as exc_info:
        guard.validate_tool_call(
            "pull_files", {"projectDir": "project"}, linked_parent / "apps-script"
        )
    assert exc_info.value.code == "tool_denied"


@pytest.mark.parametrize(
    "config",
    [
        {"scriptId": "test-id", "srcDir": "../outside"},
        {"scriptId": "test-id", "rootDir": r"C:\\Users\\ynotf\\outside"},
        {"scriptId": "test-id", "srcDir": r"\\\\server\\share"},
        {"scriptId": "test-id", "rootDir": r"E:drive-relative"},
    ],
)
def test_guard_rejects_effective_paths_from_clasp_config(
    tmp_path: Path, config: dict[str, Any]
) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    project.mkdir(parents=True)
    (project / ".clasp.json").write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call("pull_files", {"projectDir": str(project)}, root)


def test_guard_fails_closed_on_non_json_clasp_configuration(tmp_path: Path) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    project.mkdir(parents=True)
    (project / ".clasp.json").write_text(
        "{scriptId: 'test-id', allowSymlinks: true}", encoding="utf-8"
    )

    with pytest.raises(guard.GuardViolation) as exc_info:
        guard.validate_tool_call("pull_files", {"projectDir": str(project)}, root)
    assert exc_info.value.code == "tool_denied"


@pytest.mark.parametrize("device_name", ["CON", "nul.txt", "AUX ", "COM1", "LPT9.log"])
def test_guard_rejects_windows_device_names(tmp_path: Path, device_name: str) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    root.mkdir()

    with pytest.raises(guard.GuardViolation):
        guard.validate_tool_call(
            "clone_project", {"projectDir": f"project/{device_name}"}, root
        )


def test_guard_denies_all_upstream_tools_before_dispatch(
    tmp_path: Path,
) -> None:
    guard = _load_guard()
    root = tmp_path / "apps-script"
    project = root / "project"
    project.mkdir(parents=True)

    for tool_name in (
        "push_files",
        "create_project",
        "pull_files",
        "clone_project",
        "list_projects",
        "unknown_tool",
    ):
        with pytest.raises(guard.GuardViolation) as exc_info:
            guard.validate_tool_call(tool_name, {"projectDir": str(project)}, root)
        assert exc_info.value.code == "tool_denied"


def test_guard_filters_privileged_tools_and_redacts_denial_details(tmp_path: Path) -> None:
    guard = _load_guard()
    upstream = {
        "jsonrpc": "2.0",
        "id": 7,
        "result": {
            "tools": [
                {"name": "push_files"},
                {"name": "pull_files"},
                {"name": "create_project"},
                {"name": "clone_project"},
                {"name": "list_projects"},
            ]
        },
    }
    filtered = guard.filter_tools_list(upstream)
    assert [item["name"] for item in filtered["result"]["tools"]] == []

    secret_path = str(tmp_path / "private-host-path")
    denial = guard.denied_tool_response(
        request_id=9,
        violation=guard.GuardViolation("path_outside_workspace"),
    )
    rendered = json.dumps(denial)
    assert secret_path not in rendered
    assert str(tmp_path) not in rendered
    assert denial["result"]["isError"] is True
    assert denial["result"]["structuredContent"] == {
        "error_code": "path_outside_workspace"
    }


def test_clasp_wrapper_rejects_every_upstream_tool_without_contacting_google() -> None:
    proc = subprocess.Popen(
        [
            r"C:\Program Files\PowerShell\7\pwsh.EXE",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(WRAPPER_PATH),
        ],
        cwd=REPO_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert proc.stdin is not None
        requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "agentcore-clasp-test", "version": "1.0"},
                },
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            {"jsonrpc": "2.0", "id": 99, "result": {}},
        ]
        requests.extend(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {"projectDir": APPS_SCRIPT_ROOT},
                },
            }
            for request_id, tool_name in enumerate(
                (
                    "push_files",
                    "create_project",
                    "pull_files",
                    "clone_project",
                    "list_projects",
                ),
                start=2,
            )
        )
        for request in requests:
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.flush()

        initialize = _read_json_line(proc.stdout)
        assert initialize["id"] == 1
        for request_id in range(2, 7):
            denied = _read_json_line(proc.stdout)
            assert denied["id"] == request_id
            assert denied["result"]["isError"] is True
            assert denied["result"]["structuredContent"] == {
                "error_code": "tool_denied"
            }
            assert "D:\\github" not in json.dumps(denied)
    finally:
        if proc.stdin is not None:
            proc.stdin.close()
        _stop_process_tree(proc)
