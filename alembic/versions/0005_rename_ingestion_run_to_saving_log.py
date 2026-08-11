"""Rename ingestion logs and record execution type and API name."""

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
