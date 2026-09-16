"""과잉 사용 방지 — 순수 규칙 (토큰 버킷·KST 하루·한도). I/O 없음."""

from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def kst_day_start(now: datetime) -> datetime:
    if now.tzinfo is None:
        raise ValueError("now must be tz-aware")
    local = now.astimezone(KST)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(timezone.utc)


class TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: float, prune_after: int = 10_000) -> None:
        self._capacity = capacity
        self._refill = refill_per_sec
        self._prune_after = prune_after
        self._state: dict[str, tuple[float, float]] = {}  # key -> (tokens, last)

    def take(self, key: str, now: float) -> tuple[bool, float]:
        tokens, last = self._state.get(key, (float(self._capacity), now))
        delta = max(0.0, now - last)
        tokens = min(self._capacity, tokens + delta * self._refill)
        if tokens >= 1.0:
            self._state[key] = (tokens - 1.0, now)
        else:
            self._state[key] = (tokens, now)

        # Pruning: remove fully refilled old entries if state exceeds threshold
        if len(self._state) > self._prune_after:
            cutoff = now - self._capacity / self._refill
            self._state = {k: v for k, v in self._state.items() if v[1] > cutoff}

        if tokens >= 1.0:
            return True, 0.0
        return False, (1.0 - tokens) / self._refill


def attempts_allowed(count_today: int, limit: int) -> bool:
    return count_today < limit
