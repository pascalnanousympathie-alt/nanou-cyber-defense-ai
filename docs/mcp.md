# MCP server

The optional MCP server uses the official Python SDK v2 and **stdio transport**. Install it with:

```bash
python -m pip install -e ".[mcp]"
python -m nanou_cyber_ai.mcp.server
```

It exposes two read-only tools:
- `nvd_get_cve(cve_id)` — fixed-origin lookup against NIST NVD.
- `cisa_kev_check(cve_id)` — check the CISA KEV catalog.

The server intentionally does not expose shell execution, arbitrary HTTP fetches, file reads, process management, payload execution, exploit generation, credential access, or remote-control tools. Run it as a local stdio subprocess under a trusted MCP host. Do not wrap it in a public HTTP endpoint without authentication, TLS, authorization and rate limiting.

The optional SDK follows the official Python SDK v2 API: `from mcp.server import MCPServer`. See https://github.com/modelcontextprotocol/python-sdk and https://py.sdk.modelcontextprotocol.io/ before adding transports or tools.
