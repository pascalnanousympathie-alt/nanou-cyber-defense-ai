"""Offline-only, authorized attack-simulation scenarios.

This module emits synthetic telemetry for blue-team detection exercises. It
never opens sockets, sends HTTP requests, invokes a shell, or touches a target.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from typing import Any

from nanou_cyber_ai.models import AttackSimulationIn

_TARGET_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
_INTENSITY_EVENT_COUNTS = {"passive": 1, "low": 2, "medium": 3}

_PROFILE_CATALOG: dict[str, dict[str, Any]] = {
    "reconnaissance": {
        "label": "Reconnaissance signals",
        "description": "Synthetic asset-discovery and scanning telemetry for detection tuning.",
        "scenarios": [
            {
                "technique_id": "T1595.002",
                "technique": "Active Scanning: Vulnerability Scanning",
                "severity": "low",
                "signal": (
                    "SIMULATED: repeated discovery requests across a small "
                    "asset inventory"
                ),
                "detection": (
                    "Correlate repeated discovery indicators across one source "
                    "and a short time window."
                ),
                "recommendation": (
                    "Validate asset inventory coverage and alert thresholds; "
                    "confirm that authorized scanners are allowlisted."
                ),
            },
            {
                "technique_id": "T1046",
                "technique": "Network Service Discovery",
                "severity": "low",
                "signal": (
                    "SIMULATED: an unusual service-discovery event was placed "
                    "in the training stream"
                ),
                "detection": (
                    "Alert on service-discovery activity that falls outside "
                    "the approved maintenance window."
                ),
                "recommendation": (
                    "Document approved discovery jobs and review unexpected "
                    "source identities."
                ),
            },
            {
                "technique_id": "T1595.001",
                "technique": "Active Scanning: Scanning IP Blocks",
                "severity": "info",
                "signal": "SIMULATED: broad asset-enumeration pattern in synthetic telemetry",
                "detection": "Baseline normal inventory activity and flag material deviations.",
                "recommendation": (
                    "Keep the network asset inventory current and verify "
                    "monitoring coverage."
                ),
            },
        ],
    },
    "web_security": {
        "label": "Web security signals",
        "description": (
            "Synthetic web-application security alerts; no request is sent "
            "to a website."
        ),
        "scenarios": [
            {
                "technique_id": "T1190",
                "technique": "Exploit Public-Facing Application",
                "severity": "medium",
                "signal": (
                    "SIMULATED: web application request matched a generic "
                    "exploit-attempt detection pattern"
                ),
                "detection": (
                    "Correlate WAF rule identifiers, request anomaly score, "
                    "and application error spikes."
                ),
                "recommendation": "Review the affected route, patch status, WAF coverage, and application logs.",
            },
            {
                "technique_id": "T1595.002",
                "technique": "Active Scanning: Vulnerability Scanning",
                "severity": "low",
                "signal": (
                    "SIMULATED: unusual web route enumeration pattern"
                ),
                "detection": (
                    "Flag high-volume route discovery that is inconsistent "
                    "with normal client behavior."
                ),
                "recommendation": (
                    "Check rate limits, route exposure, and whether the "
                    "source belongs to an approved test."
                ),
            },
            {
                "technique_id": "T1190",
                "technique": "Exploit Public-Facing Application",
                "severity": "info",
                "signal": (
                    "SIMULATED: application-layer defensive control generated "
                    "a test alert"
                ),
                "detection": (
                    "Verify that application and edge security alerts share "
                    "a trace or correlation ID."
                ),
                "recommendation": (
                    "Preserve request metadata safely and test the incident "
                    "escalation workflow."
                ),
            },
        ],
    },
    "api_security": {
        "label": "API security signals",
        "description": "Synthetic API authorization, schema-validation, and rate-limit alerts.",
        "scenarios": [
            {
                "technique_id": "T1078",
                "technique": "Valid Accounts",
                "severity": "medium",
                "signal": (
                    "SIMULATED: an API identity attempted an operation "
                    "outside its assigned scope"
                ),
                "detection": (
                    "Alert on repeated authorization denials grouped by "
                    "principal, route, and time window."
                ),
                "recommendation": (
                    "Review least-privilege scopes, token ownership, and API "
                    "authorization tests."
                ),
            },
            {
                "technique_id": "T1190",
                "technique": "Exploit Public-Facing Application",
                "severity": "low",
                "signal": "SIMULATED: malformed API input was rejected by request validation",
                "detection": (
                    "Track validation failures without logging request "
                    "bodies, credentials, or tokens."
                ),
                "recommendation": (
                    "Keep strict schemas, reject unknown fields, and cap "
                    "request size."
                ),
            },
            {
                "technique_id": "T1499",
                "technique": "Endpoint Denial of Service",
                "severity": "info",
                "signal": "SIMULATED: API rate-limit threshold was reached in training telemetry",
                "detection": "Correlate throttling responses with per-principal request counts.",
                "recommendation": (
                    "Check rate-limit coverage and ensure throttling does not "
                    "expose sensitive data."
                ),
            },
        ],
    },
    "authentication": {
        "label": "Authentication signals",
        "description": (
            "Synthetic identity-security alerts; no login attempts or "
            "credential checks occur."
        ),
        "scenarios": [
            {
                "technique_id": "T1110.003",
                "technique": "Brute Force: Password Spraying",
                "severity": "medium",
                "signal": (
                    "SIMULATED: distributed authentication failures were "
                    "inserted into the training stream"
                ),
                "detection": (
                    "Correlate failure ratios, distinct accounts, and source "
                    "reputation without retaining passwords."
                ),
                "recommendation": (
                    "Review MFA coverage, password policy, and identity-provider "
                    "alert routing."
                ),
            },
            {
                "technique_id": "T1078",
                "technique": "Valid Accounts",
                "severity": "low",
                "signal": "SIMULATED: a sign-in succeeded from an unusual context",
                "detection": "Evaluate risk-based sign-in alerts and session anomaly signals.",
                "recommendation": (
                    "Review session lifetime, device trust, MFA, and account "
                    "recovery controls."
                ),
            },
            {
                "technique_id": "T1110",
                "technique": "Brute Force",
                "severity": "info",
                "signal": "SIMULATED: identity rate-limit control emitted a training alert",
                "detection": (
                    "Confirm that authentication throttling and lockout "
                    "telemetry reaches the SOC."
                ),
                "recommendation": (
                    "Use progressive throttling and safe account recovery; "
                    "avoid permanent lockout patterns."
                ),
            },
        ],
    },
}


def allowed_target_ids(configured: str) -> list[str]:
    """Return only configured opaque lab identifiers; never accept hostnames or URLs."""
    targets: set[str] = set()
    for candidate in configured.split(","):
        target_id = candidate.strip().lower()
        if target_id and _TARGET_ID_RE.fullmatch(target_id):
            targets.add(target_id)
    return sorted(targets)


def simulation_configuration(
    configured_targets: str,
    *,
    max_runs_per_hour: int = 10,
) -> dict[str, Any]:
    return {
        "mode": "offline_synthetic_only",
        "targets": [{"id": target_id, "label": target_id.replace("-", " ").title()}
                    for target_id in allowed_target_ids(configured_targets)],
        "profiles": [
            {"id": profile_id, "label": profile["label"], "description": profile["description"]}
            for profile_id, profile in _PROFILE_CATALOG.items()
        ],
        "intensities": [
            {"id": "passive", "label": "Passive · 1 signal"},
            {"id": "low", "label": "Low · 2 signals"},
            {"id": "medium", "label": "Medium · 3 signals"},
        ],
        "controls": {
            "authorization_required": True,
            "role_required": ["admin", "analyst"],
            "network_activity": False,
            "shell_execution": False,
            "exploit_execution": False,
            "credential_access": False,
            "malware_execution": False,
            "max_runs_per_hour": max_runs_per_hour,
        },
    }


def run_offline_simulation(
    item: AttackSimulationIn,
    *,
    configured_targets: str,
) -> dict[str, Any]:
    """Generate a local synthetic detection exercise after an explicit authorization gate."""
    if not item.authorization_acknowledged:
        raise PermissionError("Tsy voamarina ny fahazoan-dalana hanao simulation.")
    if item.target_id not in allowed_target_ids(configured_targets):
        raise PermissionError("Tsy ao amin'ny allowlist an'ny laboratoire io target ID io.")
    if item.profile not in _PROFILE_CATALOG:
        raise ValueError("Profil de simulation tsy fantatra.")
    if item.intensity not in _INTENSITY_EVENT_COUNTS:
        raise ValueError("Intensity tsy ekena.")

    profile = _PROFILE_CATALOG[item.profile]
    count = _INTENSITY_EVENT_COUNTS[item.intensity]
    created_at = datetime.now(UTC).isoformat()
    events = [
        {
            "event_id": uuid.uuid4().hex,
            "sequence": index + 1,
            "timestamp": created_at,
            "source": "NANOU_SYNTHETIC_TELEMETRY",
            "technique_id": scenario["technique_id"],
            "technique": scenario["technique"],
            "severity": scenario["severity"],
            "signal": scenario["signal"],
            "detection_logic": scenario["detection"],
            "recommended_action": scenario["recommendation"],
            "is_synthetic": True,
        }
        for index, scenario in enumerate(profile["scenarios"][:count])
    ]
    return {
        "simulation_id": uuid.uuid4().hex,
        "status": "SIMULATED",
        "mode": "offline_synthetic_only",
        "created_at": created_at,
        "target_id": item.target_id,
        "profile": item.profile,
        "profile_label": profile["label"],
        "intensity": item.intensity,
        "authorization_reference": item.authorization_reference,
        "network_activity": False,
        "target_contacted": False,
        "commands_executed": False,
        "credentials_accessed": False,
        "malware_executed": False,
        "events_generated": len(events),
        "events": events,
        "limitations": [
            "Synthetic telemetry only; no real target was contacted.",
            "No port scan, HTTP request, login attempt, exploit, shell, or payload was executed.",
            "The output validates analyst workflow and detection coverage, not target security.",
        ],
    }
