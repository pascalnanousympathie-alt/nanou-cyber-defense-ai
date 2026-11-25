from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class MalwareMetadataIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    label: Literal["malicious", "benign", "unknown"]
    source: str = Field(min_length=2, max_length=200)
    family: str | None = Field(default=None, max_length=120)
    tags: list[str] = Field(default_factory=list, max_length=30)
    observed_at: datetime | None = None
    report_url: HttpUrl | None = None
    # Only pre-extracted numeric features are accepted. No file or payload field exists.
    features: dict[str, float] = Field(default_factory=dict, max_length=4096)

    @field_validator("features")
    @classmethod
    def finite_features(cls, value: dict[str, float]) -> dict[str, float]:
        import math

        if any(not math.isfinite(number) for number in value.values()):
            raise ValueError("feature values must be finite numbers")
        return value


class MalwareMetadata(MalwareMetadataIn):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TriageResult(BaseModel):
    cve_id: str
    priority: Literal["critical", "high", "moderate", "low", "unknown"]
    in_kev: bool
    cvss_score: float | None = None
    rationale: list[str]
