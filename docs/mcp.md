# MCP architecture and integration roadmap

## Current verified implementation

The optional Python MCP server currently uses the official Python SDK v2 over **stdio** and exposes two fixed-origin defensive intelligence tools: `nvd_get_cve` and `cisa_kev_check`. The permission-scoped registry also describes metadata read and local metadata write capabilities. This is not yet a hosted MCP gateway, connector marketplace, or public server publisher.

## Target architecture

1. **MCP control plane (FastAPI):** authenticated inventory of servers, tools, owners, visibility (`private`, `organization`, `public`), versions, health, approvals and audit history.
2. **MCP data plane:** protocol adapter supporting stdio for local hosts and Streamable HTTP for remote MCP clients. Keep the remote endpoint stateless where deployed on serverless infrastructure; long-lived workers belong in a separately operated container/service.
3. **Personal/private servers:** owner-scoped server records, per-server credentials, explicit tool allowlists, per-user grants and immediate revocation.
4. **Public servers:** publication review, signed/versioned manifests, abuse reporting, per-client quotas, rate limits, terms and monitoring. Public metadata does not imply public write access.
5. **Connector broker:** provider-specific OAuth authorization-code + PKCE where supported; encrypted refresh/access tokens in a server-side vault; exact redirect URI allowlists; minimum scopes; token rotation/revocation; no provider token returned to browser JavaScript.
6. **Connector adapters:** separate adapters for GitHub, Vercel, Gmail, Supabase, Firebase/Google Cloud, Microsoft 365 and PostgreSQL providers. Each adapter exposes a small, reviewed set of tools rather than generic arbitrary API or SQL access.
7. **Tunnel/remote bridge:** prefer an outbound-initiated tunnel (for example, a Cloudflare Tunnel deployment) with TLS, service identity, short-lived credentials and explicit destination allowlists. Do not expose a raw local port or unauthenticated reverse proxy. A Vercel serverless function is not a persistent tunnel daemon; operate the tunnel agent in a separately managed container or owner-controlled host.

## Protocol baseline (2026-07-28 specification)

For the remote transport, target the MCP Streamable HTTP specification rather than inventing a proprietary tunnel protocol. The current specification uses one MCP endpoint accepting POST requests and JSON or request-scoped SSE responses; validate the Origin header and authenticate every request. Implement the matching protocol-version metadata and conformance tests, and retain stdio for local desktop clients. Check compatibility with older clients before adopting newer protocol revisions.

For remote authorization, implement the MCP OAuth profile based on OAuth 2.1: HTTPS-only authorization/redirect endpoints, exact redirect URI allowlists, PKCE, protected-resource metadata, short-lived audience-bound access tokens, and token rotation. Never forward an incoming MCP bearer token to a provider API; the connector broker must use a separate provider-issued credential for that upstream service.

## Security invariants

- OAuth consent is performed by the owner in the provider's own authorization page; never request provider passwords, MFA codes or recovery codes in this application.
- Encrypt credentials at rest using a managed KMS/envelope-encryption design; restrict decrypt permission to the connector runtime. Never log tokens or include them in API responses.
- Every tool call is authorized against user, server, connector, resource and action scopes. Apply tenant isolation, CSRF protection for browser actions, replay protection, rate limits, request size/time limits and immutable audit events.
- Read operations are the default. Write operations require explicit scopes and, for sensitive actions, per-action confirmation. Destructive operations, payment, deployment promotion, repository merges and production database mutation remain disabled unless separately authorized.
- Do not provide arbitrary shell/process execution, arbitrary URL fetch, arbitrary SQL, malware execution, unrestricted filesystem access or autonomous exploitation through MCP.
- Treat all connector responses as untrusted input; validate schemas, cap response size, redact secrets and defend against prompt injection in fetched content.
- Public MCP tools must be reviewed, versioned, documented, monitored and revocable. Add per-client identity and abuse controls before public launch.

## Delivery phases

- **Phase A — catalog and governance:** server records, personal/public visibility metadata, tool schemas, owner/role permissions, audit and revoke controls. No external secrets.
- **Phase B — remote protocol:** Streamable HTTP endpoint with OAuth resource-server validation, tenant isolation and protocol conformance tests; retain stdio for local use.
- **Phase C — tunnel runtime:** outbound tunnel agent in a dedicated container/host, service-to-service identity, health checks and reconnect behavior. Do not run a persistent tunnel process inside Vercel Functions.
- **Phase D — connectors:** one provider at a time, beginning with read-only GitHub repository metadata and Vercel project/deployment metadata, then Gmail read-only search, Supabase schema/read-only queries, Firebase project metadata. Expand scopes only after acceptance tests.
- **Phase E — publication:** personal server export first, organization sharing next, public directory only after security review, rate limiting and incident response are ready.

## Current status

The local stdio server and registry exist. The web Developer Center currently displays this target architecture as a roadmap only. No public MCP endpoint, tunnel, provider OAuth connection, connector token vault or public marketplace has been created yet.
