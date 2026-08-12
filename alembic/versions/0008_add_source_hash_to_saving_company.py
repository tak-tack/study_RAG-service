"""Add the temporary source_hash column used by revision history.

This revision was applied before the design changed to direct field comparison.
Revision 0009 removes the column; this file remains so existing Alembic history
can be upgraded safely.
"""

import sqlalchemy as sa

from alembic import op

revision = "0008_saving_company_source_hash"
down_revision = "0007_saving_log_page_no"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "takhyeong_saving_company",
        sa.Column("source_hash", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("takhyeong_saving_company", "source_hash")
