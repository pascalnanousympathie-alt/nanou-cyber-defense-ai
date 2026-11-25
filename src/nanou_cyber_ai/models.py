import math
import re
from datetime import UTC, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


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
        if any(not math.isfinite(number) for number in value.values()):
            raise ValueError("feature values must be finite numbers")
        return value


class MalwareMetadata(MalwareMetadataIn):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TriageResult(BaseModel):
    cve_id: str
    priority: Literal["critical", "high", "moderate", "low", "unknown"]
    in_kev: bool
    cvss_score: float | None = None
    rationale: list[str]


class MalwareInferenceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: Literal["ember2024-apk", "lamda-apk-2022-train-2023-test"]
    schema_version: Literal[1] = 1
    features: list[float] = Field(min_length=1, max_length=4561)

    @field_validator("features", mode="before")
    @classmethod
    def finite_numeric_features(cls, value: object) -> list[float]:
        if not isinstance(value, list):
            raise ValueError("features must be a JSON array of numbers")
        normalized: list[float] = []
        for number in value:
            if isinstance(number, bool) or not isinstance(number, (int, float)):
                raise ValueError("features must contain only numeric values")
            parsed = float(number)
            if not math.isfinite(parsed) or abs(parsed) > 1_000_000_000:
                raise ValueError("feature values must be finite and within the supported range")
            normalized.append(parsed)
        return normalized

    @model_validator(mode="after")
    def validate_dataset_schema(self) -> "MalwareInferenceIn":
        expected_count = 2568 if self.dataset_id == "ember2024-apk" else 4561
        if len(self.features) != expected_count:
            raise ValueError(
                f"{self.dataset_id} requires exactly {expected_count} numeric features"
            )
        if self.dataset_id == "lamda-apk-2022-train-2023-test" and any(
            not value.is_integer() or not -128 <= value <= 127 for value in self.features
        ):
            raise ValueError("LAMDA features must preserve the original signed int8 values")
        return self


class MalwareInferenceResult(BaseModel):
    dataset_id: Literal["ember2024-apk", "lamda-apk-2022-train-2023-test"]
    schema_version: Literal[1]
    feature_count: int
    classification: Literal["benign", "malicious"]
    malicious_probability: float = Field(ge=0, le=1)
    decision_threshold: float = Field(ge=0, le=1)
    model_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    limitation: str



class AuthBootstrapIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=6, max_length=320)
    display_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=12, max_length=128)
    bootstrap_token: str = Field(min_length=32, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("A valid email address is required.")
        return normalized

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 2:
            raise ValueError("Display name is too short.")
        return normalized


class AuthRegisterIn(AuthBootstrapIn):
    pass


class AuthLoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=6, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("A valid email address is required.")
        return normalized


class AdminUserUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["admin", "analyst", "viewer"]
    is_active: bool


class MalwareFeatureDatasetId(str, Enum):
    EMBER = "ember2024-apk"
    LAMDA = "lamda-apk-2022-train-2023-test"
