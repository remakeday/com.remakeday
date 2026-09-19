"""플레이 평가 엔드포인트 — 소유자만, 판당 한 번, 범위 밖 점수는 422."""

import uuid

from fastapi.testclient import TestClient

from apps.engine.adapter.outbound.orms.game_state_orm import SurveyVoteOrm

FULL = {"skipped": False, "fun": 5, "novelty": 4, "ai_agency": 5, "polish": 3, "recommend": 4}


def _own_attempt(c) -> str:
    return c.post("/sessions", json={}).json()["attempt_id"]


def test_owner_can_vote_once(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        first = c.post(f"/attempts/{attempt_id}/survey", json=FULL)
        assert first.status_code == 200 and first.json() == {"recorded": True}
        again = c.post(f"/attempts/{attempt_id}/survey", json={**FULL, "fun": 1})
        assert again.status_code == 200 and again.json() == {"recorded": False}
        row = db_session.query(SurveyVoteOrm).filter_by(attempt_id=uuid.UUID(attempt_id)).one()
        assert (row.fun, row.novelty, row.ai_agency, row.polish, row.recommend) == (5, 4, 5, 3, 4)


def test_skip_with_scores_clears_scores(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        r = c.post(f"/attempts/{attempt_id}/survey", json={"skipped": True, "fun": 3})
        assert r.status_code == 200 and r.json() == {"recorded": True}
        row = db_session.query(SurveyVoteOrm).filter_by(attempt_id=uuid.UUID(attempt_id)).one()
        assert row.skipped is True
        assert (row.fun, row.novelty, row.ai_agency, row.polish, row.recommend) == (None, None, None, None, None)


def test_skip_is_accepted_without_scores(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        r = c.post(f"/attempts/{attempt_id}/survey", json={"skipped": True})
        assert r.status_code == 200 and r.json() == {"recorded": True}


def test_partial_answer_is_accepted(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        r = c.post(f"/attempts/{attempt_id}/survey", json={"skipped": False, "fun": 4})
        assert r.status_code == 200 and r.json() == {"recorded": True}


def test_no_score_without_skip_is_treated_as_skip(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        r = c.post(f"/attempts/{attempt_id}/survey", json={"skipped": False})
        assert r.status_code == 200 and r.json() == {"recorded": True}


def test_score_outside_range_is_422(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        attempt_id = _own_attempt(c)
        assert c.post(f"/attempts/{attempt_id}/survey", json={**FULL, "fun": 6}).status_code == 422
        assert c.post(f"/attempts/{attempt_id}/survey", json={**FULL, "fun": 0}).status_code == 422


def test_stranger_attempt_is_404(db_session, logged_in):
    from main import app
    with TestClient(app) as c:
        assert c.post(f"/attempts/{uuid.uuid4()}/survey", json=FULL).status_code == 404
