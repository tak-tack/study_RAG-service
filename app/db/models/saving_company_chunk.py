from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.saving_company import SavingCompany


class SavingCompanyChunk(Base):
    """A pgvector embedding for one chunk of a financial-company record."""

    __tablename__ = "takhyeong_saving_company_chunk"
    __table_args__ = (UniqueConstraint("company_id", "chunk_index"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    company_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("takhyeong_saving_company.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    top_fin_grp_no: Mapped[str] = mapped_column(String(6), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dimensions), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["SavingCompany"] = relationship(back_populates="chunks")
