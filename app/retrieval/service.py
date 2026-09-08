"""pgvector 기반 금융회사 청크 의미 검색 서비스입니다."""

from dataclasses import dataclass

from langchain_ollama import OllamaEmbeddings
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.saving_company import SavingCompany
from app.db.models.saving_company_chunk import SavingCompanyChunk


@dataclass(frozen=True)
class SearchResult:
    """One retrieved chunk with its financial-company metadata."""

    company_id: int
    company_name: str
    fin_co_no: str
    top_fin_grp_no: str
    dcls_month: str
    content: str
    chunk_index: int
    distance: float


class RetrievalService:
    """Embed a query with Ollama and retrieve the closest pgvector chunks."""

    def __init__(self, session: Session, embeddings: OllamaEmbeddings | None = None) -> None:
        self._session = session
        self._embeddings = embeddings or OllamaEmbeddings(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
        )

    def search(
        self, query: str, *, top_k: int = 5, top_fin_grp_no: str | None = None
    ) -> list[SearchResult]:
        """Return the nearest stored chunks using cosine distance (smaller is better)."""
        query_vector = self._embeddings.embed_query(query)
        if len(query_vector) != settings.embedding_dimensions:
            raise RuntimeError(
                "Query embedding dimension does not match EMBEDDING_DIMENSIONS; "
                "use the same embedding model used for ingestion"
            )

        distance = SavingCompanyChunk.embedding.cosine_distance(query_vector).label("distance")
        statement = (
            select(SavingCompanyChunk, SavingCompany, distance)
            .join(SavingCompany, SavingCompany.id == SavingCompanyChunk.company_id)
            .where(SavingCompanyChunk.embedding_model == settings.ollama_embedding_model)
            .order_by(distance)
            .limit(top_k)
        )
        if top_fin_grp_no is not None:
            statement = statement.where(SavingCompanyChunk.top_fin_grp_no == top_fin_grp_no)

        rows = self._session.execute(statement).all()
        return [
            SearchResult(
                company_id=company.id,
                company_name=company.kor_co_nm,
                fin_co_no=company.fin_co_no,
                top_fin_grp_no=chunk.top_fin_grp_no,
                dcls_month=company.dcls_month,
                content=chunk.content,
                chunk_index=chunk.chunk_index,
                distance=float(row_distance),
            )
            for chunk, company, row_distance in rows
        ]
