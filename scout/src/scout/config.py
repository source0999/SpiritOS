from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScoutSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCOUT_",
        env_file=".env",
        extra="ignore",
    )

    database_path: Path = Field(default=Path("/app/data/scout.db"))
    data_dir: Path = Field(default=Path("/app/data"))
    config_path: Path = Field(default=Path("/app/config/sources.yaml"))
    api_port: int = 8077
    github_token: str | None = None
    github_ratelimit_floor: int = 200
    fetch_timeout_seconds: int = 15
    fetch_max_bytes: int = 2_000_000
    debug_poll_enabled: bool = False
    litellm_model: str = "ollama/llama3"
    litellm_timeout_seconds: int = 30
    litellm_require_authed: bool = True
    synthesis_batch_size: int = 3
    vector_packet_cap: int = 200_000
    debugger_llm_model: str | None = None
    debugger_batch_size: int = 25
    search_enabled: bool = False
    search_provider: str = "searxng"
    searxng_url: str | None = None
    search_max_results: int = 10
    search_timeout_seconds: int = 10
    search_user_agent: str = "ScoutSearch/0.3"
    discovery_jobs_enabled: bool = True
    discovery_jobs_per_day: int = 10
    discovery_candidates_per_job: int = 25
    promotion_signing_key: str | None = None
    promotion_proxy_intake_url: str = "http://localhost:8077/v1/scout-intake/promotion"


def get_settings() -> ScoutSettings:
    return ScoutSettings()
