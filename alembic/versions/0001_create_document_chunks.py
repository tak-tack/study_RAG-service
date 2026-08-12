"""[과거 로컬 프로토타입] ``document_chunks`` 테이블을 생성한 초기 이력입니다.

현재 외부 ``chatbot`` 스키마에서는 다른 시스템의 동명 테이블과 충돌할 수 있으므로
실행하지 않습니다. 외부 배포는 0005로 stamp한 뒤 0006만 적용합니다.
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_create_document_chunks"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.String(length=255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_chunk"),
    )
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1024) USING embedding::vector")
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")
