import uuid
from datetime import datetime, timezone
from uuid import UUID

from apps.engine.app.dtos import event_log_dto as ev
from apps.engine.app.dtos.auth_dto import GoogleProfileDTO, SessionUserDTO
from apps.engine.domain.entities.guard_rules import attempts_allowed


class UserDailyLimit(Exception):
    pass


class DailyCapReached(Exception):
    pass


class SessionInteractor:
    def __init__(self, *, attempts, event_log, scenario, users,
                 user_daily_attempts: int, daily_attempt_cap: int) -> None:
        self._attempts = attempts
        self._events = event_log
        self._scenario = scenario
        self._users = users
        self._user_daily_attempts = user_daily_attempts
        self._daily_attempt_cap = daily_attempt_cap

    def _resolve_user_id(self, user: SessionUserDTO) -> UUID:
        existing = self._users.get_by_sub(user.sub)
        if existing is not None:
            return existing.id
        if user.sub == "dev":
            profile = GoogleProfileDTO(sub="dev", email="dev@local", name="dev")
        else:
            profile = GoogleProfileDTO(sub=user.sub, email=user.email, name=user.name, picture=user.picture)
        return self._users.upsert_from_google(profile).id

    def start(self, prior_attempt_id: UUID | None, user: SessionUserDTO, ip_hash: str) -> dict:
        user_id = self._resolve_user_id(user)
        now = datetime.now(timezone.utc)

        if not attempts_allowed(self._attempts.count_today_all(now), self._daily_attempt_cap):
            self._events.record(
                uuid.uuid4(),
                ev.GuardEvent(layer="daily_cap", reason="오늘 정원이 마감됐다", ip_hash=ip_hash, user_sub=user.sub),
            )
            raise DailyCapReached()

        if not attempts_allowed(self._attempts.count_today(user_id, now), self._user_daily_attempts):
            self._events.record(
                uuid.uuid4(),
                ev.GuardEvent(layer="user_daily", reason="오늘은 여기까지", ip_hash=ip_hash, user_sub=user.sub),
            )
            raise UserDailyLimit()

        prior = self._attempts.get(prior_attempt_id) if prior_attempt_id else None
        attempt = self._attempts.create(prior, user_id=user_id)

        # TOCTOU: 생성 직후(내 판을 포함해) 다시 세어, 한도를 넘어섰으면 방금 만든 판을 지운다.
        # 경계값(정확히 한도에 닿은 마지막 한 판)은 통과시켜야 하므로 ">"로 비교한다.
        if self._attempts.count_today_all(now) > self._daily_attempt_cap:
            self._attempts.delete(attempt)
            self._events.record(
                uuid.uuid4(),
                ev.GuardEvent(layer="daily_cap", reason="오늘 정원이 마감됐다", ip_hash=ip_hash, user_sub=user.sub),
            )
            raise DailyCapReached()

        if self._attempts.count_today(user_id, now) > self._user_daily_attempts:
            self._attempts.delete(attempt)
            self._events.record(
                uuid.uuid4(),
                ev.GuardEvent(layer="user_daily", reason="오늘은 여기까지", ip_hash=ip_hash, user_sub=user.sub),
            )
            raise UserDailyLimit()

        prior_cells = attempt.prior_cell_results
        self._events.record(
            attempt.id,
            ev.SessionStartEvent(
                session=str(attempt.id),
                attempt_n=attempt.attempt_n,
                prior_cell_results=ev.CellScores(**prior_cells) if prior_cells else None,
            ),
        )
        return {
            "attempt_id": str(attempt.id),
            "attempt_n": attempt.attempt_n,
            "entry_lines": self._scenario.entry_lines(),
            "prior_cell_results": prior_cells,
        }
