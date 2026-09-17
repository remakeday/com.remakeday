from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.matrix.grid_keymaker_secret_manager import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return create_engine(get_settings().database_url)


@lru_cache(maxsize=4)
def get_audit_engine(url: str) -> Engine:
    """감사 기록 전용 작은 풀 — 요청 풀이 다 차도 모델 호출 기록이 요청 연결을 기다리지 않는다."""
    return create_engine(url, pool_size=2, max_overflow=2, pool_timeout=5, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session():
    with get_session_factory()() as session:
        yield session
