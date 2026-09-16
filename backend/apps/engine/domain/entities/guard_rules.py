"""과잉 사용 방지 — 순수 규칙 (토큰 버킷·KST 하루·한도). I/O 없음."""

from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def kst_day_start(now: datetime) -> datetime:
    local = now.astimezone(KST)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(timezone.utc)


class TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self._capacity = capacity
        self._refill = refill_per_sec
        self._state: dict[str, tuple[float, float]] = {}  # key -> (tokens, last)

    def take(self, key: str, now: float) -> tuple[bool, float]:
        tokens, last = self._state.get(key, (float(self._capacity), now))
        tokens = min(self._capacity, tokens + (now - last) * self._refill)
        if tokens >= 1.0:
            self._state[key] = (tokens - 1.0, now)
            return True, 0.0
        self._state[key] = (tokens, now)
        return False, (1.0 - tokens) / self._refill


def attempts_allowed(count_today: int, limit: int) -> bool:
    return count_today < limit
