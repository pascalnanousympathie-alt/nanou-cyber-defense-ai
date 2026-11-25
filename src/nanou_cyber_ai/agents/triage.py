from nanou_cyber_ai.models import TriageResult


def prioritize_cve(cve_id: str, kev_ids: set[str], cvss_score: float | None = None) -> TriageResult:
    normalized = cve_id.upper()
    in_kev = normalized in {item.upper() for item in kev_ids}
    rationale: list[str] = []
    if in_kev:
        rationale.append("Listed in the CISA Known Exploited Vulnerabilities catalog.")
    if cvss_score is not None:
        if not 0 <= cvss_score <= 10:
            raise ValueError("CVSS score must be between 0 and 10")
        rationale.append(f"CVSS base score: {cvss_score:.1f}.")
    if in_kev:
        priority = "critical"
    elif cvss_score is None:
        priority = "unknown"
    elif cvss_score >= 9:
        priority = "critical"
    elif cvss_score >= 7:
        priority = "high"
    elif cvss_score >= 4:
        priority = "moderate"
    else:
        priority = "low"
    if not rationale:
        rationale.append("No KEV match or CVSS score was supplied.")
    return TriageResult(
        cve_id=normalized,
        priority=priority,
        in_kev=in_kev,
        cvss_score=cvss_score,
        rationale=rationale,
    )
