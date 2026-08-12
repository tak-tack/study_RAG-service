"""PostgreSQL 연결 엔진과 ORM 세션 팩토리입니다.

``app.core.config``의 DB URL로 연결하며, pgvector 확장 스키마를 검색 경로에
추가합니다. 배치 작업과 수집 서비스가 ``SessionLocal``을 통해 사용합니다.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)


@event.listens_for(engine, "connect")
def include_pgvector_schema(dbapi_connection, _connection_record) -> None:
    """Make the schema that owns pgvector visible to SQLAlchemy's VECTOR casts.

    The shared external database keeps application tables in ``chatbot`` and
    the pgvector extension in a different schema. SQLAlchemy emits casts such
    as ``::VECTOR(1024)`` when binding embeddings, so PostgreSQL must be able
    to resolve the extension type on every pooled connection.
    """
    with dbapi_connection.cursor() as cursor:
        cursor.execute(
            "SELECT extnamespace::regnamespace::text "
            "FROM pg_extension WHERE extname = 'vector'"
        )
        row = cursor.fetchone()
        if row is None:
            return

        vector_schema = row[0]
        cursor.execute("SELECT current_schema()")
        current_schema = cursor.fetchone()[0]
        if vector_schema == current_schema:
            return

        quote = lambda identifier: '"' + identifier.replace('"', '""') + '"'
        cursor.execute(
            f"SET search_path TO {quote(current_schema)}, {quote(vector_schema)}"
        )


SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False)
