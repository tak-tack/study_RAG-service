"""금융감독원 Finlife ``companySearch`` API의 페이지 단위 클라이언트입니다.

``app.core.config``에서 인증·권역 설정을 받고, ``app.jobs.finlife_company_sync``에
정규화된 ``SourceDocument`` 목록을 전달합니다.
"""

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.ingestion.client import SourceDocument, SourceTextClient


@dataclass(frozen=True)
class FinlifePage:
    documents: list[SourceDocument]
    group_number: str
    page_number: int
    max_page_number: int


class FinlifeCompanyClient:
    """Typed client for Finlife's paginated company-search endpoint."""

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._timeout = timeout_seconds

    def fetch_page(self, group_number: str, page_number: int) -> FinlifePage:
        endpoint, api_key = settings.finlife_request_settings()
        params = {"auth": api_key, "topFinGrpNo": group_number, "pageNo": page_number}
        try:
            with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
                response = client.get(endpoint, params=params)
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise RuntimeError(f"Finlife company search failed: {error}") from error

        result = payload.get("result")
        if not isinstance(result, dict):
            raise TypeError("Finlife company search response did not contain result")
        if result.get("err_cd") not in (None, "000"):
            raise RuntimeError(f"Finlife API error: {result.get('err_msg', result.get('err_cd'))}")
        base_list = result.get("baseList")
        if not isinstance(base_list, list):
            raise TypeError("Finlife company search response did not contain baseList")
        documents = SourceTextClient._to_documents(base_list)
        max_page_number = int(result.get("max_page_no", page_number))
        return FinlifePage(documents, group_number, page_number, max_page_number)
