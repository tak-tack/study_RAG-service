"""벡터 검색 서비스가 Ollama 질의 벡터와 DB 결과를 연결하는지 검증합니다."""

from app.core.config import settings
from app.db.models.saving_company import SavingCompany
from app.db.models.saving_company_chunk import SavingCompanyChunk
from app.retrieval.service import RetrievalService


class FakeEmbeddings:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def embed_query(self, query: str) -> list[float]:
        self.queries.append(query)
        return [0.0] * settings.embedding_dimensions


class FakeResult:
    def __init__(self, rows: list[tuple[SavingCompanyChunk, SavingCompany, float]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[SavingCompanyChunk, SavingCompany, float]]:
        return self._rows


class FakeSession:
    def __init__(self, rows: list[tuple[SavingCompanyChunk, SavingCompany, float]]) -> None:
        self._rows = rows
        self.statement = None

    def execute(self, statement: object) -> FakeResult:
        self.statement = statement
        return FakeResult(self._rows)


def test_search_returns_company_metadata_and_distance() -> None:
    company = SavingCompany(
        id=7,
        top_fin_grp_no="020000",
        dcls_month="202607",
        fin_co_no="0010001",
        kor_co_nm="우리은행",
    )
    chunk = SavingCompanyChunk(
        id=11,
        company_id=7,
        chunk_index=0,
        top_fin_grp_no="020000",
        content="우리은행 예금 상품 안내",
        embedding_model=settings.ollama_embedding_model,
        embedding=[0.0] * settings.embedding_dimensions,
    )
    embeddings = FakeEmbeddings()
    session = FakeSession([(chunk, company, 0.18)])

    results = RetrievalService(session, embeddings=embeddings).search(
        "예금 상품을 취급하는 은행", top_k=3, top_fin_grp_no="020000"
    )

    assert embeddings.queries == ["예금 상품을 취급하는 은행"]
    assert len(results) == 1
    assert results[0].company_name == "우리은행"
    assert results[0].content == "우리은행 예금 상품 안내"
    assert results[0].distance == 0.18
