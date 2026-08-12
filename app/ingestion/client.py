"""일반 외부 REST 응답에서 텍스트 문서를 추출하는 클라이언트입니다.

``app.ingestion.finlife``가 JSON 배열을 ``SourceDocument``로 변환할 때 재사용하며,
향후 다른 REST 기반 수집기도 이 모듈의 문서 형식을 사용합니다.
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
            return self._to_documents(self._resolve_pointer(response.json(), json_text_pointer))
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
    def _to_documents(cls, value: Any) -> list[SourceDocument]:
        if isinstance(value, str):
            return [SourceDocument(content=cls._require_text(value), metadata={})]
        if not isinstance(value, list) or not value:
            raise ValueError("JSON text pointer must resolve to text or a non-empty array")

        documents: list[SourceDocument] = []
        for index, item in enumerate(value):
            if isinstance(item, str):
                documents.append(
                    SourceDocument(content=cls._require_text(item), metadata={"sourceItemIndex": index})
                )
            elif isinstance(item, dict):
                documents.append(
                    SourceDocument(
                        content=cls._mapping_to_text(item),
                        metadata={"sourceItemIndex": index, **cls._scalar_metadata(item)},
                    )
                )
            else:
                raise TypeError(f"Array item {index} must be text or an object")
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
