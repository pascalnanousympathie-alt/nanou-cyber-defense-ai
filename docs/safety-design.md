# Safety design

## Malware data boundary

The project includes malware research, but only as:
- SHA-256 hashes and other non-executable indicators;
- sample labels, family names, first-seen timestamps and source attribution;
- vendor/public analysis report references;
- pre-extracted structural/statistical feature vectors (such as EMBER).

It does **not** store or execute PE, ELF, APK, PDF or script payloads. It does not implement packing, obfuscation, persistence, credential theft, ransomware encryption, exploitation, evasion, command-and-control, exfiltration, or DDoS.

## MCP controls

- Each tool has a stable identifier, risk class and required capability.
- Tool lookup fails closed for unknown names.
- The registry does not expose shell execution, arbitrary HTTP requests, filesystem traversal, process management, or credential access.
- External feed origins are constants in the connector implementation.
- Write operations are limited to validated local metadata records.

## Agent controls

Agents return findings and recommended remediation only. Applying a patch or changing a live system is a separate, human-approved workflow outside this MVP.

## Attack Simulation Manager

- Attack Simulation is a deterministic, local-only tabletop checklist generator, not a scanner or penetration-testing engine.
- It never sends network requests, probes hosts, executes exploits or payloads, tests credentials, runs malware, or changes systems.
- Only Admin can create/revoke exact-host allowlist entries. Every entry requires a declared authorization basis, explicit operator confirmation, and an expiry no more than 365 days away.
- Admin/Analyst simulation creation rechecks that the scope is active and unexpired; each request requires a fresh confirmation and is rate limited.
- Reports explicitly state `simulation_only`, zero verified findings, and `requires_manual_validation` for every check. MITRE ATT&CK IDs are threat-reference mappings, not claims of activity.
- Scope lifecycle and report creation are audit logged. Viewer and external Developer API credentials cannot access these routes.

See [Attack Simulation Manager](attack-simulation.md) for roles, routes, and operational limits.

## Dataset controls

- Do not commit raw malware samples or credentials.
- Keep downloaded datasets in an ignored cache directory.
- Verify checksums and upstream license terms before using any dataset.
- Keep dataset provenance, feature version, label source and evaluation split in the experiment record.
