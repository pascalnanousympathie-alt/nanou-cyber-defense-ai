# Project Status — Nanou Cyber Defense AI

Last verified: 2026-11-26 (UTC)

## Product scope

Nanou Cyber Defense AI is a defensive cybersecurity web platform. Its current workflows include vulnerability intelligence (NVD/CVE and CISA KEV), scoped MCP tool inventory, account/RBAC governance, AI assistant read-only defensive commands, pre-extracted malware-feature CSV validation, and local defensive tabletop reports.

Safety boundaries:
- No malware or executable upload/execution.
- No autonomous exploit runner, shell/process execution, intrusive scanning, or autonomous remediation.
- The malware feature workflow accepts a pre-extracted CSV row. It is not a direct APK scanner.
- Malware inference requires a trusted SHA-256-verified model artifact; no Production model readiness is claimed.
- Optional external AI-provider calls remain disabled until a safe server-side provider/access model is approved and configured.

## Repository and branches

Repository: pascalnanousympathie-alt/nanou-cyber-defense-ai.

- PR #1: feat/web-platform → main, Draft/Open, mergeable, unmerged. Head: 62f0b42bcec2a096186a84e18029048f3ce320da.
- PR #3: fix/admin-password-rotation → feat/web-platform, Draft/Open, mergeable, unmerged. Head at last verification: 590488b8afebfa740add47dbd8757588c8033634; base: 62f0b42bcec2a096186a84e18029048f3ce320da; 59 commits ahead / 0 behind.
- PR #3 contains PR #1's cyber UI through a normal merge commit. No force-push, no merge into main, and no Production promotion has occurred.

The repository did not contain the historical PROJECT_STATUS / PARALLEL_ORCHESTRATION files; this document and PARALLEL_ORCHESTRATION_RUNBOOK.md are the new coordination references.

## Latest verified UI and Preview

A protected Git Preview is READY:
- Deployment ID: dpl_HSoSTJv8aFcudRrLBtJw7XskY2PW.
- Preview URL: https://nanou-cyber-defense-ai-git-fix-admin-password-rotation-nanou3.vercel.app/
- Deployed Git commit: ad2f668c8323996a16366ade5b4f69f652f8d9e4.

The Preview commit is 11 commits behind current PR #3 head. Git comparison shows those differences are docs, tests and minor bootstrap CLI error handling; the app runtime, auth/API, database runtime verification, CSS and JavaScript application source are unchanged.

Live Opera evidence on this Preview:
- /ready: {"status":"ready","database":"postgresql"}.
- /api/auth/me: authenticated:false, user:null, bootstrap_required:false in the signed-out browser.
- Unauthenticated /api/admin/users: denied with “Sign in with an approved account.”
- Screenshot verifies deep-black/emerald-cyan HUD, grouped navigation, dimensional CSS typography and shield hero.
- Connected browser is signed out. Owner Admin Console/password-change acceptance and live Viewer/Analyst acceptance are not yet verified.

A manual Vercel API deployment request returned HTTP 402 api-deployments-free-per-day (more than 100 deployments, retry-after 24h). The Git-linked Preview above exists and is READY; an exact Preview for the latest docs/test HEAD was not created. No CLI bypass or paid upgrade was attempted. Keep SSO enabled.

## Latest CI and security evidence

On current PR #3 head 590488b8afebfa740add47dbd8757588c8033634:
- CI [45794790570](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45794790570): PASS.
  - Ruff lint and format: PASS.
  - Pytest: 123 passed / 4 skipped.
  - ML smoke: 13 passed.
  - pip-audit: no known vulnerabilities found.
- Security [45794790508](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45794790508): PASS.
  - Gitleaks full-history/refs: no leaks detected.
  - CodeQL Python and JavaScript/TypeScript: PASS, SARIF uploaded.
- GitHub Code Scanning alert overview was not independently inspected from the connected signed-out session. Do not claim zero open alerts.

## Database and Production status

Preview and Production use distinct Neon projects and separate sensitive Vercel database variables.

Production Neon project cold-resonance-28231813, PostgreSQL 17.12:
- Database nanou_cyber_defense: nine application tables, zero users and zero active sessions.
- Runtime role nanou_app owns the database and application tables, has CREATEROLE and CREATEDB, inherits BYPASSRLS through neon_superuser, and has broad table privileges including TRUNCATE.
- No Production snapshots or automated snapshot schedule were present; PITR history is six hours.
- Neon Free rejected Production branch protection because the protected-branch allowance was full.
- No Production schema, grants, rows, database URL, Vercel environment variables, or deployment were changed.

A least-privilege runtime-role prototype was tested only on the isolated restore-test Neon project. A NOLOGIN role passed SET ROLE, SELECT/INSERT/UPDATE/DELETE and sequence-usage smoke tests, without superuser, CREATEROLE, CREATEDB, BYPASSRLS, database/schema CREATE or TRUNCATE. The test row was deleted and zero leftovers remained. It is not a Production/Vercel login role.

PostgreSQL app startup is now schema-verify-only: it verifies required public tables and columns and does not run metadata.create_all. SQLite remains self-initializing for local development/tests. Initial PostgreSQL schema bootstrap is a separate command, python -m nanou_cyber_ai.storage.bootstrap, using protected NANOU_MIGRATION_DATABASE_URL. It is not a schema-upgrade engine; future ALTERs need explicit reviewed migrations.

## Production launch gates

Production remains BLOCKED until:
1. Create and restore a verified Production backup in an isolated destination; document RPO/RTO and rollback. No paid snapshot/upgrade without approval.
2. Create distinct migration-owner and restricted runtime login roles, test exact DDL/default grants/DML/sequences against a restored copy, then prepare a controlled cutover plan. Do not change Production ownership/grants before backup/restore proof.
3. Resolve Neon branch protection within the approved plan without weakening another service.
4. Preserve Vercel SSO; verify hosting plan, quota, monitoring, incident response and rollback.
5. Complete owner-browser Admin acceptance and separate Viewer/Analyst registration, approval, RBAC, logout and re-login checks.
6. Complete independent security review and inspect CodeQL alerts while signed in.
7. Only then consider merge to main and Production promotion, with explicit owner approval.

No Production launch, merge to main, SSO removal, paid plan upgrade, public release or real malware execution is authorized by this status document.
