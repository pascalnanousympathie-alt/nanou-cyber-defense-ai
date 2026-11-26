# Hosting and deployment runbook

## Current hosting layout

- Web application: Vercel Python/FastAPI runtime; current Preview is protected by Vercel Authentication.
- Plan suitability: confirm the team's current Vercel plan before any non-personal or commercial use. Hobby is restricted to personal/non-commercial use under the current Terms of Service.
- Repository: `pascalnanousympathie-alt/nanou-cyber-defense-ai`.
- Current candidate: PR #3 branch `fix/admin-password-rotation`, based on `feat/web-platform`; PR #1 (`feat/web-platform` → `main`) and PR #3 remain Draft/Open and unmerged.
- Database: Neon PostgreSQL. Preview and Production use separate, environment-scoped sensitive `NANOU_DATABASE_URL` entries.
- Static assets: bundled in the Python package and served same-origin by FastAPI.

The Preview database is the dedicated Neon project `nanou-cyber-defense-preview`; the separate original Production project remains isolated. The connection strings remain secret and were never read or printed. The live Preview readiness route verifies a PostgreSQL connection, but does not prove Production readiness or a Production SLA.

Vercel Hobby is free for personal/non-commercial use only. It is not an appropriate plan for a commercial or third-party service operated for financial gain. Confirm the current terms before broad use: https://vercel.com/legal/terms

## Verified Vercel configuration

- Project: `nanou-cyber-defense-ai` (FastAPI framework).
- Team: `Nanou` (`nanou3`).
- Git connection: this repository is linked.
- Deployment protection: Vercel Authentication is enabled for **All Deployments**, including production URLs.
- `NANOU_DATABASE_URL`: Preview has a dedicated Preview-only Neon database secret; Production retains a separate Production-only sensitive secret. Values are not read or printed.
- `NANOU_BOOTSTRAP_TOKEN`: Preview-only; one-time bootstrap is already claimed and the token is no longer needed for routine operation.
- Latest verified Preview commit `6152cfaa5836484576a2fa33ebb9585bf2c9a695`: **READY** (documentation-updated PR head).
- Latest Preview URL: https://nanou-cyber-defense-jm1fztyb8-nanou3.vercel.app

The secret values are not stored in Git or this document. Preview and Production database variables are separated. The Preview PostgreSQL provider and encrypted backup/restore have been checked; Production database readiness and restore have not been exercised. A Preview readiness check is not proof of a Production SLA.

The Vercel project reports SSO protection for all deployments and `live=false`. An older protected production deployment exists, but the current work is validated on the Preview branch. Do not remove the SSO gate or expose an unprotected URL as part of this runbook.

## Live verification already completed

Using the protected Preview in the connected browser:

| Check | Result |
|---|---|
| Vercel build | READY |
| Dashboard `/` | Loaded; API status online |
| `/ready` | `{"status":"ready","database":"postgresql"}` |
| `/api/auth/me` in the connected Opera tab | `authenticated:false`, `user:null`, `bootstrap_required:false` (signed-out browser) |
| Unauthenticated `/api/admin/users` | Correctly denied: `Sign in with an approved account.` |
| First Administrator | Created; active, approved, role `admin` |
| Password rotation | Success event recorded in Preview audit |
| Restore drill | Encrypted post-rotation backup restored in an isolated PostgreSQL test project |
| Vercel SSO | Enabled for All Deployments |

GitHub Actions PR validation run [45779479304](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45779479304) on commit `c444538bc3be01977aaf6942f1fe537a2d7547cf` completed successfully:
- `test`: **PASS** — Ruff lint, Ruff format, **116 passed / 4 skipped**.
- `ml-smoke`: **PASS** — **13 passed**.
- `dependency-audit`: **PASS** — pip-audit reported **No known vulnerabilities found** for the installed third-party Python dependencies.
- Security regression tests cover keyed HMAC fingerprints, Content-Length rejection and streamed/chunked request-body limits (2 MiB).

