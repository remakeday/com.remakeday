"""회원탈퇴 — 탈퇴한 사용자의 행은 모든 테이블에서 0, 다른 사용자의 행은 그대로, 세션 쿠키 삭제 (설계 2026-10-16 §2.4)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
from apps.engine.adapter.outbound.orms.game_state_orm import (
    AttemptOrm,
    LoopOrm,
    NightOrm,
    NoteOrm,
    NpcStateOrm,
    RuleOrm,
    SurveyVoteOrm,
)
from apps.engine.adapter.outbound.orms.user_orm import UserOrm
from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
from apps.engine.adapter.outbound.repositories.game_repository import (
    AttemptRepository,
    LoopRepository,
    NightRepository,
    NoteRepository,
    RuleRepository,
    SurveyVoteRepository,
)
from apps.engine.adapter.outbound.repositories.user_repository import UserRepository
from apps.engine.adapter.outbound.security.session_token_signer import SessionTokenSigner
from apps.engine.app.dtos.auth_dto import GoogleProfileDTO, SessionUserDTO
from apps.engine.app.dtos.event_log_dto import GuardEvent, SessionStartEvent
from apps.engine.domain.value_objects.game_constants import SURVEY_SCORE_FIELDS

SECRET = "test-secret-withdraw"


def _footprint(db_session, user_id, attempt_ids, sub) -> dict[str, int]:
    """한 사용자가 남긴 행 수 — 탈퇴 전에 잡아 둔 user_id·attempt_ids로 센다(탈퇴 뒤에는 users 행으로 찾을 수 없다)."""
    db_session.expire_all()
    loop_ids = select(LoopOrm.id).where(LoopOrm.attempt_id.in_(attempt_ids))

    def count(model, *where) -> int:
        return db_session.scalar(select(func.count()).select_from(model).where(*where))

    return {
        "users": count(UserOrm, UserOrm.id == user_id),
        "attempts": count(AttemptOrm, AttemptOrm.id.in_(attempt_ids)),
        "loops": count(LoopOrm, LoopOrm.attempt_id.in_(attempt_ids)),
        "npc_states": count(NpcStateOrm, NpcStateOrm.loop_id.in_(loop_ids)),
        "nights": count(NightOrm, NightOrm.loop_id.in_(loop_ids)),
        "notes": count(NoteOrm, NoteOrm.attempt_id.in_(attempt_ids)),
        "rules": count(RuleOrm, RuleOrm.attempt_id.in_(attempt_ids)),
        "survey_votes": count(SurveyVoteOrm, SurveyVoteOrm.user_id == user_id),
        "events": count(EventLogOrm, EventLogOrm.session_id.in_(attempt_ids)),
        "guard_events": count(EventLogOrm, EventLogOrm.type == "guard",
                              EventLogOrm.payload["user_sub"].astext == sub),
    }


def _seed(db_session, sub: str):
    """sub 사용자의 판 하나 — 탈퇴가 지워야 할 모든 테이블에 한 줄 이상."""
    user = UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub=sub, email=f"{sub}@x", name=sub))
    attempt = AttemptRepository(db_session).create(None, user_id=user.id)
    loop = LoopRepository(db_session).create(LoopOrm(attempt_id=attempt.id, loop_n=1, budget_left=8),
                                             [NpcStateOrm(code="chaeyeon", name="채연")])
    NightRepository(db_session).create(NightOrm(loop_id=loop.id))
    NoteRepository(db_session).upsert(attempt.id, kind="fragment", text="트럭 소리.", loop_n=1,
                                      source_key=f"{loop.id}:scene-1")
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="user_choice", target="채연",
                                           when_beat=None, effect="enforce", action="쉰다", created_loop=1))
    SurveyVoteRepository(db_session).record(attempt.id, user.id, skipped=True,
                                            scores=dict.fromkeys(SURVEY_SCORE_FIELDS))
    events = EventLogRepository(db_session)
    events.record(attempt.id, SessionStartEvent(session=str(attempt.id), attempt_n=1, prior_cell_results=None))
    events.record(uuid.uuid4(), GuardEvent(layer="user_daily", reason="오늘은 여기까지", ip_hash="x", user_sub=sub))
    return user.id, [attempt.id]


# ── 저장소 ────────────────────────────────────────────────────


def test_delete_with_data_removes_every_row_of_one_user_only(db_session):
    """Review Focus 5 — 같은 테이블을 쓰는 다른 사용자의 판·평가·guard 이벤트는 그대로."""
    alice, bob = _seed(db_session, "alice"), _seed(db_session, "bob")
    alice_before, bob_before = _footprint(db_session, *alice, "alice"), _footprint(db_session, *bob, "bob")
    assert all(alice_before.values()), alice_before  # 지울 행이 모든 테이블에 있었다
    UserRepository(db_session).delete_with_data(alice[0], "alice")
    assert _footprint(db_session, *alice, "alice") == dict.fromkeys(alice_before, 0)
    assert _footprint(db_session, *bob, "bob") == bob_before


def test_delete_with_data_is_all_or_nothing(db_session, monkeypatch):
    """Review Focus 5 — 커밋이 실패하면 하나도 지워지지 않는다(한 트랜잭션)."""
    alice = _seed(db_session, "alice")
    before = _footprint(db_session, *alice, "alice")

    def failing_commit():
        raise RuntimeError("commit failed")

    monkeypatch.setattr(db_session, "commit", failing_commit)
    with pytest.raises(RuntimeError):
        UserRepository(db_session).delete_with_data(alice[0], "alice")
    monkeypatch.undo()
    assert _footprint(db_session, *alice, "alice") == before


# ── HTTP (실제 세션 쿠키) ─────────────────────────────────────


@pytest.fixture
def cookie_auth(db_session, monkeypatch):
    """실제 세션 쿠키 경로 — GUARD_AUTH=on. 속도 제한은 풀고 판 수 한도는 넉넉히 둔다."""
    from apps.engine.adapter.inbound.api.v1 import guards
    from core.matrix import grid_keymaker_secret_manager as cfg
    s = cfg.get_settings()
    for key, value in {"guard_auth": "on", "session_secret": SECRET, "ip_sessions_per_minute": 1000,
                       "ip_actions_per_minute": 1000, "user_daily_attempts": 10,
                       "frontend_base_url": "http://localhost:3500"}.items():
        monkeypatch.setattr(s, key, value)
    guards._BUCKETS.clear()
    yield s
    guards._BUCKETS.clear()


def _token(sub: str) -> str:
    return SessionTokenSigner(SECRET).issue(SessionUserDTO(sub=sub, email=f"{sub}@x", name=sub), 3600)


def _client(app, sub: str, db_session=None) -> TestClient:
    """세션 쿠키를 든 클라이언트. db_session을 주면 Google 로그인 콜백처럼 users 행을 먼저 만든다."""
    if db_session is not None:
        UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub=sub, email=f"{sub}@x", name=sub))
    client = TestClient(app)
    client.cookies.set("rd_session", _token(sub))
    return client


def _play_one_night(client) -> None:
    """실제 게임 한 밤 — 회차·NPC 상태·노트·밤·규칙·평가·이벤트가 실제 경로로 생긴다(빠뜨린 테이블을 잡는다)."""
    attempt_id = client.post("/sessions", json={}).json()["attempt_id"]
    loop_id = client.post(f"/sessions/{attempt_id}/loops").json()["loop_id"]
    for _ in range(6):
        client.post(f"/loops/{loop_id}/beats/next")
    night_id = client.post(f"/loops/{loop_id}/night/draft",
                           json={"tapped_note_ids": [], "free_text": "채연이 밥을 남겼다."}).json()["night_id"]
    assert client.post(f"/nights/{night_id}/submit").status_code == 200
    client.get(f"/nights/{night_id}/options")
    assert client.post(f"/nights/{night_id}/rule", json={"choice": "1"}).json()["ok"]
    assert client.post(f"/attempts/{attempt_id}/survey", json={"skipped": True}).status_code == 200


def _ids(db_session, sub: str):
    db_session.expire_all()
    user = db_session.scalar(select(UserOrm).where(UserOrm.google_sub == sub))
    return user.id, list(db_session.scalars(select(AttemptOrm.id).where(AttemptOrm.user_id == user.id)))


def test_withdraw_deletes_only_that_users_rows(cookie_auth, db_session, monkeypatch):
    from main import app
    with TestClient(app):  # lifespan(시드) 1회
        alice, bob = _client(app, "google-alice", db_session), _client(app, "google-bob", db_session)
        _play_one_night(alice)
        _play_one_night(bob)
        monkeypatch.setattr(cookie_auth, "user_daily_attempts", 1)
        assert alice.post("/sessions", json={}).status_code == 403  # guard 이벤트(user_sub) 한 줄씩
        assert bob.post("/sessions", json={}).status_code == 403
        alice_ids, bob_ids = _ids(db_session, "google-alice"), _ids(db_session, "google-bob")
        alice_before = _footprint(db_session, *alice_ids, "google-alice")
        bob_before = _footprint(db_session, *bob_ids, "google-bob")
        assert all(alice_before.values()), alice_before

        res = alice.delete("/api/v1/auth/me")

    assert res.status_code == 204
    set_cookie = res.headers["set-cookie"]
    assert 'rd_session=""' in set_cookie and "Max-Age=0" in set_cookie
    assert _footprint(db_session, *alice_ids, "google-alice") == dict.fromkeys(alice_before, 0)
    assert _footprint(db_session, *bob_ids, "google-bob") == bob_before


def test_withdraw_of_user_without_row_is_204(cookie_auth, db_session):
    from main import app
    with TestClient(app):
        res = _client(app, "google-ghost").delete("/api/v1/auth/me")
    assert res.status_code == 204
    assert 'rd_session=""' in res.headers["set-cookie"]


def test_withdraw_requires_login(cookie_auth):
    from main import app
    with TestClient(app) as client:
        assert client.delete("/api/v1/auth/me").status_code == 401


def test_withdrawn_session_cookie_cannot_recreate_user(cookie_auth, db_session):
    """사용자 결정 2026-10-16 — 탈퇴 뒤 남은(아직 서명이 유효한) 쿠키로 새 판을 요청해도 401이고 users 행이 다시 생기지 않는다."""
    from main import app
    with TestClient(app):
        alice = _client(app, "google-alice", db_session)
        assert alice.post("/sessions", json={}).status_code == 200
        assert alice.delete("/api/v1/auth/me").status_code == 204
        leftover = TestClient(app)  # 브라우저가 쿠키를 지우지 않았거나 누가 복사해 둔 경우
        leftover.cookies.set("rd_session", _token("google-alice"))
        res = leftover.post("/sessions", json={})
        active = leftover.get("/api/v1/me/attempts/active")
    assert res.status_code == 401 and res.json() == {"detail": "로그인이 필요하다"}
    assert active.status_code == 200 and active.json()["attempt"] is None  # 조회는 읽기만 — 행을 만들지 않는다
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(UserOrm).where(UserOrm.google_sub == "google-alice")) == 0
    assert db_session.scalar(select(func.count()).select_from(AttemptOrm)) == 0


def test_session_start_without_users_row_is_rejected_without_upsert():
    """유스케이스 단위 — users 행이 없으면 UnknownUser, upsert하지 않는다(판 수 조회 전에 멈춘다)."""
    from types import SimpleNamespace

    from apps.engine.app.use_cases.session_interactor import SessionInteractor, UnknownUser

    class Users:
        def __init__(self):
            self.upserts = []

        def get_by_sub(self, sub):
            return None

        def upsert_from_google(self, profile):
            self.upserts.append(profile.sub)
            return SimpleNamespace(id=uuid.uuid4())

    users = Users()
    uc = SessionInteractor(attempts=None, event_log=None, scenario=None, users=users,
                           user_daily_attempts=3, daily_attempt_cap=200)
    with pytest.raises(UnknownUser):
        uc.start(None, SessionUserDTO(sub="google-gone", email="", name=""), "iphash")
    assert users.upserts == []
