import pytest
from pydantic import ValidationError

from nanou_cyber_ai.agents.triage import prioritize_cve
from nanou_cyber_ai.mcp.registry import ToolNotAllowed, authorize_tool
from nanou_cyber_ai.models import MalwareMetadataIn


def test_kev_match_is_critical() -> None:
    result = prioritize_cve("CVE-2024-1234", {"cve-2024-1234"}, 5.0)
    assert result.priority == "critical"
    assert result.in_kev is True


def test_cvss_prioritization() -> None:
    assert prioritize_cve("CVE-2024-1234", set(), 8.1).priority == "high"
    assert prioritize_cve("CVE-2024-1234", set(), 2.0).priority == "low"


def test_cvss_out_of_range_rejected() -> None:
    with pytest.raises(ValueError):
        prioritize_cve("CVE-2024-1234", set(), 11.0)


def test_mcp_allowlist_requires_scope() -> None:
    tool = authorize_tool("nvd.cve.get", {"intel:read"})
    assert tool.access == "read"
    with pytest.raises(ToolNotAllowed):
        authorize_tool("nvd.cve.get", set())


def test_unknown_mcp_tool_fails_closed() -> None:
    with pytest.raises(ToolNotAllowed):
        authorize_tool("shell.exec", {"*"})


def test_metadata_accepts_sha256_and_numeric_features() -> None:
    record = MalwareMetadataIn(
        sha256="a" * 64, label="malicious", source="EMBER feature dataset",
        features={"section_entropy_mean": 4.5, "imports_count": 21},
    )
    assert record.label == "malicious"
    assert "file_bytes" not in record.model_dump()


def test_metadata_rejects_invalid_hash_and_extra_binary_fields() -> None:
    with pytest.raises(ValidationError):
        MalwareMetadataIn(sha256="not-a-hash", label="unknown", source="test")
    with pytest.raises(ValidationError):
        MalwareMetadataIn(sha256="a" * 64, label="unknown", source="test",
                          file_bytes="MZ...")
