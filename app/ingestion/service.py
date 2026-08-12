"""금융회사 수집 결과를 원본·청크·벡터 테이블에 적재하는 서비스입니다.

``app.api.nifi``에서 전달받은 문서를 ``app.ingestion.text``로 정제·청킹하고, Ollama와
``app.db.models``를 통해 pgvector 저장까지 하나의 트랜잭션으로 처리합니다.
"""

from dataclasses import dataclass

from langchain_ollama import OllamaEmbeddings
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.saving_company import SavingCompany
from app.db.models.saving_company_chunk import SavingCompanyChunk
from app.ingestion.client import SourceDocument
from app.ingestion.text import clean_text, split_text


@dataclass(frozen=True)
class CompanySyncResult:
    company_ids: list[int]
    companies_stored: int
    chunks_stored: int


class IngestionService:
    """Store Finlife company records and their pgvector chunks."""

    def __init__(self, session: Session, embeddings: OllamaEmbeddings | None = None) -> None:
        self._session = session
        self._embeddings = embeddings or OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )

    def sync_companies(
        self, source_documents: list[SourceDocument], top_fin_grp_no: str
    ) -> CompanySyncResult:
        company_ids: list[int] = []
        pending_chunks: list[tuple[int, int, str]] = []
        try:
            for source_index, source_document in enumerate(source_documents):
                company = self._company_fields(source_document.metadata, source_index, top_fin_grp_no)
                company_id, is_changed = self._upsert_company_if_changed(company)
                company_ids.append(company_id)
                if not is_changed:
                    continue
                chunks = split_text(clean_text(source_document.content))
                for chunk_index, chunk in enumerate(chunks):
                    pending_chunks.append((company_id, chunk_index, chunk))

            if pending_chunks:
                changed_company_ids = list(dict.fromkeys(chunk[0] for chunk in pending_chunks))
                self._session.execute(
                    delete(SavingCompanyChunk).where(SavingCompanyChunk.company_id.in_(changed_company_ids))
                )
                vectors = self._embeddings.embed_documents([chunk[2] for chunk in pending_chunks])
                if len(vectors) != len(pending_chunks):
                    raise RuntimeError("Ollama returned a different number of embeddings than chunks")
                if any(len(vector) != settings.embedding_dimensions for vector in vectors):
                    raise RuntimeError(
                        "Embedding dimension does not match EMBEDDING_DIMENSIONS; use a matching model or migration"
                    )

                self._session.add_all(
                    SavingCompanyChunk(
                        company_id=company_id,
                        chunk_index=chunk_index,
                        top_fin_grp_no=top_fin_grp_no,
                        content=chunk,
                        embedding_model=settings.ollama_embedding_model,
                        embedding=vector,
                    )
                    for (company_id, chunk_index, chunk), vector in zip(
                        pending_chunks, vectors, strict=True
                    )
                )
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

        return CompanySyncResult(
            company_ids=list(dict.fromkeys(company_ids)),
            companies_stored=len({company_id for company_id, _, _ in pending_chunks}),
            chunks_stored=len(pending_chunks),
        )

    def _upsert_company_if_changed(self, company: dict[str, str | None]) -> tuple[int, bool]:
        """회사 원본 필드가 다를 때만 갱신하고 재임베딩 대상으로 표시합니다."""
        existing = self._session.scalar(
            select(SavingCompany).where(
                SavingCompany.top_fin_grp_no == company["top_fin_grp_no"],
                SavingCompany.fin_co_no == company["fin_co_no"],
            )
        )
        if existing is not None:
            if _company_matches(existing, company):
                return existing.id, False
            for field, value in company.items():
                setattr(existing, field, value)
            self._session.flush()
            return existing.id, True

        created = SavingCompany(**company)
        self._session.add(created)
        self._session.flush()
        return created.id, True

    @staticmethod
    def _company_fields(
        metadata: dict[str, object], source_index: int, top_fin_grp_no: str
    ) -> dict[str, str | None]:
        required = ("dcls_month", "fin_co_no", "kor_co_nm")
        missing = [key for key in required if not metadata.get(key)]
        if missing:
            raise ValueError(
                f"Source item {source_index} is missing required company fields: {', '.join(missing)}"
            )
        return {
            "top_fin_grp_no": top_fin_grp_no,
            "dcls_month": str(metadata["dcls_month"]),
            "fin_co_no": str(metadata["fin_co_no"]),
            "kor_co_nm": str(metadata["kor_co_nm"]),
            "dcls_chrg_man": _optional_text(metadata.get("dcls_chrg_man")),
            "homp_url": _optional_text(metadata.get("homp_url")),
            "cal_tel": _optional_text(metadata.get("cal_tel")),
        }


def _optional_text(value: object | None) -> str | None:
    return str(value) if value not in (None, "") else None


def _company_matches(existing: SavingCompany, company: dict[str, str | None]) -> bool:
    """DB 원본 레코드가 이번 수신 데이터와 같은지 저장 컬럼별로 비교합니다."""
    return all(getattr(existing, field) == value for field, value in company.items())
