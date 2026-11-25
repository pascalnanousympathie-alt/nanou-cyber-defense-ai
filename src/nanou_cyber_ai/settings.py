from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NANOU_", extra="ignore")

    data_dir: Path = Field(default=Path("~/.local/share/nanou-cyber-defense-ai").expanduser())
    http_timeout_seconds: float = Field(default=15.0, gt=0, le=60)
    metadata_api_token: SecretStr | None = None


settings = Settings()
