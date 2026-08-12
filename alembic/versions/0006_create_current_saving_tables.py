"""현재 외부 ``chatbot`` 스키마용 금융회사 테이블을 생성하는 마이그레이션입니다.

``app.db.models``의 ``takhyeong_saving_company``, 청크, 로그 모델과 대응하며,
공유 ``document_chunks``를 수정하지 않습니다. ``alembic/env.py``에서 전용 이력
테이블을 사용해 이 마이그레이션을 안전하게 적용합니다.

The earlier revisions represent the local prototype's history.  A shared
`chatbot` schema can already contain an unrelated `document_chunks` table, so
external deployments are stamped at revision 0005 before this revision is run.
This migration then creates only the three tables owned by this project.
"""

import sqlalchemy as sa

from alembic import op

revision = "0006_current_saving_tables"
down_revision = "0005_saving_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    vector_schema = connection.execute(
        sa.text(
            "SELECT extnamespace::regnamespace::text "
            "FROM pg_extension WHERE extname = 'vector'"
        )
    ).scalar_one_or_none()
    if vector_schema is None:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        vector_schema = connection.execute(
            sa.text(
                "SELECT extnamespace::regnamespace::text "
                "FROM pg_extension WHERE extname = 'vector'"
            )
        ).scalar_one()

    quote = connection.dialect.identifier_preparer.quote
    vector_type = f"{quote(vector_schema)}.vector(1024)"

    op.create_table(
        "takhyeong_saving_company",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("top_fin_grp_no", sa.String(length=6), nullable=False),
        sa.Column("dcls_month", sa.String(length=6), nullable=False),
        sa.Column("fin_co_no", sa.String(length=32), nullable=False),
        sa.Column("kor_co_nm", sa.String(length=255), nullable=False),
        sa.Column("dcls_chrg_man", sa.Text()),
        sa.Column("homp_url", sa.Text()),
        sa.Column("cal_tel", sa.String(length=64)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "top_fin_grp_no",
            "fin_co_no",
            name="uq_takhyeong_saving_company_group_fin_co_no",
        ),
    )
    op.create_table(
        "takhyeong_saving_company_chunk",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("top_fin_grp_no", sa.String(length=6), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["company_id"], ["takhyeong_saving_company.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "company_id",
            "chunk_index",
            name="uq_takhyeong_saving_company_chunk",
        ),
    )
    op.execute(
        "ALTER TABLE takhyeong_saving_company_chunk "
        f"ALTER COLUMN embedding TYPE {vector_type} USING embedding::{vector_type}"
    )
    op.create_index(
        "ix_takhyeong_saving_company_chunk_company_id",
        "takhyeong_saving_company_chunk",
        ["company_id"],
    )
    op.create_table(
        "takhyeong_saving_log",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("job_name", sa.String(length=100), nullable=False),
        sa.Column("execution_type", sa.String(length=20), nullable=False),
        sa.Column("api_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("companies_stored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunks_stored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_takhyeong_saving_company_chunk_company_id",
        table_name="takhyeong_saving_company_chunk",
    )
    op.drop_table("takhyeong_saving_log")
    op.drop_table("takhyeong_saving_company_chunk")
    op.drop_table("takhyeong_saving_company")
