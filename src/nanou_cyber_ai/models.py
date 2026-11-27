import ipaddress
import math
import re
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
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


class AuthAccountIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=6, max_length=320)
    display_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=12, max_length=128)

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


class AuthBootstrapIn(AuthAccountIn):
    bootstrap_token: str = Field(min_length=32, max_length=256)


class AuthRegisterIn(AuthAccountIn):
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


class AdminPairingExchangeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pairing_code: str = Field(
        min_length=40,
        max_length=160,
        pattern=r"^ncd_pair_[A-Za-z0-9_-]+$",
    )


class AuthPasswordChangeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)

    @model_validator(mode="after")
    def require_new_password(self) -> "AuthPasswordChangeIn":
        if self.current_password == self.new_password:
            raise ValueError("The new password must differ from the current password.")
        return self


class AdminUserUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["admin", "analyst", "viewer"]
    is_active: bool


class AssistantChatTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1200)


class AssistantChatIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=1000)
    history: list[AssistantChatTurn] = Field(default_factory=list, max_length=8)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Chat message cannot be empty.")
        return normalized


class AttackScopeCreateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=80)
    target: str = Field(min_length=1, max_length=253)
    authorization_basis: Literal["owned_asset", "written_permission", "isolated_lab"]
    authorization_expires_on: date
    authorization_confirmed: bool

    @field_validator("name")
    @classmethod
    def normalize_scope_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 3:
            raise ValueError("Anaran'ny scope fohy loatra.")
        return normalized

    @field_validator("target")
    @classmethod
    def normalize_scope_target(cls, value: str) -> str:
        normalized = value.strip().rstrip(".")
        if not normalized or any(char in normalized for char in "/\\?#@%") or "://" in normalized:
            raise ValueError("Target dia host/domain/IP tokana ihany; tsy URL na CIDR.")
        try:
            address = ipaddress.ip_address(normalized)
        except ValueError:
            address = None
        if address is not None:
            return str(address)
        try:
            host = normalized.encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise ValueError("Domain tsy manaraka IDNA.") from exc
        if len(host) > 253:
            raise ValueError("Domain lava loatra.")
        labels = host.split(".")
        if all(label.isdigit() for label in labels):
            raise ValueError("Adiresy IPv4 tsy marina.")
        if host != "localhost" and len(labels) < 2:
            raise ValueError("FQDN na localhost ihany no ekena.")
        if any(
            not label
            or len(label) > 63
            or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
            for label in labels
        ):
            raise ValueError("Host/domain tsy manaraka ny endrika DNS.")
        return host

    @model_validator(mode="after")
    def validate_authorization(self) -> "AttackScopeCreateIn":
        today = datetime.now(UTC).date()
        if not self.authorization_confirmed:
            raise ValueError("Tsy maintsy manamarina fa manana alalana amin'ny target ianao.")
        if self.authorization_expires_on <= today:
            raise ValueError("Lany daty na androany ny fahazoan-dalana.")
        if self.authorization_expires_on > today + timedelta(days=365):
            raise ValueError("Fahazoan-dalana 365 andro fara-fahabetsany.")
        return self


class AttackSimulationCreateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scope_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    profile: Literal["reconnaissance", "web_security", "api_security", "authentication"]
    intensity: Literal["passive", "low", "medium"]
    duration_minutes: int = Field(default=10, ge=1, le=30)
    authorization_confirmed: bool

    @model_validator(mode="after")
    def require_current_authorization(self) -> "AttackSimulationCreateIn":
        if not self.authorization_confirmed:
            raise ValueError(
                "Tsy maintsy manamarina indray ny fahazoan-dalana alohan'ny simulation."
            )
        return self


class DeveloperApiKeyCreateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3, max_length=80)
    scopes: list[Literal["intel:read", "malware:metadata:read", "ai:chat"]] = Field(
        min_length=1,
        max_length=3,
    )
    expires_in_days: int = Field(default=30, ge=1, le=90)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("API key name must contain at least three characters.")
        return normalized

    @field_validator("scopes")
    @classmethod
    def unique_scopes(
        cls,
        value: list[Literal["intel:read", "malware:metadata:read", "ai:chat"]],
    ) -> list[Literal["intel:read", "malware:metadata:read", "ai:chat"]]:
        if len(set(value)) != len(value):
            raise ValueError("Duplicate API key scopes are not allowed.")
        return value

    @model_validator(mode="after")
    def validate_assistant_scope(self) -> "DeveloperApiKeyCreateIn":
        if "ai:chat" in self.scopes and not {
            "intel:read",
            "malware:metadata:read",
        }.intersection(self.scopes):
            raise ValueError("The ai:chat scope requires at least one read scope.")
        return self


class MalwareFeatureDatasetId(StrEnum):
    EMBER = "ember2024-apk"
    LAMDA = "lamda-apk-2022-train-2023-test"
