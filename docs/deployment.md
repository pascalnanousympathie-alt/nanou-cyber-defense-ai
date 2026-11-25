# Hosting and deployment runbook

## Prototype layout

- Application: Vercel Python/FastAPI runtime.
- Persistent database: dedicated Neon PostgreSQL Free project.
- Static assets: bundled in the Python package and served same-origin.

Neon Free is suitable for a light prototype with finite storage and compute allowances; monitor the account quotas and autosuspend behavior. Vercel Hobby is free but only for personal/non-commercial use. Neither plan is a production SLA.

Render Free is not selected as the primary host: services sleep after inactivity and the filesystem is ephemeral.

## Provisioned resources

- Neon project: `nanou-cyber-defense-ai` (PostgreSQL 17, Singapore region).
- Neon database: `nanou_cyber_defense`.
- Neon role: `nanou_app`.
- Vercel project: `nanou-cyber-defense-ai`, linked to this repository.
- Vercel team: `Nanou`.
- Vercel deployment protection: Authentication required for **All Deployments**.
- Vercel encrypted environment variable: `NANOU_DATABASE_URL`, targets Preview and Production.

The connection string is stored in Vercel's encrypted environment-variable store and is not committed to the repository or printed in this runbook.

## First protected deployment

1. Push the reviewed `feat/web-platform` commit.
2. Create a Preview deployment from that exact branch/commit.
3. Verify build status and inspect `/health`, `/ready`, `/`, `/api/auth/csrf` and `/api/auth/me` through the protected deployment.
4. Set a unique 32+ character NANOU_BOOTSTRAP_TOKEN as an encrypted Vercel environment variable for Preview. Keep the value in the Vercel secret store; do not paste it into Git, logs or chat.
5. While Vercel Authentication still protects the deployment, open the protected URL, reveal/copy the bootstrap token from Vercel environment-variable settings, and create the first Administrator using a unique password of at least 12 characters.
6. Verify login, logout, registration, approval, role restrictions, audit events and persistence across a fresh session.
7. Keep deployment protection enabled until the intended audience and hosting terms are confirmed. Do not disable protection simply to expose the initial bootstrap endpoint.

## Database safety

Hosted execution refuses SQLite fallback; a durable PostgreSQL `NANOU_DATABASE_URL` is mandatory. SQLAlchemy creates the initial tables on startup. For future schema evolution, introduce reviewed migrations. Test backups and restores before storing real user/security data.

## Remaining launch gates

- Verify CI on the final commit.
- Verify Vercel preview build and health/readiness.
- Complete first Admin bootstrap through the protected browser.
- Confirm persistence and restore process.
- Confirm Hobby plan use is personal/non-commercial only. Move to a suitable plan/provider before commercial or third-party operation.
- Do not claim direct APK scanning: current workflow is pre-extracted CSV only.
