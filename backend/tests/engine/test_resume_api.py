"""이어하기 API — 진행 중인 판 찾기·단계 매핑·포기 (설계 2026-10-16 §2.1~2.3, §4)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.engine.adapter.outbound.orms.event_log_orm import EventLogOrm
from apps.engine.adapter.outbound.orms.game_state_orm import AttemptOrm
from apps.engine.adapter.outbound.repositories.game_repository import AttemptRepository, LoopRepository
from apps.engine.adapter.outbound.repositories.user_repository import UserRepository
from apps.engine.app.dtos.auth_dto import GoogleProfileDTO

ACTIVE = "/api/v1/me/attempts/active"
ABANDON = "/api/v1/me/attempts/active/abandon"


def _limit() -> int:
    from core.matrix import grid_keymaker_secret_manager as cfg
    return cfg.get_settings().user_daily_attempts


def _play_until(client, state: str) -> dict:
    """새 판 하나를 state까지 실제 API로 진행한다(가짜 모델). none = 판만 있고 회차 없음."""
    ids: dict = {}

    def new_session():
        ids["attempt_id"] = client.post("/sessions", json={}).json()["attempt_id"]

    def start_day():
        ids["loop_id"] = client.post(f"/sessions/{ids['attempt_id']}/loops").json()["loop_id"]

    def end_day():
        for _ in range(6):
            client.post(f"/loops/{ids['loop_id']}/beats/next")

    def draft():
        ids["night_id"] = client.post(f"/loops/{ids['loop_id']}/night/draft",
                                      json={"tapped_note_ids": [], "free_text": "채연이 밥을 남겼다."}).json()["night_id"]

    def submit():
        assert client.post(f"/nights/{ids['night_id']}/submit").status_code == 200

    def choose_rule():
        client.get(f"/nights/{ids['night_id']}/options")
        assert client.post(f"/nights/{ids['night_id']}/rule", json={"choice": "1"}).json()["ok"]

    steps = [("none", new_session), ("day", start_day), ("night_pending", end_day),
             ("night_draft", draft), ("intervention", submit), ("closed", choose_rule)]
    for name, step in steps:
        step()
        if name == state:
            return ids
    raise AssertionError(f"모르는 상태: {state}")


@pytest.mark.parametrize("state,phase", [
    ("none", "entry"), ("day", "day"), ("night_pending", "night"), ("night_draft", "night"),
    ("scored", "score"), ("intervention", "god"), ("closed", "entry"),
])
def test_resume_phase_follows_latest_loop_state(db_session, logged_in, state, phase):
    from main import app
    with TestClient(app) as client:
        ids = _play_until(client, "intervention" if state == "scored" else state)
        if state == "scored":  # 지금 엔진은 scored를 거치지 않는다(제출 뒤 곧바로 intervention) — 표의 행을 직접 만든다
            loop = LoopRepository(db_session).latest_for(uuid.UUID(ids["attempt_id"]))
            loop.state = "scored"
            db_session.commit()
        res = client.get(ACTIVE)
    assert res.status_code == 200
    body = res.json()
    assert body["attempt"]["attempt_id"] == ids["attempt_id"]
    assert len(body["attempt"]["entry_lines"]) == 3
    assert body["resume_phase"] == phase
    assert (body["loop"] is None) == (state == "none")  # 회차 없음만 loop가 없다 — 프론트가 선택 화면 없이 그대로 쓰는 기준
    assert (body["night"] is None) == (phase in ("entry", "day"))
    assert body["daily_limit"] == _limit()


def test_day_resume_returns_current_scene_and_writes_nothing(db_session, logged_in):
    from main import app
    with TestClient(app) as client:
        ids = _play_until(client, "day")
        client.post(f"/loops/{ids['loop_id']}/beats/next")
        db_session.expire_all()
        before = db_session.scalar(select(func.count()).select_from(EventLogOrm))
        first, second = client.get(ACTIVE).json(), client.get(ACTIVE).json()
        db_session.expire_all()
        after = db_session.scalar(select(func.count()).select_from(EventLogOrm))
    assert after == before
    assert first == second
    loop = first["loop"]
    assert (loop["loop_id"], loop["beat"]) == (ids["loop_id"], 2)
    assert loop["lines"] and loop["lines"][0]["kind"] == "scene"
    assert (loop["ambient"], loop["aftermath"]) == (None, None)


def test_draft_and_god_resume_carry_night_data(db_session, logged_in):
    from main import app
    with TestClient(app) as client:
        ids = _play_until(client, "night_draft")
        drafted = client.get(ACTIVE).json()["night"]
        client.post(f"/nights/{ids['night_id']}/submit")
        god = client.get(ACTIVE).json()["night"]
    assert (drafted["night_id"], drafted["claims"], drafted["submit"]) == (ids["night_id"], ["채연이 밥을 남겼다."], None)
    assert (god["night_id"], god["questions_left"]) == (ids["night_id"], 3)
    assert god["submit"]["loop_n"] == 1 and god["submit"]["intervention_available"] is True
    assert isinstance(god["submit"]["suggested_questions"], list)


def test_abandoned_attempt_is_not_active_but_still_counts_today(db_session, logged_in):
    from main import app
    with TestClient(app) as client:
        ids = _play_until(client, "none")
        assert client.get(ACTIVE).json()["today_remaining"] == _limit() - 1
        res = client.post(ABANDON)
        assert res.status_code == 204 and res.content == b""
        body = client.get(ACTIVE).json()
        assert (body["attempt"], body["resume_phase"], body["loop"], body["night"]) == (None, None, None, None)
        assert body["today_remaining"] == _limit() - 1  # 포기한 판도 그날 판 수에 남는다 — "1회 차감"의 실체
        assert client.post(f"/sessions/{ids['attempt_id']}/loops").status_code == 409  # 포기한 판은 다시 열 수 없다
    db_session.expire_all()
    assert db_session.get(AttemptOrm, uuid.UUID(ids["attempt_id"])).status == "abandoned"


def test_abandon_without_active_attempt_is_a_noop(db_session, logged_in):
    from main import app
    with TestClient(app) as client:
        assert client.post(ABANDON).status_code == 204
        assert client.get(ACTIVE).json() == {
            "attempt": None, "resume_phase": None, "loop": None, "night": None,
            "today_remaining": _limit(), "daily_limit": _limit()}


def test_other_users_attempt_is_never_active(db_session, logged_in):
    from main import app
    alice = UserRepository(db_session).upsert_from_google(GoogleProfileDTO(sub="alice", email="", name="alice"))
    AttemptRepository(db_session).create(None, user_id=alice.id)
    with TestClient(app) as client:
        assert client.get(ACTIVE).json()["attempt"] is None
        assert client.post(ABANDON).status_code == 204
    db_session.expire_all()
    assert db_session.scalars(select(AttemptOrm.status)).all() == ["active"]  # 남의 판은 포기되지 않는다


def test_abandoning_latest_does_not_resurface_older_active(db_session, logged_in):
    """사용자 결정 2026-10-16 — 진행 중인 판은 최신 판이 active일 때만. 최신 판을 포기하면 오래된 active 판이 있어도 attempt=null."""
    from main import app
    with TestClient(app) as client:
        old = _play_until(client, "none")["attempt_id"]
        new = _play_until(client, "none")["attempt_id"]
        assert client.get(ACTIVE).json()["attempt"]["attempt_id"] == new
        assert client.post(ABANDON).status_code == 204
        body = client.get(ACTIVE).json()
        assert (body["attempt"], body["resume_phase"]) == (None, None)
        assert client.post(ABANDON).status_code == 204  # 두 번째 포기는 아무것도 하지 않는다 — 오래된 판을 포기하지 않는다
    db_session.expire_all()
    assert db_session.get(AttemptOrm, uuid.UUID(old)).status == "active"  # 오래된 판은 건드리지 않는다
    assert db_session.get(AttemptOrm, uuid.UUID(new)).status == "abandoned"


@pytest.mark.parametrize("method,path", [("GET", ACTIVE), ("POST", ABANDON)])
def test_me_routes_require_login(db_session, monkeypatch, method, path):
    from main import app
    from apps.engine.adapter.inbound.api.v1 import guards
    from core.matrix import grid_keymaker_secret_manager as cfg
    monkeypatch.setattr(cfg.get_settings(), "guard_auth", "on")
    guards._BUCKETS.clear()
    with TestClient(app) as client:
        assert client.request(method, path).status_code == 401
