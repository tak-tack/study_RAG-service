from fastapi import FastAPI

app = FastAPI(title="Study RAG Service", version="0.1.0")


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    """Report process availability without checking external dependencies."""
    return {"status": "ok"}
