"""SessionInteractor.start의 TOCTOU 재확인 — 생성 직후 다시 세어 한도를 넘겼으면 지운다."""

import uuid
from types import SimpleNamespace

import pytest

from apps.engine.app.dtos.auth_dto import SessionUserDTO
from apps.engine.app.use_cases.session_interactor import (
    DailyCapReached,
    SessionInteractor,
    UserDailyLimit,
)


class FakeAttempts:
    def __init__(self, counts_all, counts_user):
        self._counts_all = iter(counts_all)
        self._counts_user = iter(counts_user)
        self.created = []
        self.deleted = []

    def count_today_all(self, now):
        return next(self._counts_all)

    def count_today(self, user_id, now):
        return next(self._counts_user)

    def get(self, attempt_id):
        return None

    def create(self, prior, user_id=None):
        row = SimpleNamespace(id=uuid.uuid4(), attempt_n=1, prior_cell_results=None)
        self.created.append(row)
        return row

    def delete(self, attempt):
        self.deleted.append(attempt)


class FakeEvents:
    def __init__(self):
        self.records = []

    def record(self, session_id, event):
        self.records.append((session_id, event))


class FakeUsers:
    def get_by_sub(self, sub):
        return SimpleNamespace(id=uuid.uuid4())


def _interactor(attempts, *, daily_attempt_cap=1, user_daily_attempts=5):
    return SessionInteractor(
        attempts=attempts,
        event_log=FakeEvents(),
        scenario=SimpleNamespace(entry_lines=lambda: []),
        users=FakeUsers(),
        user_daily_attempts=user_daily_attempts,
        daily_attempt_cap=daily_attempt_cap,
    )


def _user():
    return SessionUserDTO(sub="u1", email="a@b", name="n")


def test_recheck_deletes_attempt_when_daily_cap_exceeded_after_create():
    # 정원 1: 만들기 전엔 0석 남아 통과하지만, 생성 직후 다시 세니(동시 요청 포함) 2 — 한도를 넘겼다.
    attempts = FakeAttempts(counts_all=[0, 2], counts_user=[0])
    interactor = _interactor(attempts, daily_attempt_cap=1)
    with pytest.raises(DailyCapReached):
        interactor.start(None, _user(), "iphash")
    assert len(attempts.created) == 1
    assert attempts.deleted == attempts.created


def test_recheck_deletes_attempt_when_user_daily_limit_exceeded_after_create():
    attempts = FakeAttempts(counts_all=[0, 1], counts_user=[0, 5])
    interactor = _interactor(attempts, daily_attempt_cap=100, user_daily_attempts=1)
    with pytest.raises(UserDailyLimit):
        interactor.start(None, _user(), "iphash")
    assert len(attempts.created) == 1
    assert attempts.deleted == attempts.created


def test_recheck_allows_the_exact_boundary_attempt():
    # 정원 1: 만들기 전 0석, 생성 직후 정확히 1 — 한도에 닿았을 뿐 넘지 않았으므로 지우지 않는다.
    attempts = FakeAttempts(counts_all=[0, 1], counts_user=[0, 1])
    interactor = _interactor(attempts, daily_attempt_cap=1, user_daily_attempts=1)
    result = interactor.start(None, _user(), "iphash")
    assert result["attempt_id"] == str(attempts.created[0].id)
    assert attempts.deleted == []
