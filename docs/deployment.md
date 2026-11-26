# Hosting and deployment runbook

## Current hosting layout

- Web application: Vercel Python/FastAPI runtime; current Preview is protected by Vercel Authentication.
- Plan suitability: confirm the team's current Vercel plan before any non-personal or commercial use. Hobby is restricted to personal/non-commercial use under the current Terms of Service.
- Repository: `pascalnanousympathie-alt/nanou-cyber-defense-ai`, branch `feat/web-platform`.
- Database: PostgreSQL through the encrypted `NANOU_DATABASE_URL` environment variable.
- Static assets: bundled in the Python package and served same-origin by FastAPI.

The exact managed PostgreSQL provider/plan is not identified in this repository because the connection string is a protected secret. The live Preview readiness route has successfully returned `{"status":"ready","database":"postgresql"}`, which verifies a PostgreSQL connection from the deployed Preview. Do not infer the provider or its free-tier quota from that response.

Vercel Hobby is free for personal/non-commercial use only. It is not an appropriate plan for a commercial or third-party service operated for financial gain. Confirm the current terms before broad use: https://vercel.com/legal/terms

## Verified Vercel configuration

- Project: `nanou-cyber-defense-ai` (FastAPI framework).
- Team: `Nanou` (`nanou3`).
- Git connection: this repository is linked.
- Deployment protection: Vercel Authentication is enabled for **All Deployments**, including production URLs.
- `NANOU_DATABASE_URL`: Preview has a dedicated Preview-only Neon database secret; Production retains a separate Production-only sensitive secret. Values are not read or printed.
- `NANOU_BOOTSTRAP_TOKEN`: Preview-only; the one-time bootstrap has already been claimed.
- Latest verified Preview commit `8a9a3eff77e43ac51249ab4c3299e0b7bd03fc58`: **READY**.
- Latest Preview URL: https://nanou-cyber-defense-92smirzsz-nanou3.vercel.app

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
| First Administrator | Created; active, approved, role `admin` |
| Password rotation | Success event recorded in Preview audit |
| Restore drill | Encrypted post-rotation backup restored in an isolated PostgreSQL test project |
| Vercel SSO | Enabled for All Deployments |

GitHub Actions CI run 45635004451 completed:
- `test`: **PASS**, Ruff lint + Ruff format + pytest; 77 passed, 4 skipped.
- `ml-smoke`: **PASS**, 13 tests covering training, EMBER JSONL export and LAMDA Parquet preparation.

The dashboard is deployed as a protected Preview and its PostgreSQL readiness endpoint has been exercised. Automated tests cover bootstrap, login, approval, role restrictions, password rotation and logout. The connected Opera browser remains signed out; owner-browser acceptance cannot be claimed from that tab.

## First Administrator setup

1. Keep Vercel Authentication on **All Deployments**.
2. Open the protected Preview URL and sign in through Vercel.
3. In Vercel project environment settings, confirm or reset `NANOU_BOOTSTRAP_TOKEN` for the Preview environment. It must be a random value of at least 32 characters. Keep the raw value in your own password manager while completing the one-time setup; it is intentionally not recorded in Git, this runbook, or chat.
4. Open the Preview dashboard and submit the first Administrator form with your display name, email, a unique password of at least 12 characters, and the matching bootstrap token.
5. Check `/api/auth/me` again. Expected state after success: `authenticated:true`, Admin role, and `bootstrap_required:false`.
6. Register a separate test user. Approve it as Analyst from the Admin console, then verify Analyst inference/metadata permissions and that an Analyst cannot access Admin user/audit routes.
7. Verify logout revokes the session and that a fresh login works. Confirm audit events appear for registration, approval, login and logout.

The bootstrap token is separate from the Admin password. The backend disables bootstrap once it succeeds; a later token change does not reopen bootstrap.

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
- Before storing real user/security data, verify provider identity, billing/quota, automated backups, retention and a restore drill.
- Keep database credentials and bootstrap token in the hosting provider's encrypted secret store. Never paste their values in repository files, CI logs or support messages.

## Remaining launch gates

- Complete the owner-browser Admin Console acceptance and separate live test-user acceptance. CI covers the same authentication and RBAC paths using isolated test accounts.
- Complete Production-only database identity, backup/restore, quota and connection-permission review before any Production migration.
- Keep Vercel SSO enabled. Do not disable it to make an external AI provider work.
- If moving to public or commercial operation, select a hosting plan whose terms permit that use and conduct a separate security/operations review.
- Do not disable Vercel SSO protection or promote a production deployment until those launch gates are deliberately approved.
