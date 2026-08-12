"""일반 외부 REST 응답에서 텍스트 문서를 추출하는 클라이언트입니다.

``app.api.nifi``가 NiFi에서 받은 JSON 배열을 ``SourceDocument``로 변환할 때 사용하며,
향후 다른 수신 라우터도 이 모듈의 문서 형식을 재사용합니다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


class SourceTextError(ValueError):
    """Raised when an upstream response cannot provide usable text."""


@dataclass(frozen=True)
class SourceDocument:
    """One textual document extracted from an upstream response."""

    content: str
    metadata: dict[str, Any]


class SourceTextClient:
    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._timeout = timeout_seconds

    def fetch_documents(self, source_url: str, json_text_pointer: str) -> list[SourceDocument]:
        try:
            with httpx.Client(timeout=self._timeout, follow_redirects=True) as client:
                response = client.get(source_url)
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise SourceTextError(f"Unable to fetch source text: {error}") from error

        if "application/json" not in response.headers.get("content-type", "").lower():
            return [SourceDocument(content=self._require_text(response.text), metadata={})]

        try:
            return self.to_documents(self._resolve_pointer(response.json(), json_text_pointer))
        except (ValueError, TypeError) as error:
            raise SourceTextError(f"Unable to extract source text from JSON: {error}") from error

    @staticmethod
    def _resolve_pointer(payload: Any, pointer: str) -> Any:
        if pointer == "":
            return payload
        if not pointer.startswith("/"):
            raise ValueError("JSON text pointer must start with '/'")

        current = payload
        for raw_token in pointer[1:].split("/"):
            token = raw_token.replace("~1", "/").replace("~0", "~")
            if isinstance(current, dict):
                current = current[token]
            elif isinstance(current, list):
                current = current[int(token)]
            else:
                raise TypeError(f"Pointer cannot continue through a {type(current).__name__}")
        return current

    @staticmethod
    def _require_text(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Upstream content must be a non-empty text value")
        return value

    @classmethod
    def to_documents(cls, value: Any) -> list[SourceDocument]:
        """텍스트 또는 JSON 배열을 공통 ``SourceDocument`` 목록으로 변환합니다.

        HTTP 응답 처리뿐 아니라 NiFi 웹훅이 이미 파싱한 ``records`` 배열을 받을 때도
        사용합니다.
        """
        if isinstance(value, str):
            return [SourceDocument(content=cls._require_text(value), metadata={})]
        if not isinstance(value, list) or not value:
            raise ValueError("JSON text pointer must resolve to text or a non-empty array")

        documents: list[SourceDocument] = []
        for index, item in enumerate(value):
            if isinstance(item, str):
                try:
                    content = cls._require_text(item)
                except ValueError as error:
                    raise ValueError(f"records[{index}] must be non-empty text") from error
                documents.append(SourceDocument(content=content, metadata={"sourceItemIndex": index}))
            elif isinstance(item, dict):
                if not item:
                    raise ValueError(f"records[{index}] is an empty object")
                try:
                    content = cls._mapping_to_text(item)
                except ValueError as error:
                    raise ValueError(
                        f"records[{index}] contains only null or blank values"
                    ) from error
                documents.append(
                    SourceDocument(
                        content=content,
                        metadata={"sourceItemIndex": index, **cls._scalar_metadata(item)},
                    )
                )
            else:
                raise TypeError(f"records[{index}] must be text or an object")
        return documents

    @staticmethod
    def _mapping_to_text(item: dict[str, Any]) -> str:
        lines = []
        for key, value in item.items():
            if value is None or value == "":
                continue
            rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
            lines.append(f"{key}: {rendered}")
        if not lines:
            raise ValueError("JSON object did not contain usable values")
        return "\n".join(lines)

    @staticmethod
    def _scalar_metadata(item: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in item.items()
            if value is None or isinstance(value, (str, int, float, bool))
        }
