"""Alembic 실행 환경입니다.

``app.core.config``의 외부 DB 연결값과 ``app.db.models`` 메타데이터를 결합해
마이그레이션을 실행합니다. 공용 ``chatbot`` 스키마와 충돌하지 않도록 전용 이력
테이블 ``takhyeong_saving_alembic_version``을 사용합니다.
"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.db.base import Base
from app.db.models.saving_company import SavingCompany  # noqa: F401
from app.db.models.saving_company_chunk import SavingCompanyChunk  # noqa: F401
from app.db.models.saving_log import SavingLog  # noqa: F401

config = context.config
# ConfigParser treats '%' as interpolation syntax. Escape URL-encoded values such
# as '%3D' only while passing the URL through Alembic's configuration object.
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# The `chatbot` schema is shared with other applications. Keep this project's
# Alembic state separate from their conventional `alembic_version` table.
VERSION_TABLE = "takhyeong_saving_alembic_version"


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=VERSION_TABLE,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
