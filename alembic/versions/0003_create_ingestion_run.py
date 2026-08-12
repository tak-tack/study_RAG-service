"""[과거 로컬 프로토타입] ``ingestion_run`` 실행 로그 테이블 생성 이력입니다.

이 테이블은 0005에서 ``takhyeong_saving_log``로 이름이 변경됐으며, 외부 DB에서는
0006이 현재 로그 테이블을 직접 생성합니다.
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_ingestion_run"
down_revision = "0002_saving_company"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_run",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("job_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("companies_stored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunks_stored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
    )


def downgrade() -> None:
    op.drop_table("ingestion_run")
