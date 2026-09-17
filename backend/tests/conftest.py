import os

from pydantic import ValidationError
from sqlalchemy.engine import make_url

from core.matrix.grid_keymaker_secret_manager import Settings as _Settings

_TEST_DB_NAME = "pigfarm_test"
_ADMIN_DB_NAME = "pigfarm"


def _test_database_url():
    """테스트 DB URL — 비밀번호는 코드에 두지 않는다.
    TEST_DATABASE_URL이 있으면 그대로, 없으면 DATABASE_URL(환경변수 > backend/.env)의
    호스트·계정을 그대로 쓰고 DB 이름만 pigfarm_test로 바꾼다."""
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        url = make_url(explicit)
    else:
        try:
            base = _Settings().database_url
        except ValidationError as exc:
            raise RuntimeError(
                "테스트 DB 접속 정보가 없습니다 — TEST_DATABASE_URL 환경변수를 주거나 "
                "backend/.env에 DATABASE_URL을 설정하세요"
            ) from exc
        url = make_url(base).set(database=_TEST_DB_NAME)
    # 테스트는 매번 모든 테이블을 TRUNCATE한다 — 운영 DB를 가리키면 지워진다
    if not (url.database or "").endswith("_test"):
        raise RuntimeError(
            "테스트 DB 이름은 '_test'로 끝나야 합니다 — TEST_DATABASE_URL의 DB 이름을 확인하세요"
        )
    return url


_TEST_URL = _test_database_url()
_ADMIN_URL = _TEST_URL.set(database=_ADMIN_DB_NAME)

# 설정 로딩 전에 테스트 DB·fake provider로 강제 (env가 .env 파일보다 우선)
os.environ["DATABASE_URL"] = _TEST_URL.render_as_string(hide_password=False)
os.environ["NPC_LLM_PROVIDER"] = "fake"
os.environ["CORE_LLM_PROVIDER"] = "fake"
os.environ["EMBEDDING_PROVIDER"] = "fake"
# .env의 배포 값과 무관하게 로컬 설정·테스트 전용 인스펙터 토큰으로 돈다 (F26b)
os.environ["FRONTEND_BASE_URL"] = "http://localhost:3500"
os.environ["INSPECTOR_TOKEN"] = "test-inspector-token"
# 하루 판 한도는 코드 기본값으로 — .env의 테스트플레이용 상향값이 한도 테스트로 새지 않게
for _name in ("user_daily_attempts", "daily_attempt_cap"):
    os.environ[_name.upper()] = str(_Settings.model_fields[_name].default)

import pytest
from sqlalchemy import create_engine, text


@pytest.fixture(scope="session", autouse=True)
def _database():
    admin = create_engine(_ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": _TEST_URL.database},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{_TEST_URL.database}"'))
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
