"""NiFi 수집 실행 이력을 ``takhyeong_saving_log``에 매핑합니다.

``app.api.nifi``가 API 정보와 시작·성공·실패 상태, 실제 변경 처리 건수를 기록합니다.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SavingLog(Base):
    """NiFi가 전달한 Finlife 적재 요청의 감사 로그입니다."""

    __tablename__ = "takhyeong_saving_log"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    job_name: Mapped[str] = mapped_column(String(100), nullable=False)
    execution_type: Mapped[str] = mapped_column(String(20), nullable=False)
    api_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    companies_stored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_stored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
