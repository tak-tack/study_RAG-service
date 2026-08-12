"""수집 원문을 정규화하고 LangChain 청크로 나누는 순수 텍스트 처리 모듈입니다.

``app.ingestion.service``가 임베딩 직전에 호출하며, DB·네트워크 연결에는 의존하지
않아 단위 테스트하기 쉬운 계층입니다.
"""

from __future__ import annotations

import re
import unicodedata

from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean_text(text: str) -> str:
    """Normalize Unicode and whitespace while preserving paragraph boundaries."""
    normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[^\S\n]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 150) -> list[str]:
    """Split cleaned text into overlapping, retrieval-friendly LangChain chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)
