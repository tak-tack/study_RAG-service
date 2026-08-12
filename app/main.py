"""FastAPI 진입점입니다.

상태 확인 API와 NiFi 수신 웹훅을 제공합니다. NiFi 수신은 ``app.api.nifi``를 통해
``app.ingestion.service``의 청킹·임베딩·저장 흐름과 연결되며, 향후 검색·RAG API는
``app.retrieval`` 및 ``app.rag``에 추가합니다.
"""

from fastapi import FastAPI

from app.api.nifi import router as nifi_router

app = FastAPI(title="Study RAG Service", version="0.1.0")
app.include_router(nifi_router)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    """Report process availability without checking external dependencies."""
    return {"status": "ok"}
