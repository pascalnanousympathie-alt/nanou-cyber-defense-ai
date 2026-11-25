# Security Policy

## Reporting

Please do not publish credentials, private vulnerability details, personal data, or live malware samples in issues. For a sensitive report, contact the repository owner privately through GitHub's security reporting feature if enabled.

## Scope

This project is defensive. Supported inputs are vulnerability identifiers, hashes, metadata, and pre-extracted static features. It must not execute submitted files or provide attack automation.

## Safe handling

- Never commit API keys, tokens, private reports, or `.env` files.
- Do not upload executable malware samples to issues, pull requests, or this repository.
- Keep any local research corpus outside the repository and use an isolated analysis environment.
- Treat all external feeds and model output as untrusted data.
