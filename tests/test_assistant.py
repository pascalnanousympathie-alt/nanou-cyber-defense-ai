from __future__ import annotations

import pytest

from nanou_cyber_ai.assistant.runtime import (
    _local_command,
    _tools_for_access,
    execute_tool,
    run_assistant,
)
from nanou_cyber_ai.settings import settings


def test_local_command_router_understands_defensive_commands() -> None:
    assert _local_command("Jereo CVE-2024-3094") == (
        "lookup_cve",
        {"cve_id": "CVE-2024-3094"},
    )
    assert _local_command("Jereo CISA KEV") == ("get_kev_summary", {})
    assert _local_command("Jereo malware metadata") == (
        "list_malware_metadata",
        {"limit": 10},
    )
    assert _local_command("MCP tools") == ("list_defensive_tools", {})
    assert _local_command("help") == ("help", {})


def test_assistant_tool_allowlist_respects_role_and_scopes() -> None:
    viewer_tools = {
        tool["name"]
        for tool in _tools_for_access({"intel:read", "malware:metadata:read", "ai:chat"}, "viewer")
    }
    assert "lookup_cve" in viewer_tools
    assert "get_kev_summary" in viewer_tools
    assert "list_malware_metadata" in viewer_tools
    assert "get_service_status" in viewer_tools
    assert "get_malware_model_status" not in viewer_tools

    analyst_tools = {
        tool["name"]
        for tool in _tools_for_access({"intel:read", "malware:metadata:read"}, "analyst")
    }
    assert "get_malware_model_status" in analyst_tools


@pytest.mark.asyncio
async def test_assistant_cannot_execute_unregistered_or_write_tools() -> None:
    with pytest.raises(PermissionError):
        await execute_tool(
            "shell.exec",
            {"command": "id"},
            role="admin",
            scopes={"intel:read", "malware:metadata:read"},
        )

    with pytest.raises(PermissionError):
        await execute_tool(
            "malware.metadata.add",
            {"sha256": "a" * 64, "label": "malicious", "source": "chat"},
            role="admin",
            scopes={"intel:read", "malware:metadata:read"},
        )


@pytest.mark.asyncio
async def test_assistant_local_help_runs_without_external_provider(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ai_api_key", None)
    response = await run_assistant(
        "help",
        [],
        role="viewer",
        scopes={"intel:read", "malware:metadata:read"},
    )
    assert response["mode"] == "local"
    assert response["action"] == "help"
    assert response["executed"] is False
    assert "CISA KEV" in response["reply"]


@pytest.mark.asyncio
async def test_viewer_cannot_request_analyst_only_model_status() -> None:
    with pytest.raises(PermissionError):
        await execute_tool(
            "get_malware_model_status",
            {},
            role="viewer",
            scopes={"intel:read", "malware:metadata:read"},
        )
