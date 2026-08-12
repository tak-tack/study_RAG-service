"""FastAPI 진입점입니다.

현재는 상태 확인 API만 제공합니다. 수집 작업은 ``app.jobs.finlife_company_sync``가
담당하며, 향후 검색·RAG API는 ``app.retrieval`` 및 ``app.rag``와 연결합니다.
"""

from fastapi import FastAPI

app = FastAPI(title="Study RAG Service", version="0.1.0")


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    """Report process availability without checking external dependencies."""
    return {"status": "ok"}
