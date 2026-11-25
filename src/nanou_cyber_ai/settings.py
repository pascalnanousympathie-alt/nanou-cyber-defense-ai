from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NANOU_", extra="ignore")

    data_dir: Path = Field(default=Path("~/.local/share/nanou-cyber-defense-ai").expanduser())
    http_timeout_seconds: float = Field(default=15.0, gt=0, le=60)
    metadata_api_token: SecretStr | None = None
    malware_model_path: Path | None = None
    malware_model_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    malware_model_dataset_id: str | None = Field(default=None, max_length=80)
    malware_model_threshold: float = Field(default=0.5, ge=0, le=1)


settings = Settings()
