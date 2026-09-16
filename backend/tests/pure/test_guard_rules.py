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


def test_kst_day_start_rejects_naive_datetime():
    naive_now = datetime(2026, 9, 16, 14, 59)
    try:
        kst_day_start(naive_now)
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "tz-aware" in str(e)


def test_token_bucket_prunes_old_entries():
    bucket = TokenBucket(capacity=1, refill_per_sec=1.0, prune_after=10_000)
    # Insert 10_001 keys at now=0.0
    for i in range(10_001):
        bucket.take(f"key_{i}", now=0.0)
    assert len(bucket._state) == 10_001
    # Call take at now=100.0 (cutoff = 100 - 1/1.0 = 99.0)
    # All entries with last <= 99.0 should be pruned, only "key_x" at now=100.0 remains
    bucket.take("x", now=100.0)
    # After pruning, should have at most 2 entries (one from before, one new)
    assert len(bucket._state) <= 2


def test_token_bucket_clamps_backward_time():
    bucket = TokenBucket(capacity=2, refill_per_sec=1.0)
    # At now=10.0, take first token
    ok1, wait1 = bucket.take("k", now=10.0)
    assert ok1 is True
    # At now=5.0 (backward), should behave as if delta=0 (same as calling at 10.0 again)
    ok2, wait2 = bucket.take("k", now=5.0)
    # Should allow taking the second token (same as calling at 10.0 again)
    assert ok2 is True and wait2 == 0.0
    # Third call at backward time should fail (capacity exhausted)
    ok3, wait3 = bucket.take("k", now=5.0)
    assert ok3 is False and 0.9 <= wait3 <= 1.0
