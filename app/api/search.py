"""저장된 금융회사 벡터 청크를 조회하는 검색 API입니다."""

from __future__ import annotations

import logging
from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.retrieval.service import RetrievalService

router = APIRouter(prefix="/api", tags=["search"])
logger = logging.getLogger(__name__)


class SearchRequest(BaseModel):
    """A semantic-search query and optional financial-sector filter."""

    query: str = Field(min_length=1, max_length=1_000)
    top_k: int = Field(default=5, ge=1, le=20)
    top_fin_grp_no: str | None = Field(default=None, pattern=r"^\d{6}$")


class SearchHit(BaseModel):
    company_id: int
    company_name: str
    fin_co_no: str
    top_fin_grp_no: str
    dcls_month: str
    content: str
    chunk_index: int
    distance: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchHit]


def get_session() -> Generator[Session, None, None]:
    """Create one ORM session for a search request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.post("/search", response_model=SearchResponse)
def search_documents(
    request: SearchRequest, session: Session = Depends(get_session)
) -> SearchResponse:
    """Find stored chunks semantically similar to the supplied query."""
    try:
        results = RetrievalService(session).search(
            request.query,
            top_k=request.top_k,
            top_fin_grp_no=request.top_fin_grp_no,
        )
    except Exception as error:
        logger.exception("Vector search failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Query embedding or vector search failed",
        ) from error

    return SearchResponse(
        query=request.query,
        results=[SearchHit(**result.__dict__) for result in results],
    )
