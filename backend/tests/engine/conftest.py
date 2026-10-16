"""engine 테스트 공유 픽스처."""

import pytest


@pytest.fixture
def logged_in(request, db_session):
    """`guards.require_user`를 로그인된 사용자로 오버라이드 — 로그인 때처럼 users 행도 만든다. 실패해도 finally에서 정리."""
    from main import app
    from apps.engine.adapter.inbound.api.v1 import guards
    from apps.engine.adapter.outbound.repositories.user_repository import UserRepository
    from apps.engine.app.dtos.auth_dto import GoogleProfileDTO, SessionUserDTO

    sub = getattr(request, "param", "tester")
    UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub=sub, email="t@x", name="t"))
    app.dependency_overrides[guards.require_user] = lambda: SessionUserDTO(sub=sub, email="t@x", name="t")
    guards._BUCKETS.clear()
    try:
        yield
    finally:
        app.dependency_overrides.pop(guards.require_user, None)
        guards._BUCKETS.clear()
