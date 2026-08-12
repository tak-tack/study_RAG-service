"""더 이상 사용하지 않는 ``source_hash`` 컬럼을 제거합니다.

``app.ingestion.service``는 원본 회사 컬럼을 직접 비교해 변경 여부를 판단하므로,
별도 해시 저장 컬럼 없이 동일 데이터의 재임베딩을 생략합니다.
"""

import sqlalchemy as sa

from alembic import op

revision = "0009_remove_source_hash"
down_revision = "0008_saving_company_source_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("takhyeong_saving_company", "source_hash")


def downgrade() -> None:
    op.add_column(
        "takhyeong_saving_company",
        sa.Column("source_hash", sa.String(length=64), nullable=True),
    )
