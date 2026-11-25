def test_mcp_server_imports_and_registers_read_only_tools() -> None:
    from nanou_cyber_ai.mcp.server import mcp

    assert mcp is not None
