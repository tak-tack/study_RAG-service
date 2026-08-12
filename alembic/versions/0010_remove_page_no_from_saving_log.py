"""더 이상 사용하지 않는 로그 테이블 ``page_no`` 컬럼을 제거합니다.

NiFi는 ``X-Page-No`` Header를 요청 검증에 사용하지만, 페이지 번호를
``takhyeong_saving_log``에 영구 저장하지 않습니다. 이 마이그레이션은 이 프로젝트
소유 테이블만 변경합니다.
"""

import sqlalchemy as sa

from alembic import op

revision = "0010_remove_log_page_no"
down_revision = "0009_remove_source_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("takhyeong_saving_log", "page_no")


def downgrade() -> None:
    op.add_column("takhyeong_saving_log", sa.Column("page_no", sa.Integer(), nullable=True))
