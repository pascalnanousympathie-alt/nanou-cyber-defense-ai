# Attack Simulation Manager

## Purpose and safety boundary

The Attack Simulation Manager is a **local deterministic tabletop exercise builder**, not a penetration-testing engine. It produces scenario checklists, manual validation steps, remediation guidance, and MITRE ATT&CK reference mappings. It does not contact the target.

Every generated report is marked `simulation_only`. Each checklist item is marked `requires_manual_validation`; the report always records zero verified findings. The execution counters are fixed at zero for network requests, hosts contacted, exploits, payloads, and automatic changes. Malware execution is always false.

The feature does not perform port scans, service discovery, HTTP requests, vulnerability probes, exploit execution, credential testing, brute force, persistence, evasion, malware execution, shell commands, or production changes. The user-facing “intensity” selects the number of tabletop checklist items (3, 5, or 7); it is not an attack rate or technical intensity. Each profile also supplies SOC detection-design recommendations with suggested log sources, alert conditions, severity, and triage guidance. These are drafts only; they are not deployed, enabled, or tested detection rules.

## Scope and authorization

Only an Administrator can add or revoke a scope. An entry contains:
- A human-readable scope name.
- Exactly one canonical hostname, FQDN, or IP address (no URL, port, path, query, or CIDR).
- The authorization basis: owned asset, written permission, or isolated lab.
- An expiry date, between tomorrow and 365 days from the current date.
- An explicit authorization confirmation.

The confirmation and basis are operator-supplied assertions; the application does not independently verify legal ownership or inspect an authorization document. Store no passwords, access tokens, or confidential documents in a scope. Use a non-sensitive approval/ticket reference in the name only when useful. Expired or revoked scopes cannot be simulated. Authorization expiry is checked again server-side when each simulation is created. Scope revocation is a soft-disable operation and does not delete past audit/report history.

## Roles and controls

- **Admin**: create and revoke scopes, list scopes, create simulations, read simulation history.
- **Analyst**: view active scopes and create simulations; cannot create or revoke scopes.
- **Viewer / unauthenticated**: no access to these endpoints or the dashboard section.

Browser POST requests require the existing session and CSRF controls. The existing auth store enforces quotas: default 20 scope-creation attempts per Admin per day and 8 simulations per user per hour. Limits are configurable with `NANOU_ATTACK_SCOPE_CREATIONS_PER_DAY` and `NANOU_ATTACK_SIMULATIONS_PER_HOUR`.

## Profiles and API

Four deterministic profiles are available:
- `reconnaissance`
- `web_security`
- `api_security`
- `authentication`

Intensity values are `passive`, `low`, and `medium` (3/5/7 checks). Review duration is a planning field limited to 1–30 minutes.

All routes use the signed-in browser session; POST routes also require CSRF:
- `GET /api/attack/scopes`
- `POST /api/attack/scopes` — Admin only.
- `POST /api/attack/scopes/{scope_id}/revoke` — Admin only.
- `POST /api/attack/simulations` — Admin/Analyst.
- `GET /api/attack/simulations?limit=30` — Admin/Analyst.
- `GET /api/attack/simulations/{simulation_id}` — Admin/Analyst.

These are deliberately not part of the external Developer API or its Bearer scopes. The public API schema remains read-only.

## Audit and reporting

Scope creation/revocation and simulation creation write audit events containing the actor, action, target type, record ID, outcome, request ID, and IP digest. Raw IPs, authorization documents, credentials, chat text, and arbitrary request payloads are not copied into the audit event.

Reports are stored as deterministic JSON, can be reopened in the dashboard, and can be exported by the user as a JSON file. A report is a planning artifact only. A human reviewer must carry out any separately authorized manual checks and attach evidence in the organization's approved evidence system. Do not treat a tabletop report as a vulnerability scan or penetration-test result.
