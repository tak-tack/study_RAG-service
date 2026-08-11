from functools import lru_cache
from urllib.parse import parse_qs, urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/rag"
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "bge-m3"
    embedding_dimensions: int = 1024
    source_api_url: str | None = None
    source_api_text_pointer: str = "/content"
    finlife_api_base_url: str = "https://finlife.fss.or.kr/finlifeapi/companySearch.json"
    finlife_api_key: str | None = None
    finlife_top_fin_grp_nos: str | None = None
    finlife_page_nos: str = "1"

    def finlife_request_settings(self) -> tuple[str, str]:
        """Return the endpoint and API key for the scheduled Finlife job.

        The legacy SOURCE_API_URL remains a temporary fallback so existing local settings
        keep working until the API key is moved to FINLIFE_API_KEY.
        """
        if self.finlife_api_key and self.finlife_top_fin_grp_nos:
            return self.finlife_api_base_url, self.finlife_api_key
        if not self.source_api_url:
            raise ValueError("FINLIFE_API_KEY and FINLIFE_TOP_FIN_GRP_NOS must be configured")

        parsed = urlparse(self.source_api_url)
        query = parse_qs(parsed.query)
        api_key = query.get("auth", [None])[0]
        if not api_key:
            raise ValueError("Finlife API key or topFinGrpNo is missing")
        return urlunparse(parsed._replace(query="")), api_key

    def finlife_group_numbers(self) -> list[str]:
        """Return unique Finlife topFinGrpNo values in configured order."""
        raw_groups = self.finlife_top_fin_grp_nos
        if raw_groups:
            groups = [value.strip() for value in raw_groups.split(",") if value.strip()]
        elif self.source_api_url:
            groups = parse_qs(urlparse(self.source_api_url).query).get("topFinGrpNo", [])
        else:
            groups = []
        if not groups:
            raise ValueError("FINLIFE_TOP_FIN_GRP_NOS must contain at least one group number")
        return list(dict.fromkeys(groups))

    def finlife_page_numbers(self) -> list[int]:
        """Parse the configured, comma-separated Finlife page numbers."""
        try:
            pages = [int(value.strip()) for value in self.finlife_page_nos.split(",") if value.strip()]
        except ValueError as error:
            raise ValueError("FINLIFE_PAGE_NOS must contain comma-separated positive integers") from error
        if not pages or any(page < 1 for page in pages):
            raise ValueError("FINLIFE_PAGE_NOS must contain at least one positive integer")
        return list(dict.fromkeys(pages))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