The dashboard is deployed as a protected Preview and its PostgreSQL readiness endpoint has been exercised. Automated tests cover bootstrap, login, approval, role restrictions, password rotation, logout, HMAC fingerprinting and request-size enforcement. The connected Opera browser remains signed out; the Admin console has not been live-accepted in the owner's authenticated browser. The Preview DB audit records successful password rotation and login; that does not prove the currently connected Opera tab owns the remaining valid session.

## Administrator acceptance status

The first Administrator account has already been created on the dedicated Preview database. It is active, approved and has role `admin`; `bootstrap_claimed=true`. A successful password-change event and successful login event are present in Preview audit history. Do not reset the bootstrap token or recreate the initial Administrator.

The connected Opera browser is signed out (`/api/auth/me` returns `authenticated:false`, `user:null`, `bootstrap_required:false`). The unauthenticated Admin users endpoint correctly refuses access. CI has passed the isolated bootstrap/login/approval/RBAC/password-change/logout test suite, but this is not a substitute for acceptance in the owner's own authenticated browser. Never bypass authentication or reuse a previously disclosed password.

After owner sign-in through Vercel SSO and the application login, inspect the Admin governance/audit workspace, then use a separate test account to accept Viewer/Analyst permissions and logout/re-login. These checks must be carried out with the owner's own credentials in the browser; no password or session token should be shared in chat.

## Data preparation and model constraints

The feature workflow accepts only one-row UTF-8 CSV text up to 1 MiB:
- EMBER2024: exactly 2,568 numeric feature columns in the trained order.
- LAMDA: exactly 4,561 signed-int8 feature columns in the trained order.
- Optional `sha256` and `label` fields are metadata only.
- Unknown/reordered/missing columns, multiple rows, non-finite values, invalid hashes and out-of-range LAMDA values are rejected.
- CSV uploads are not persisted. APK, executable or model binaries are not accepted or executed.

This is not direct APK scanning. APK-to-feature extraction and Android/on-device integration are not part of the verified workflow.

## Database safety and operations

- Hosted/serverless execution refuses SQLite fallback; `NANOU_DATABASE_URL` must resolve to a durable PostgreSQL service.
- The Preview `/ready` endpoint verified a PostgreSQL connection. Production readiness has not been exercised in this task.
- SQLAlchemy creates the initial tables on startup. Introduce reviewed migrations for future schema evolution.
- Preview: a post-rotation encrypted AES-256-GCM backup was decrypted and restored into a separate isolated Neon PostgreSQL test project. The restore check verified 7 application tables, one Admin, four audit events, and `bootstrap_claimed=true`.
- Preview PITR history retention is 6 hours; no paid manual snapshot or scheduled snapshot was provisioned.
- Production backup/restore has not been exercised. Confirm Production provider settings, billing/quota, automated backups, retention and restore procedure before any Production data migration.
- Keep database credentials and bootstrap token in the hosting provider's encrypted secret store. Never paste their values in repository files, CI logs or support messages.

## Remaining launch gates

- Owner-browser Admin Console acceptance and live Viewer/Analyst acceptance remain unverified because the connected Opera browser is signed out. Automated CI tests are green but do not prove that owner's browser session.
- PR #3 must be reviewed and integrated into PR #1's branch; then the combined candidate requires a fresh CI run and review. PR #1 still requires review before any merge to `main`.
- Before any Production migration: verify Production database identity/permissions, create and restore a Production backup in an isolated destination, review retention/quota, and prepare a reviewed migration/rollback plan.
- A broader SAST/secrets/container scan and operational threat-model review are not covered by `pip-audit`; no claim of a complete security audit is made.
- External AI provider access, direct APK scanning and verified malware-model inference remain unconfigured/unimplemented. The current malware workflow validates pre-extracted CSV features only.
- Keep Vercel SSO enabled. Do not expose a public deployment or promote Production until an approved access design, hosting-plan suitability and all launch gates are reviewed.
- Do not incur paid plan, snapshot, provider or model costs without explicit owner approval.
