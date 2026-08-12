"""[과거 로컬 프로토타입] 실행 로그의 현재 이름·식별 컬럼으로 전환한 이력입니다.

외부 DB는 이 리비전으로 stamp한 뒤 0006에서 실제 테이블을 생성합니다.
"""

import sqlalchemy as sa

from alembic import op

revision = "0005_saving_log"
down_revision = "0004_top_fin_group"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("ingestion_run", "takhyeong_saving_log")
    op.add_column(
        "takhyeong_saving_log",
        sa.Column("execution_type", sa.String(length=20), nullable=False, server_default="manual"),
    )
    op.add_column(
        "takhyeong_saving_log",
        sa.Column("api_name", sa.String(length=100), nullable=False, server_default="companySearch"),
    )
    op.alter_column("takhyeong_saving_log", "execution_type", server_default=None)
    op.alter_column("takhyeong_saving_log", "api_name", server_default=None)


def downgrade() -> None:
    op.drop_column("takhyeong_saving_log", "api_name")
    op.drop_column("takhyeong_saving_log", "execution_type")
    op.rename_table("takhyeong_saving_log", "ingestion_run")
