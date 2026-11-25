# Attack Simulation Manager

The dashboard includes a Red Team / Blue Team training panel for Admin and Analyst accounts. Its execution engine is **offline and synthetic only**: it creates sample telemetry and detection guidance for tabletop and SOC workflow exercises. It does not send packets, resolve DNS, open sockets, make HTTP requests, probe ports, attempt authentication, exploit vulnerabilities, execute shell commands, or run malware.

## Supported profiles

- `reconnaissance` — synthetic discovery and scanning indicators.
- `web_security` — synthetic web application security alerts.
- `api_security` — synthetic API authorization, validation, and throttling alerts.
- `authentication` — synthetic identity and sign-in alerts.

Each profile maps selected signals to MITRE ATT&CK technique identifiers and includes detection logic plus defensive recommendations. These are simulated signals, not evidence that a real target is vulnerable or compromised.

## Scope configuration

Set `NANOU_SIMULATION_ALLOWED_TARGETS` to a comma-separated list of opaque lab identifiers, for example:

```bash
NANOU_SIMULATION_ALLOWED_TARGETS=local-lab,staging-lab
```

Identifiers are lowercase letters, digits, and hyphens only (maximum 48 characters). URLs, hostnames, IP addresses, and arbitrary target strings are not accepted. The identifiers label isolated training scopes; this manager never resolves them or connects to them. The default is `local-lab`.

## Authorization and controls

Every run requires an Admin or Analyst session, an allowlisted target identifier, an authorization reference (such as a change ticket), and an explicit authorization acknowledgement. Requests are limited to 10 runs per user per hour by default (`NANOU_SIMULATION_REQUESTS_PER_HOUR`; configurable from 1 to 60).

Intensity is limited to:
- `passive` — one synthetic signal;
- `low` — two synthetic signals;
- `medium` — three synthetic signals.

The run endpoint records an audit event with the actor, selected target identifier, request ID, and simulated/blocked outcome. The authorization reference and raw request body are not copied into the audit record. Run output is returned to the active session and is not retained as a simulation-history database record.

## Endpoints

- `GET /api/simulations/config` — authenticated Admin/Analyst simulation configuration.
- `POST /api/simulations/run` — generate one offline synthetic report.

These endpoints are session/CSRF protected and deliberately excluded from the public Developer API and OpenAPI contract. No remote API-key scope can start a simulation.

## Validation

Tests cover target allowlisting, invalid profile/intensity, authorization acknowledgement, role/session protection, synthetic output, no-target-contact assertions, audit events, and UI assets.
