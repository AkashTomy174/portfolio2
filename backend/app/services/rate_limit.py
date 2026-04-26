import time
from hashlib import sha256


class RateLimiter:
  def __init__(self, max_requests: int, window_seconds: int) -> None:
    self.max_requests = max_requests
    self.window_seconds = window_seconds
    self._hits: dict[str, tuple[int, float]] = {}

  @staticmethod
  def ip_hash(ip: str) -> str:
    return sha256(ip.encode("utf-8")).hexdigest()[:16]

  def allow(self, ip: str) -> bool:
    now = time.time()
    key = self.ip_hash(ip)
    count, reset_at = self._hits.get(key, (0, now + self.window_seconds))

    if now >= reset_at:
      count = 0
      reset_at = now + self.window_seconds

    if count >= self.max_requests:
      return False

    self._hits[key] = (count + 1, reset_at)
    return True
