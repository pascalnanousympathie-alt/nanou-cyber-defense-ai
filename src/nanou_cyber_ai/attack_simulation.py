"""Deterministic, local-only security scenario simulations.

This module never opens sockets, performs scans, runs exploits, or executes payloads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

PROFILE_CATALOG: dict[str, dict[str, Any]] = {
    "reconnaissance": {
        "label": "Reconnaissance & asset exposure",
        "description": (
            "Tabletop review of asset inventory, exposure ownership, and "
            + "information disclosure."
        ),
        "checks": [
            {
                "id": "REC-01",
                "title": "Asset inventory ownership",
                "scenario": "A threat actor builds a target list from incomplete asset records.",
                "validation": (
                    "Manually confirm every in-scope hostname/IP has an owner, purpose, and "
                    + "review date."
                ),
                "remediation": "Maintain an approved asset inventory and retire unowned records.",
                "priority": "high",
            },
            {
                "id": "REC-02",
                "title": "External service register",
                "scenario": "An undocumented service increases the organization's exposure.",
                "validation": (
                    "Compare the approved service register with the architecture and cloud "
                    + "inventory; do not probe hosts."
                ),
                "remediation": (
                    "Require an owner and change record for every externally reachable "
                    + "service."
                ),
                "priority": "high",
            },
            {
                "id": "REC-03",
                "title": "Public information minimization",
                "scenario": (
                    "Public documents disclose environment names or sensitive operational "
                    + "details."
                ),
                "validation": (
                    "Review approved public pages and documents for accidental technical "
                    + "disclosures."
                ),
                "remediation": (
                    "Remove secrets and unnecessary infrastructure details from public "
                    + "material."
                ),
                "priority": "medium",
            },
            {
                "id": "REC-04",
                "title": "Exposure ownership and expiry",
                "scenario": "A temporary asset remains in use after its approval expires.",
                "validation": (
                    "Check named owner, business purpose, and expiry date for each exposed "
                    + "asset."
                ),
                "remediation": (
                    "Apply an expiry workflow and require periodic owner recertification."
                ),
                "priority": "medium",
            },
            {
                "id": "REC-05",
                "title": "Monitoring coverage",
                "scenario": (
                    "A change to an approved asset is not reflected in the security "
                    + "monitoring plan."
                ),
                "validation": (
                    "Confirm asset changes produce a review task and are covered by "
                    + "approved monitoring."
                ),
                "remediation": "Connect asset lifecycle events to the security review process.",
                "priority": "medium",
            },
            {
                "id": "REC-06",
                "title": "Third-party boundary",
                "scenario": (
                    "An inventory entry is mistaken for authorization to test a "
                    + "supplier-owned system."
                ),
                "validation": (
                    "Verify written permission and precise scope for every third-party "
                    + "asset."
                ),
                "remediation": (
                    "Exclude third-party systems until the owner grants explicit written "
                    + "authorization."
                ),
                "priority": "high",
            },
            {
                "id": "REC-07",
                "title": "Reconnaissance alert readiness",
                "scenario": "Suspicious discovery activity is not escalated to the security team.",
                "validation": (
                    "Review whether the SOC has an approved alert triage procedure for "
                    + "discovery signals."
                ),
                "remediation": (
                    "Document alert ownership, triage severity, evidence retention, and "
                    + "escalation contacts."
                ),
                "priority": "low",
            },
        ],
        "attack_mapping": [
            {
                "id": "T1590",
                "tactic": "Reconnaissance",
                "technique": "Gather Victim Network Information",
            },
            {"id": "T1595", "tactic": "Reconnaissance", "technique": "Active Scanning"},
        ],
    },
    "web_security": {
        "label": "Web application security",
        "description": (
            "Non-invasive control review for input handling, authorization, "
            + "sessions, and browser protections."
        ),
        "checks": [
            {
                "id": "WEB-01",
                "title": "Input validation boundary",
                "scenario": "Untrusted input reaches a sensitive application operation.",
                "validation": (
                    "Review schemas, server-side validation, parameterized queries, and "
                    + "negative tests."
                ),
                "remediation": (
                    "Enforce typed allowlisted inputs and parameterized data access on the "
                    + "server."
                ),
                "priority": "high",
            },
            {
                "id": "WEB-02",
                "title": "Authorization at object boundary",
                "scenario": (
                    "A signed-in user can reference an object outside their permitted "
                    + "workspace."
                ),
                "validation": (
                    "Review object ownership checks and role tests for every object-level "
                    + "operation."
                ),
                "remediation": (
                    "Authorize every object lookup against the current principal and "
                    + "tenant."
                ),
                "priority": "critical",
            },
            {
                "id": "WEB-03",
                "title": "Session lifecycle",
                "scenario": "A revoked or expired session remains usable.",
                "validation": (
                    "Review session expiry, logout revocation, cookie attributes, and "
                    + "role-change invalidation."
                ),
                "remediation": (
                    "Revoke sessions on logout, expiry, disablement, and privilege changes."
                ),
                "priority": "high",
            },
            {
                "id": "WEB-04",
                "title": "Browser security headers",
                "scenario": "Weak browser policy increases the impact of content injection.",
                "validation": (
                    "Review CSP, frame restrictions, MIME sniffing, referrer policy, and "
                    + "HSTS where applicable."
                ),
                "remediation": (
                    "Adopt a restrictive tested CSP and security headers without unsafe "
                    + "wildcards."
                ),
                "priority": "medium",
            },
            {
                "id": "WEB-05",
                "title": "CSRF and origin checks",
                "scenario": (
                    "A state-changing request is accepted without a valid anti-CSRF "
                    + "control."
                ),
                "validation": (
                    "Review cookie-authenticated writes, token comparison, SameSite policy, "
                    + "and Origin validation."
                ),
                "remediation": (
                    "Require CSRF protection for browser writes and narrowly scope any "
                    + "machine-auth exception."
                ),
                "priority": "high",
            },
            {
                "id": "WEB-06",
                "title": "Abuse throttling",
                "scenario": "A public endpoint can be used for excessive requests.",
                "validation": (
                    "Review per-account and per-key limits, bounded request sizes, and "
                    + "rate-limit audit events."
                ),
                "remediation": (
                    "Apply server-side quotas, request-size limits, and safe backoff "
                    + "responses."
                ),
                "priority": "medium",
            },
            {
                "id": "WEB-07",
                "title": "Error and secret disclosure",
                "scenario": "An error response or browser log exposes internal values.",
                "validation": (
                    "Review production error handling and confirm secrets are absent from "
                    + "UI, telemetry, and audit logs."
                ),
                "remediation": (
                    "Return generic errors and redact credentials, tokens, and sensitive "
                    + "payloads."
                ),
                "priority": "high",
            },
        ],
        "attack_mapping": [
            {
                "id": "T1190",
                "tactic": "Initial Access",
                "technique": "Exploit Public-Facing Application",
            },
            {
                "id": "T1078",
                "tactic": "Defense Evasion / Persistence / Privilege Escalation / Initial Access",
                "technique": "Valid Accounts",
            },
        ],
    },
    "api_security": {
        "label": "API security",
        "description": (
            "Design-level review of API authentication, scopes, object access, "
            + "input validation, and abuse controls."
        ),
        "checks": [
            {
                "id": "API-01",
                "title": "Token storage and lifecycle",
                "scenario": (
                    "An API credential is exposed or remains valid beyond its intended "
                    + "lifetime."
                ),
                "validation": (
                    "Review server-side hashing, one-time display, expiry, revocation, and "
                    + "owner disablement."
                ),
                "remediation": (
                    "Store only token hashes, show secrets once, and enforce expiry and "
                    + "revocation."
                ),
                "priority": "critical",
            },
            {
                "id": "API-02",
                "title": "Least-privilege scopes",
                "scenario": "An integration has broader data access than its task requires.",
                "validation": "Map every route to a required scope and test missing-scope denial.",
                "remediation": (
                    "Use narrow read scopes and deny unknown or write scopes by default."
                ),
                "priority": "high",
            },
            {
                "id": "API-03",
                "title": "Object-level authorization",
                "scenario": "A caller can request another user's object by changing an identifier.",
                "validation": "Review ownership and tenant checks for all identifier-based routes.",
                "remediation": (
                    "Bind every object lookup to the authenticated principal and permitted "
                    + "scope."
                ),
                "priority": "critical",
            },
            {
                "id": "API-04",
                "title": "Schema and payload limits",
                "scenario": "Oversized or unexpected fields reach business logic.",
                "validation": (
                    "Review strict schemas, field lengths, content types, and maximum "
                    + "request size."
                ),
                "remediation": (
                    "Reject extra fields, malformed values, and oversized bodies before "
                    + "processing."
                ),
                "priority": "high",
            },
            {
                "id": "API-05",
                "title": "Rate limiting and quotas",
                "scenario": "An integration exhausts resources through repeated requests.",
                "validation": (
                    "Review per-key and per-principal quotas plus observable 429 responses."
                ),
                "remediation": "Set bounded quotas and alert on sustained abuse patterns.",
                "priority": "medium",
            },
            {
                "id": "API-06",
                "title": "Audit and correlation",
                "scenario": "A sensitive API action cannot be attributed to an actor or request.",
                "validation": (
                    "Check that action names, actor IDs, target IDs, outcomes, and request "
                    + "IDs are recorded without payload secrets."
                ),
                "remediation": (
                    "Use structured audit events and redact request bodies and credentials."
                ),
                "priority": "medium",
            },
            {
                "id": "API-07",
                "title": "Transport and caching",
                "scenario": (
                    "Sensitive API responses are cached or transported without required "
                    + "protections."
                ),
                "validation": (
                    "Review TLS termination, HSTS, and Cache-Control for authenticated "
                    + "data."
                ),
                "remediation": "Enforce HTTPS and no-store for sensitive authenticated responses.",
                "priority": "high",
            },
        ],
        "attack_mapping": [
            {
                "id": "T1190",
                "tactic": "Initial Access",
                "technique": "Exploit Public-Facing Application",
            },
            {
                "id": "T1078",
                "tactic": "Defense Evasion / Persistence / Privilege Escalation / Initial Access",
                "technique": "Valid Accounts",
            },
        ],
    },
    "authentication": {
        "label": "Authentication & identity",
        "description": (
            "Tabletop review for account takeover paths, authentication hygiene, "
            + "and session governance."
        ),
        "checks": [
            {
                "id": "AUTH-01",
                "title": "Credential policy",
                "scenario": "Weak or reused credentials increase the chance of account compromise.",
                "validation": (
                    "Review password length, breached-password controls, and approved MFA "
                    + "coverage."
                ),
                "remediation": (
                    "Require strong password handling and MFA for privileged and sensitive "
                    + "accounts."
                ),
                "priority": "high",
            },
            {
                "id": "AUTH-02",
                "title": "Password hashing",
                "scenario": "A database disclosure exposes passwords that are cheaply recoverable.",
                "validation": (
                    "Review approved adaptive password hashing parameters and per-password "
                    + "salts."
                ),
                "remediation": (
                    "Use a maintained adaptive password hash and benchmark cost settings "
                    + "safely."
                ),
                "priority": "critical",
            },
            {
                "id": "AUTH-03",
                "title": "Login throttling",
                "scenario": "Repeated failed authentication attempts are not slowed or surfaced.",
                "validation": (
                    "Review per-account and source throttling, generic errors, and lockout "
                    + "recovery."
                ),
                "remediation": "Use bounded rate limits and alert on unusual failure patterns.",
                "priority": "high",
            },
            {
                "id": "AUTH-04",
                "title": "Session invalidation",
                "scenario": "A session continues after account disablement or role reduction.",
                "validation": (
                    "Review server-side session checks after logout, disablement, and role "
                    + "changes."
                ),
                "remediation": "Invalidate sessions immediately when authorization state changes.",
                "priority": "high",
            },
            {
                "id": "AUTH-05",
                "title": "Privileged account separation",
                "scenario": "Routine access is performed with a standing administrator identity.",
                "validation": (
                    "Review separate admin identities, approval paths, and least privilege."
                ),
                "remediation": (
                    "Separate daily and privileged identities and require approval for "
                    + "elevation."
                ),
                "priority": "medium",
            },
            {
                "id": "AUTH-06",
                "title": "Authentication event detection",
                "scenario": "Use of a valid account from an unusual context is not investigated.",
                "validation": (
                    "Review alerting for anomalous sign-in, privilege changes, and "
                    + "suspicious session use."
                ),
                "remediation": (
                    "Define detection thresholds, triage ownership, and response playbooks."
                ),
                "priority": "medium",
            },
            {
                "id": "AUTH-07",
                "title": "Recovery flow integrity",
                "scenario": "An account recovery workflow bypasses normal identity verification.",
                "validation": (
                    "Review recovery proofing, token expiry, one-time use, and notification "
                    + "controls."
                ),
                "remediation": (
                    "Use short-lived one-time recovery tokens and notify account owners."
                ),
                "priority": "high",
            },
        ],
        "attack_mapping": [
            {
                "id": "T1078",
                "tactic": "Defense Evasion / Persistence / Privilege Escalation / Initial Access",
                "technique": "Valid Accounts",
            },
            {"id": "T1110", "tactic": "Credential Access", "technique": "Brute Force"},
        ],
    },
}


DETECTION_CATALOG: dict[str, list[dict[str, str]]] = {
    "reconnaissance": [
        {
            "rule_id": "ASSET-NEW-PUBLIC",
            "name": "New external asset without owner",
            "log_sources": "Cloud control-plane audit, asset inventory, CMDB",
            "signal": (
                "A newly published external asset has no recorded owner, business "
                + "purpose, or approval."
            ),
            "alert_when": "A new external asset fails the ownership/approval reconciliation.",
            "severity": "high",
            "triage": (
                "Confirm business ownership and change record; isolate only through an "
                + "approved change process."
            ),
        },
        {
            "rule_id": "DNS-DISCOVERY-SPIKE",
            "name": "Unusual DNS discovery volume",
            "log_sources": "Recursive DNS logs, resolver security events",
            "signal": (
                "A client creates a DNS query pattern materially outside its "
                + "established baseline."
            ),
            "alert_when": "A baseline-adjusted query or NXDOMAIN burst crosses the SOC threshold.",
            "severity": "medium",
            "triage": (
                "Correlate device identity, user, approved inventory, and endpoint "
                + "telemetry."
            ),
        },
        {
            "rule_id": "THIRD-PARTY-SCOPE",
            "name": "Third-party asset without test authorization",
            "log_sources": "Asset register, vendor register, approval/ticket system",
            "signal": (
                "A proposed assessment target is owned by a supplier but has no current "
                + "written authorization."
            ),
            "alert_when": (
                "A third-party target is added to an assessment plan without an "
                + "approval reference."
            ),
            "severity": "high",
            "triage": (
                "Block assessment scheduling and obtain explicit written permission "
                + "from the asset owner."
            ),
        },
    ],
    "web_security": [
        {
            "rule_id": "WEB-WAF-INJECTION",
            "name": "Repeated web injection signatures",
            "log_sources": "WAF events, reverse-proxy access logs, application request IDs",
            "signal": (
                "Repeated SQLi/XSS signature matches from one source or account, "
                + "including blocked events."
            ),
            "alert_when": (
                "Signature events exceed a configurable source/account baseline in a "
                + "rolling window."
            ),
            "severity": "high",
            "triage": (
                "Review redacted WAF evidence, correlate request IDs, and confirm "
                + "whether controls blocked the requests."
            ),
        },
        {
            "rule_id": "WEB-SESSION-REVOKE",
            "name": "Use of revoked session",
            "log_sources": (
                "Authentication audit, session lifecycle events, application "
                + "authorization logs"
            ),
            "signal": (
                "A session token or session identifier is presented after logout, "
                + "expiry, disablement, or role change."
            ),
            "alert_when": "A revoked-session validation event is recorded for a protected route.",
            "severity": "critical",
            "triage": (
                "Revoke related sessions, verify account state, and preserve the event "
                + "chain without logging tokens."
            ),
        },
        {
            "rule_id": "WEB-ERROR-BURST",
            "name": "Application error and denial spike",
            "log_sources": "Reverse proxy, WAF, application error telemetry",
            "signal": (
                "Unusual 4xx/5xx bursts correlate with security-rule denials or a "
                + "single application path."
            ),
            "alert_when": (
                "Error ratios exceed the service baseline and correlate with security "
                + "events."
            ),
            "severity": "medium",
            "triage": (
                "Trace request IDs, inspect sanitized exception classes, and confirm no "
                + "secrets entered logs."
            ),
        },
    ],
    "api_security": [
        {
            "rule_id": "API-AUTHZ-DENY",
            "name": "API authorization denial spike",
            "log_sources": "API gateway, application RBAC audit, tenant authorization events",
            "signal": (
                "A principal or API key generates repeated 401/403 responses across "
                + "protected resources."
            ),
            "alert_when": (
                "Denied requests exceed per-principal baseline or touch multiple "
                + "object/tenant boundaries."
            ),
            "severity": "high",
            "triage": (
                "Validate principal scopes, tenant ownership checks, and key revocation "
                + "status."
            ),
        },
        {
            "rule_id": "API-RATE-LIMIT",
            "name": "Sustained API quota exhaustion",
            "log_sources": "API gateway rate-limit counters, service metrics",
            "signal": "A key or user repeatedly reaches 429 responses across consecutive windows.",
            "alert_when": (
                "429 rate exceeds the configured service threshold for a sustained "
                + "interval."
            ),
            "severity": "medium",
            "triage": (
                "Confirm expected integration traffic, identify the owning team, and "
                + "preserve quota metadata."
            ),
        },
        {
            "rule_id": "API-OBJECT-BOUNDARY",
            "name": "Cross-tenant object access denial",
            "log_sources": "Application object-authorization audit, API gateway request IDs",
            "signal": (
                "Object access is denied because the object does not belong to the "
                + "authenticated tenant/principal."
            ),
            "alert_when": (
                "Repeated cross-tenant denials occur for the same principal or resource "
                + "family."
            ),
            "severity": "critical",
            "triage": (
                "Review object-ownership predicates and access logs; do not log object "
                + "contents or bearer tokens."
            ),
        },
    ],
    "authentication": [
        {
            "rule_id": "AUTH-FAIL-BURST",
            "name": "Authentication failure burst",
            "log_sources": "Identity provider, authentication gateway, application login audit",
            "signal": (
                "Repeated failed sign-ins target one account or originate from one "
                + "device/source."
            ),
            "alert_when": (
                "Failures exceed the per-account or per-source baseline within a "
                + "rolling window."
            ),
            "severity": "high",
            "triage": (
                "Check account lock state, MFA result, device context, and user "
                + "confirmation through approved channels."
            ),
        },
        {
            "rule_id": "AUTH-MFA-ABUSE",
            "name": "Repeated MFA denials or timeouts",
            "log_sources": "Identity provider MFA audit, push notification provider events",
            "signal": (
                "Multiple denied, expired, or timed-out MFA challenges occur for one "
                + "account."
            ),
            "alert_when": (
                "Challenge denials/timeouts cross the identity team's configured "
                + "threshold."
            ),
            "severity": "high",
            "triage": (
                "Contact the account owner using a trusted channel and review recent "
                + "session activity."
            ),
        },
        {
            "rule_id": "AUTH-SESSION-STALE",
            "name": "Session remains valid after privilege change",
            "log_sources": "User-management audit, session store, authorization decision logs",
            "signal": (
                "A protected request is accepted using a session created before role "
                + "reduction or account disablement."
            ),
            "alert_when": (
                "A request succeeds after a session-revocation event for the same "
                + "account."
            ),
            "severity": "critical",
            "triage": (
                "Invalidate all account sessions, verify role propagation, and inspect "
                + "the affected protected actions."
            ),
        },
    ],
}

_INTENSITY_CHECKS = {"passive": 3, "low": 5, "medium": 7}


def build_simulation_report(
    *,
    simulation_id: str,
    scope: dict[str, Any],
    profile: str,
    intensity: str,
    duration_minutes: int,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    """Build a tabletop report; never performs network or host activity."""
    if profile not in PROFILE_CATALOG:
        raise ValueError("Profil de simulation tsy fantatra.")
    if intensity not in _INTENSITY_CHECKS:
        raise ValueError("Niveau simulation tsy fantatra.")
    profile_info = PROFILE_CATALOG[profile]
    checks = profile_info["checks"][: _INTENSITY_CHECKS[intensity]]
    timestamp = created_at or datetime.now(UTC)
    return {
        "id": simulation_id,
        "status": "simulation_only",
        "created_at": timestamp.isoformat(),
        "scope": {
            "id": scope["id"],
            "name": scope["name"],
            "target": scope["target"],
            "target_type": scope["target_type"],
            "authorization_expires_at": scope["authorization_expires_at"],
        },
        "profile": profile,
        "profile_label": profile_info["label"],
        "profile_description": profile_info["description"],
        "intensity": intensity,
        "review_window_minutes": duration_minutes,
        "execution": {
            "mode": "local_deterministic_tabletop",
            "network_requests": 0,
            "hosts_contacted": 0,
            "exploits_executed": 0,
            "payloads_executed": 0,
            "malware_executed": False,
            "automatic_changes": 0,
        },
        "summary": {
            "checks_prepared": len(checks),
            "verified_findings": 0,
            "manual_validation_required": len(checks),
            "notice": (
                "Scénario simulé ihany ity; tsy manamarina vulnerability tena misy na "
                + "scan an'ilay target."
            ),
        },
        "checks": [
            {
                **item,
                "status": "requires_manual_validation",
                "evidence": None,
            }
            for item in checks
        ],
        "attack_mapping": [
            {
                **item,
                "usage": "Threat-reference mapping only; no technique was executed.",
            }
            for item in profile_info["attack_mapping"]
        ],
        "detection_recommendations": [
            {
                **item,
                "type": "SOC detection design; not a deployed or enabled detection rule.",
                "status": "draft_only",
                "enabled": False,
            }
            for item in DETECTION_CATALOG[profile]
        ],
        "next_steps": [
            "Hamarino an-tanana ny checklist ao amin'ny rafitra nahazoana alalana.",
            "Tehirizo ao amin'ny ticket na evidence repository ny porofo tsy misy secrets.",
            "Avereno ny simulation rehefa vita ny remediation.",
        ],
        "limitations": [
            (
                "Tsy misy network request, port scan, exploit, payload, malware, "
                "credential test, persistence, na evasion."
            ),
            "Tsy vokatra pentest na vulnerability scan ity tatitra ity.",
            (
                "Ny ATT&CK IDs dia fanondroana threat-model fotsiny fa tsy porofo fa nitranga "
                "ilay technique."
            ),
        ],
    }
