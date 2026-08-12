"""금감원 금융회사 원본 데이터를 ``takhyeong_saving_company``에 매핑합니다.

``app.ingestion.service``가 회사 정보를 upsert하며, 청크 모델과 ``company_id``로
연결됩니다. 스키마는 Alembic의 현재 마이그레이션(0006)이 생성합니다.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Identity, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.saving_company_chunk import SavingCompanyChunk


class SavingCompany(Base):
    """A financial company returned by the Finlife company-search API."""

    __tablename__ = "takhyeong_saving_company"
    __table_args__ = (UniqueConstraint("top_fin_grp_no", "fin_co_no"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    top_fin_grp_no: Mapped[str] = mapped_column(String(6), nullable=False)
    dcls_month: Mapped[str] = mapped_column(String(6), nullable=False)
    fin_co_no: Mapped[str] = mapped_column(String(32), nullable=False)
    kor_co_nm: Mapped[str] = mapped_column(String(255), nullable=False)
    dcls_chrg_man: Mapped[str | None] = mapped_column(Text)
    homp_url: Mapped[str | None] = mapped_column(Text)
    cal_tel: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    chunks: Mapped[list["SavingCompanyChunk"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
