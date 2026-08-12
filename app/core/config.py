"""환경 변수 기반 런타임 설정 모듈입니다.

``.env``의 DB·Ollama·NiFi 수신 인증 값을 읽어 ``app.db.session``,
``app.api.nifi`` 및 ``app.ingestion.service``에 제공합니다.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/rag"
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "bge-m3"
    embedding_dimensions: int = 1024
    nifi_ingest_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
