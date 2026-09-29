"""Failed-login throttling (sliding window, in memory).

Only *failures* count, and a successful login clears the key, so a user who mistypes
once isn't punished. Keyed by (client IP, email) so one attacker can't lock a victim
out from everywhere, and one IP can't spray a single account.

Limitation (documented in NOTES.md): state is per process. With several API replicas
this should move to Redis (same interface: INCR + EXPIRE).
"""

import threading
import time
from collections import defaultdict, deque


class LoginRateLimiter:
    def __init__(self, max_failures: int = 5, window_seconds: float = 300.0) -> None:
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        q = self._failures[key]
        while q and now - q[0] > self.window:
            q.popleft()
        return q

    def retry_after(self, key: str) -> int | None:
        """Seconds until another attempt is allowed, or None if allowed now."""
        now = time.monotonic()
        with self._lock:
            q = self._prune(key, now)
            if len(q) < self.max_failures:
                return None
            return max(1, int(self.window - (now - q[0])) + 1)

    def record_failure(self, key: str) -> None:
        with self._lock:
            self._failures[key].append(time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._failures.clear()


login_limiter = LoginRateLimiter()
