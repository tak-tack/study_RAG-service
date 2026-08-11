from dataclasses import dataclass

from langchain_ollama import OllamaEmbeddings
from sqlalchemy import delete, func
from sqlalchemy.dialects.postgresql import insert
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
                company_id = self._upsert_company(company)
                company_ids.append(company_id)
                chunks = split_text(clean_text(source_document.content))
                for chunk_index, chunk in enumerate(chunks):
                    pending_chunks.append((company_id, chunk_index, chunk))
            if not pending_chunks:
                raise ValueError("No usable text remained after cleaning")

            self._session.execute(
                delete(SavingCompanyChunk).where(SavingCompanyChunk.company_id.in_(company_ids))
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
            companies_stored=len(source_documents),
            chunks_stored=len(pending_chunks),
        )

    def _upsert_company(self, company: dict[str, str | None]) -> int:
        statement = insert(SavingCompany).values(**company)
        statement = statement.on_conflict_do_update(
            index_elements=[SavingCompany.top_fin_grp_no, SavingCompany.fin_co_no],
            set_={
                **{
                    key: value
                    for key, value in company.items()
                    if key not in {"top_fin_grp_no", "fin_co_no"}
                },
                "updated_at": func.now(),
            },
        ).returning(SavingCompany.id)
        return self._session.execute(statement).scalar_one()

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
