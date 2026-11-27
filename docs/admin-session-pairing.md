# Admin-to-Termux read-only pairing

This feature connects a Termux operator process to an already authenticated Admin browser without exporting the browser session cookie, copying a password, or creating an unrestricted Admin session.

## Operator flow

1. Sign in through the protected Nanou Cyber Defense web platform in the owner's browser.
2. Open **Kaonty sy fidirana** and use **Hamorona pairing code** in the Admin-only Termux panel.
3. Copy the one-time code and paste it into the hidden prompt of the local Termux helper.
4. The helper exchanges the code over HTTPS, then stores the short-lived bridge bearer only in process memory.
5. Keep the Termux process running while the bridge is needed. Press **Ctrl+C** to stop it and request server-side revocation.

Install/run the helper from a repository checkout:

~~~bash
python3 scripts/nanou-admin-session.py
~~~

The pairing code is entered through getpass; it is not an argument, environment variable, file, or chat message. The helper does not print the bearer token or write it to disk.

## Token lifecycle and restrictions

- Pairing code: cryptographically random, shown once, expires after **90 seconds**, and is atomically consumed once.
- A new pairing request revokes prior unused pairing codes and active Admin bridge tokens belonging to that Admin.
- Exchange verifies the owner is still an active, approved Admin.
- Bridge token: distinct random bearer, hashed at rest in the existing api_keys table, expires after **15 minutes**, and is explicitly scoped to **admin:bridge:read**.
- Bridge requests are rate limited to **30 per minute**. The pairing creation and exchange routes also use the normal authentication rate limiter.
- Bridge routes are limited to identity, user-list and audit-list reads. They do not expose password hashes, browser session cookies, generic Developer API keys, bootstrap tokens, write operations, role changes, approvals, account deactivation, or arbitrary URL/shell/process controls.
- The normal Developer API requires the separate ncd_live_ token prefix and the existing intel:read, malware:metadata:read, or ai:chat scopes. A bridge token is not accepted as a Developer API token.
- The bridge self-revoke endpoint is available to the bridge itself. Changing the Admin password or role/active state revokes outstanding pairing/bridge credentials. A process crash is bounded by the 15-minute server expiry.
- Internal pairing/bridge rows use the pre-existing api_keys table and are excluded from the normal Developer API key listing. No Production DDL or new database table is required.

## Local transport

The helper exposes only a fixed action allowlist (ping, whoami, users, audit) on a Unix domain socket at $HOME/.local/run/nanou-cyber-admin/bridge.sock. Its dedicated parent directory is mode 0700 and the socket is mode 0600; the shared Termux temporary directory is not modified. The bearer token remains in memory; the socket is removed and revocation is attempted when the process stops.

This is intentionally read-only. Do not expand the bridge into general Admin write access or reuse it as a persistent automation identity. Any wider permissions require a separate reviewed authorization design and a new explicit approval.
