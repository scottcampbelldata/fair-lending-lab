"""Centralized env-driven config. No module-time DB or HTTP."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env", override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(REPO_ROOT / ".env"), extra="ignore")

    pghost: str = Field(default="localhost", alias="PGHOST")
    pgport: int = Field(default=5432, alias="PGPORT")
    pgdatabase: str = Field(default="fair_lending_lab", alias="PGDATABASE")
    pguser: str = Field(default="flab_app", alias="PGUSER")
    pgpassword: str = Field(default="", alias="PGPASSWORD")

    api_host: str = Field(default="127.0.0.1", alias="FLAB_API_HOST")
    api_port: int = Field(default=8702, alias="FLAB_API_PORT")
    data_dir: Path = Field(default=REPO_ROOT / "data", alias="FLAB_DATA_DIR")
    random_seed: int = Field(default=20260625, alias="FLAB_RANDOM_SEED")
    log_level: str = Field(default="INFO", alias="FLAB_LOG_LEVEL")
    hmda_year: int = Field(default=2023, alias="FLAB_HMDA_YEAR")
    hmda_state: str = Field(default="MA", alias="FLAB_HMDA_STATE")
    cors_origins: str = Field(
        default="http://localhost:3000",
        alias="FLAB_CORS_ORIGINS",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.pguser}:{self.pgpassword}"
            f"@{self.pghost}:{self.pgport}/{self.pgdatabase}"
        )

    @property
    def psycopg_dsn(self) -> str:
        return (
            f"host={self.pghost} port={self.pgport} dbname={self.pgdatabase} "
            f"user={self.pguser} password={self.pgpassword}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def get_data_dir() -> Path:
    p = get_settings().data_dir
    p.mkdir(parents=True, exist_ok=True)
    (p / "raw").mkdir(parents=True, exist_ok=True)
    (p / "processed").mkdir(parents=True, exist_ok=True)
    return p


def get_random_seed() -> int:
    return get_settings().random_seed


if "FLAB_FORCE_SEED" in os.environ:
    _forced = int(os.environ["FLAB_FORCE_SEED"])

    def get_random_seed() -> int:  # type: ignore[no-redef]
        return _forced
