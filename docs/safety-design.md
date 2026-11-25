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

## Dataset controls

- Do not commit raw malware samples or credentials.
- Keep downloaded datasets in an ignored cache directory.
- Verify checksums and upstream license terms before using any dataset.
- Keep dataset provenance, feature version, label source and evaluation split in the experiment record.
