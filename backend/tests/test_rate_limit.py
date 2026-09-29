from app.core.rate_limit import LoginRateLimiter


def test_window_expiry(monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr("app.core.rate_limit.time.monotonic", lambda: clock[0])
    limiter = LoginRateLimiter(max_failures=2, window_seconds=60)
    limiter.record_failure("k")
    limiter.record_failure("k")
    assert limiter.retry_after("k") == 61
    clock[0] += 61
    assert limiter.retry_after("k") is None
