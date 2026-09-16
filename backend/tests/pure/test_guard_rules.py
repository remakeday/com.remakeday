from datetime import datetime, timezone, timedelta
from apps.engine.domain.entities.guard_rules import kst_day_start, TokenBucket, attempts_allowed


def test_kst_day_start_rolls_at_kst_midnight():
    # 2026-09-16 14:59 UTC = 09-16 23:59 KST → 09-16 00:00 KST = 09-15 15:00 UTC
    now = datetime(2026, 9, 16, 14, 59, tzinfo=timezone.utc)
    assert kst_day_start(now) == datetime(2026, 9, 15, 15, 0, tzinfo=timezone.utc)
    # 15:00 UTC = 09-17 00:00 KST → 새 날
    assert kst_day_start(now + timedelta(minutes=1)) == datetime(2026, 9, 16, 15, 0, tzinfo=timezone.utc)


def test_token_bucket_allows_capacity_then_blocks_and_refills():
    bucket = TokenBucket(capacity=2, refill_per_sec=1.0)
    assert bucket.take("ip", now=0.0) == (True, 0.0)
    assert bucket.take("ip", now=0.0) == (True, 0.0)
    ok, wait = bucket.take("ip", now=0.0)
    assert ok is False and 0.9 <= wait <= 1.0
    assert bucket.take("ip", now=1.0)[0] is True
    assert bucket.take("other", now=1.0)[0] is True  # 키별 독립


def test_attempts_allowed():
    assert attempts_allowed(4, 5) and not attempts_allowed(5, 5)
