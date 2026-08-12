"""[과거 로컬 프로토타입] 금융회사·청크 테이블 최초 생성 이력입니다.

0001의 로컬 ``document_chunks``에 의존하므로 공유 외부 DB에는 적용하지 않습니다.
현재 외부 배포용 테이블 생성은 0006 마이그레이션이 담당합니다.
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_saving_company"
down_revision = "0001_create_document_chunks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "takhyeong_saving_company",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("dcls_month", sa.String(length=6), nullable=False),
        sa.Column("fin_co_no", sa.String(length=32), nullable=False),
        sa.Column("kor_co_nm", sa.String(length=255), nullable=False),
        sa.Column("dcls_chrg_man", sa.Text()),
        sa.Column("homp_url", sa.Text()),
        sa.Column("cal_tel", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("fin_co_no", name="uq_takhyeong_saving_company_fin_co_no"),
    )
    op.create_table(
        "takhyeong_saving_company_chunk",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["company_id"], ["takhyeong_saving_company.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("company_id", "chunk_index", name="uq_takhyeong_saving_company_chunk"),
    )
    op.execute(
        "ALTER TABLE takhyeong_saving_company_chunk "
        "ALTER COLUMN embedding TYPE vector(1024) USING embedding::vector"
    )
    op.create_index(
        "ix_takhyeong_saving_company_chunk_company_id",
        "takhyeong_saving_company_chunk",
        ["company_id"],
    )
    op.execute(
        """
        INSERT INTO takhyeong_saving_company
            (dcls_month, fin_co_no, kor_co_nm, dcls_chrg_man, homp_url, cal_tel)
        SELECT DISTINCT ON (metadata->>'fin_co_no')
            metadata->>'dcls_month',
            metadata->>'fin_co_no',
            metadata->>'kor_co_nm',
            NULLIF(metadata->>'dcls_chrg_man', ''),
            NULLIF(metadata->>'homp_url', ''),
            NULLIF(metadata->>'cal_tel', '')
        FROM document_chunks
        WHERE NULLIF(metadata->>'fin_co_no', '') IS NOT NULL
        ORDER BY metadata->>'fin_co_no', created_at DESC
        """
    )
    op.execute(
        """
        INSERT INTO takhyeong_saving_company_chunk
            (company_id, chunk_index, content, embedding_model, embedding, created_at)
        SELECT company.id, chunk.chunk_index, chunk.content, chunk.embedding_model,
               chunk.embedding, chunk.created_at
        FROM document_chunks AS chunk
        JOIN takhyeong_saving_company AS company
          ON company.fin_co_no = chunk.metadata->>'fin_co_no'
        """
    )
    op.drop_table("document_chunks")


def downgrade() -> None:
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("document_id", sa.String(length=255), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False, server_default="migrated"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(1024) USING embedding::vector")
    op.execute(
        """
        INSERT INTO document_chunks
            (document_id, chunk_index, content, metadata, embedding_model, embedding, created_at)
        SELECT company.fin_co_no, chunk.chunk_index, chunk.content,
               json_build_object(
                    'dcls_month', company.dcls_month,
                    'fin_co_no', company.fin_co_no,
                    'kor_co_nm', company.kor_co_nm,
                    'dcls_chrg_man', company.dcls_chrg_man,
                    'homp_url', company.homp_url,
                    'cal_tel', company.cal_tel
               ),
               chunk.embedding_model, chunk.embedding, chunk.created_at
        FROM takhyeong_saving_company_chunk AS chunk
        JOIN takhyeong_saving_company AS company ON company.id = chunk.company_id
        """
    )
    op.drop_index("ix_takhyeong_saving_company_chunk_company_id",
                  table_name="takhyeong_saving_company_chunk")
    op.drop_table("takhyeong_saving_company_chunk")
    op.drop_table("takhyeong_saving_company")
