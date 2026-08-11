from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SavingLog(Base):
    """Audit record for a manual or scheduled Finlife synchronization."""

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
