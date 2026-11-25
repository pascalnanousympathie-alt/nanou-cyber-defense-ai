from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NANOU_", extra="ignore")

    data_dir: Path = Field(default=Path("~/.local/share/nanou-cyber-defense-ai").expanduser())
    http_timeout_seconds: float = Field(default=15.0, gt=0, le=60)
    database_url: SecretStr | None = None
    bootstrap_token: SecretStr | None = None
    session_cookie_name: str = Field(default="nanou_session", min_length=8, max_length=40)
    session_ttl_hours: int = Field(default=12, ge=1, le=168)
    auth_attempts_per_window: int = Field(default=10, ge=3, le=50)
    auth_rate_window_seconds: int = Field(default=900, ge=60, le=3600)
    api_key_requests_per_minute: int = Field(default=60, ge=10, le=600)
    assistant_requests_per_minute: int = Field(default=30, ge=5, le=120)
    simulation_requests_per_hour: int = Field(default=10, ge=1, le=60)
    simulation_allowed_targets: str = Field(default="local-lab", max_length=1000)
    ai_api_key: SecretStr | None = None
    ai_model: str = Field(default="gpt-6.2-astra", min_length=1, max_length=80)
    malware_model_path: Path | None = None
    malware_model_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    malware_model_dataset_id: str | None = Field(default=None, max_length=80)
    malware_model_threshold: float = Field(default=0.5, ge=0, le=1)


settings = Settings()
