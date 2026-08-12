"""NiFi 수신 요청의 ``X-Page-No`` 값을 실행 로그에 저장합니다.

``app.api.nifi``와 ``app.db.models.saving_log``가 사용하는 ``page_no`` 컬럼을
``takhyeong_saving_log``에 추가합니다. 기존 수동 실행 로그는 NULL로 보존합니다.
"""

import sqlalchemy as sa

from alembic import op

revision = "0007_saving_log_page_no"
down_revision = "0006_current_saving_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("takhyeong_saving_log", sa.Column("page_no", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("takhyeong_saving_log", "page_no")
