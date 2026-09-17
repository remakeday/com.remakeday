"""판 소유자 확인 (F26) — 경로의 판 하위 ID를 판으로 해석해 요청 사용자의 판인지 확인한다.

주인 비교는 세션 생성(SessionInteractor)과 같은 기준이다: 세션 sub → users.id → attempts.user_id.
"""

import uuid
from collections.abc import Mapping

from apps.engine.app.dtos.auth_dto import SessionUserDTO


class AttemptNotFound(Exception):
    """판이 없거나 남의 판 — 존재 여부를 흘리지 않도록 둘을 구분하지 않는다."""


def _parse(raw: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(raw))
    except ValueError as e:
        raise AttemptNotFound() from e


class AttemptAccessInteractor:
    def __init__(self, *, attempts, loops, nights, users) -> None:
        self._attempts = attempts
        self._loops = loops
        self._nights = nights
        self._users = users
        # 경로 ID 이름 → 그 ID가 속한 판 ID (없으면 None)
        self._resolvers = {
            "attempt_id": lambda attempt_id: attempt_id,
            "loop_id": self._attempt_of_loop,
            "night_id": self._attempt_of_night,
        }

    def ensure_owner(self, path_ids: Mapping[str, str], user: SessionUserDTO) -> None:
        targets = [(self._resolvers[name], raw) for name, raw in path_ids.items() if name in self._resolvers]
        if not targets:
            raise AttemptNotFound()
        owner = self._users.get_by_sub(user.sub)
        if owner is None:
            raise AttemptNotFound()
        for resolve, raw in targets:
            attempt_id = resolve(_parse(raw))
            if attempt_id is None or self._attempts.get_owned(attempt_id, owner.id) is None:
                raise AttemptNotFound()

    def _attempt_of_loop(self, loop_id: uuid.UUID) -> uuid.UUID | None:
        loop = self._loops.get(loop_id)
        return loop.attempt_id if loop is not None else None

    def _attempt_of_night(self, night_id: uuid.UUID) -> uuid.UUID | None:
        night = self._nights.get(night_id)
        return self._attempt_of_loop(night.loop_id) if night is not None else None
