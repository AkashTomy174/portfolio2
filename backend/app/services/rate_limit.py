from __future__ import annotations

import time

from app.services.observability import hash_ip

# NOTE: Rate limiting and login-attempt tracking are per-process.
# If deployed with multiple Gunicorn/Uvicorn workers, each worker enforces
# limits independently, effectively multiplying the allowed request/attempt
# ceiling by worker count. Single-worker deployment is required for these
# limits to be authoritative, or migrate to a Redis-backed counter (see
# build_session_store in memory.py for the pattern) before scaling beyond
# a single worker.


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int, salt: str = "") -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._salt = salt
        self._hits: dict[str, tuple[int, float]] = {}
 
    def allow(self, ip: str) -> bool:
        now = time.time()
        key = hash_ip(ip, self._salt)
        count, reset_at = self._hits.get(key, (0, now + self.window_seconds))

        if now >= reset_at:
            count = 0
            reset_at = now + self.window_seconds

        if count >= self.max_requests:
            return False

        self._hits[key] = (count + 1, reset_at)

        # Prune expired entries when the dict gets large to prevent unbounded
        # growth under bot traffic or IP scans.
        if len(self._hits) > 10_000:
            self._hits = {
                k: v for k, v in self._hits.items() if v[1] > now
            }

        return True
