import os

# 설정 로딩 전에 테스트 DB·fake provider로 강제 (env가 .env 파일보다 우선)
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://pigfarm:pigfarm-dev@localhost:5435/pigfarm_test"
)
os.environ["NPC_LLM_PROVIDER"] = "fake"
os.environ["CORE_LLM_PROVIDER"] = "fake"
os.environ["EMBEDDING_PROVIDER"] = "fake"

import pytest
from sqlalchemy import create_engine, text

_ADMIN_URL = "postgresql+psycopg://pigfarm:pigfarm-dev@localhost:5435/pigfarm"


@pytest.fixture(scope="session", autouse=True)
def _database():
    admin = create_engine(_ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'pigfarm_test'")
        ).scalar()
        if not exists:
            conn.execute(text("CREATE DATABASE pigfarm_test"))
    admin.dispose()

    import apps.engine.adapter.outbound.orms.event_log_orm  # noqa: F401
    import apps.engine.adapter.outbound.orms.scenario_seed_orm  # noqa: F401
    from core.matrix.grid_oracle_database_manager import Base, get_engine

    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)
    yield


@pytest.fixture()
def db_session(_database):
    from core.matrix.grid_oracle_database_manager import (
        Base,
        get_engine,
        get_session_factory,
    )

    with get_engine().connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(
                text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE')
            )
        conn.commit()
    with get_session_factory()() as session:
        yield session
