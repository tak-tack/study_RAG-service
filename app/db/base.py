"""SQLAlchemy ORM 모델의 공통 선언 기반입니다.

``app.db.models``의 테이블 모델이 이를 상속하고, ``alembic/env.py``가
``Base.metadata``를 참조해 마이그레이션 대상 메타데이터를 구성합니다.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
