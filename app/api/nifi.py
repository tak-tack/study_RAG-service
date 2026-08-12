"""NiFi → FastAPI 금융회사 적재 웹훅입니다.

NiFi가 Open API 응답을 정규화한 뒤 이 라우터로 전송하면, ``app.ingestion.service``가
청킹·Ollama 임베딩·pgvector 저장을 수행합니다. 실행 결과는
``takhyeong_saving_log``에 ``nifi`` 유형으로 기록됩니다.
"""

from __future__ import annotations

import secrets
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.saving_log import SavingLog
from app.db.session import SessionLocal
from app.ingestion.client import SourceTextClient
from app.ingestion.service import IngestionService

router = APIRouter(prefix="/api/nifi", tags=["nifi"])


class FinlifeCompanyIngestionRequest(BaseModel):
    """NiFi 요청 Body의 금융회사 레코드 묶음입니다.

    권역·페이지·API 식별 정보는 NiFi JSON 재조립 오류를 피하기 위해 HTTP Header로
    받습니다.
    """

    records: list[dict[str, Any]] = Field(default_factory=list)


class NiFiIngestionResponse(BaseModel):
    """NiFi가 성공 여부와 적재 건수를 확인할 때 사용하는 응답입니다."""

    log_id: int | None
    status: str
    company_ids: list[int]
    companies_stored: int
    chunks_stored: int


def get_session() -> Generator[Session, None, None]:
    """요청 단위 ORM 세션을 만들고 요청 종료 시 항상 닫습니다."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def verify_nifi_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """설정된 경우에만 NiFi 전용 공유 키를 검증합니다."""
    if settings.nifi_ingest_api_key and not secrets.compare_digest(
        x_api_key or "", settings.nifi_ingest_api_key
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid X-API-Key")


@router.post(
    "/finlife/companies",
    response_model=NiFiIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_nifi_api_key)],
)
def ingest_finlife_companies(
    request: FinlifeCompanyIngestionRequest,
    top_fin_grp_no: Annotated[
        str, Header(alias="X-Top-Fin-Grp-No", pattern=r"^\d{6}$")
    ],
    page_no: Annotated[int, Header(alias="X-Page-No", ge=1)],
    api_name: Annotated[str, Header(alias="X-Api-Name", min_length=1, max_length=100)],
    session: Session = Depends(get_session),  # noqa: B008 - FastAPI dependency declaration
) -> NiFiIngestionResponse:
    """NiFi Header와 Body로 전달된 금융회사 원본을 저장하고 벡터화합니다."""
    if not request.records:
        return NiFiIngestionResponse(
            log_id=None,
            status="no_data",
            company_ids=[],
            companies_stored=0,
            chunks_stored=0,
        )

    run = SavingLog(
        job_name="nifi_finlife_company_ingest",
        execution_type="nifi",
        api_name=api_name,
        status="running",
    )
    session.add(run)
    session.commit()

    try:
        documents = SourceTextClient.to_documents(request.records)
        result = IngestionService(session).sync_companies(documents, top_fin_grp_no)
        run.status = "success"
        run.companies_stored = result.companies_stored
        run.chunks_stored = result.chunks_stored
        run.finished_at = datetime.now(UTC)
        session.commit()
        return NiFiIngestionResponse(
            log_id=run.id,
            status=run.status,
            company_ids=result.company_ids,
            companies_stored=result.companies_stored,
            chunks_stored=result.chunks_stored,
        )
    except (TypeError, ValueError) as error:
        _record_failure(session, run, error)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except Exception as error:
        _record_failure(session, run, error)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Embedding or database storage failed") from error


def _record_failure(session: Session, run: SavingLog, error: Exception) -> None:
    """적재 실패를 롤백한 뒤 별도 로그 트랜잭션으로 남깁니다."""
    session.rollback()
    run.status = "failed"
    run.error_message = str(error)
    run.finished_at = datetime.now(UTC)
    session.add(run)
    session.commit()
