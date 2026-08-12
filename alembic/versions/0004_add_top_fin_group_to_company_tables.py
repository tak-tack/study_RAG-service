"""[과거 로컬 프로토타입] 권역 코드를 기존 회사·청크 테이블에 추가한 이력입니다.

로컬 기존 데이터를 삭제하는 작업이 포함되어 외부 DB에는 실행하지 않습니다.
현재 테이블에는 0006이 ``top_fin_grp_no``를 처음부터 포함해 생성합니다.
"""

import sqlalchemy as sa

from alembic import op

revision = "0004_top_fin_group"
down_revision = "0003_ingestion_run"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The legacy data has no trustworthy group association. It is intentionally replaced
    # by the next scheduled synchronization, which records the source group on every row.
    op.execute("DELETE FROM takhyeong_saving_company_chunk")
    op.execute("DELETE FROM takhyeong_saving_company")
    op.execute("ALTER TABLE takhyeong_saving_company_chunk ALTER COLUMN id RESTART WITH 1")
    op.execute("ALTER TABLE takhyeong_saving_company ALTER COLUMN id RESTART WITH 1")

    op.add_column(
        "takhyeong_saving_company",
        sa.Column("top_fin_grp_no", sa.String(length=6), nullable=True),
    )
    op.alter_column("takhyeong_saving_company", "top_fin_grp_no", nullable=False)
    op.drop_constraint(
        "uq_takhyeong_saving_company_fin_co_no",
        "takhyeong_saving_company",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_takhyeong_saving_company_group_fin_co_no",
        "takhyeong_saving_company",
        ["top_fin_grp_no", "fin_co_no"],
    )

    op.add_column(
        "takhyeong_saving_company_chunk",
        sa.Column("top_fin_grp_no", sa.String(length=6), nullable=True),
    )
    op.alter_column("takhyeong_saving_company_chunk", "top_fin_grp_no", nullable=False)


def downgrade() -> None:
    op.drop_column("takhyeong_saving_company_chunk", "top_fin_grp_no")
    op.drop_constraint(
        "uq_takhyeong_saving_company_group_fin_co_no",
        "takhyeong_saving_company",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_takhyeong_saving_company_fin_co_no",
        "takhyeong_saving_company",
        ["fin_co_no"],
    )
    op.drop_column("takhyeong_saving_company", "top_fin_grp_no")
