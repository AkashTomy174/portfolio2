"""
app/services/memory.py

Conversation memory for the AI Akash chatbot.

Supports follow-up questions by maintaining per-session message history.

Design
------
- Sessions are keyed by a client-supplied session_id (opaque string).
- Each session stores a list of {"role": "user"|"assistant", "content": str}
  dicts, capped at max_history turns (user+assistant pairs).
- Sessions expire after ttl_seconds of inactivity (last-access time).
- Two backends:
    InMemorySessionStore  — default, zero dependencies, process-local.
    RedisSessionStore     — optional, requires redis package, shared across
                            workers.  Falls back to in-memory if Redis is
                            unavailable.

Usage in main.py
----------------
    history = memory.get(session_id)
    # ... generate answer ...
    memory.append(session_id, "user", payload.message)
    memory.append(session_id, "assistant", answer_text)

The LLM service receives the history list and prepends it to the prompt so
Gemini has context for follow-up questions.
"""
from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger("ai-akash")

Message = dict[str, str]   # {"role": "user"|"assistant", "content": str}


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class SessionStore(ABC):
    @abstractmethod
    def get(self, session_id: str) -> list[Message]:
        """Return the message history for a session (empty list if unknown)."""

    @abstractmethod
    def append(self, session_id: str, role: str, content: str) -> None:
        """Append one message to a session, pruning if over max_history."""

    @abstractmethod
    def delete(self, session_id: str) -> None:
        """Remove a session."""

    @abstractmethod
    def session_count(self) -> int:
        """Return the number of active sessions (for health/metrics)."""


# ---------------------------------------------------------------------------
# In-memory backend
# ---------------------------------------------------------------------------

class _SessionEntry:
    __slots__ = ("messages", "last_access")

    def __init__(self) -> None:
        self.messages: list[Message] = []
        self.last_access: float = time.monotonic()


class InMemorySessionStore(SessionStore):
    """
    Thread-safe-enough for CPython's GIL.

    Expired sessions are pruned lazily on every get/append call.
    A hard cap (_MAX_SESSIONS) prevents unbounded memory growth if many
    unique session IDs are generated.
    """

    _MAX_SESSIONS = 1_000

    def __init__(self, max_history: int, ttl_seconds: int) -> None:
        self.max_history = max_history      # max user+assistant turns to keep
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, _SessionEntry] = {}

    def get(self, session_id: str) -> list[Message]:
        self._evict_expired()
        entry = self._sessions.get(session_id)
        if entry is None:
            return []
        entry.last_access = time.monotonic()
        return list(entry.messages)

    def append(self, session_id: str, role: str, content: str) -> None:
        self._evict_expired()
        if session_id not in self._sessions:
            if len(self._sessions) >= self._MAX_SESSIONS:
                self._evict_oldest()
            self._sessions[session_id] = _SessionEntry()
        entry = self._sessions[session_id]
        entry.messages.append({"role": role, "content": content})
        # Keep only the last max_history * 2 messages (each turn = 2 messages)
        cap = self.max_history * 2
        if len(entry.messages) > cap:
            entry.messages = entry.messages[-cap:]
        entry.last_access = time.monotonic()

    def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def session_count(self) -> int:
        return len(self._sessions)

    def _evict_expired(self) -> None:
        now = time.monotonic()
        expired = [
            sid for sid, entry in self._sessions.items()
            if now - entry.last_access > self.ttl_seconds
        ]
        for sid in expired:
            del self._sessions[sid]

    def _evict_oldest(self) -> None:
        if not self._sessions:
            return
        oldest = min(self._sessions, key=lambda sid: self._sessions[sid].last_access)
        del self._sessions[oldest]


# ---------------------------------------------------------------------------
# Redis backend
# ---------------------------------------------------------------------------

class RedisSessionStore(SessionStore):
    """
    Redis-backed session store.

    Each session is stored as a JSON string under key "session:{session_id}".
    TTL is set on every write so Redis handles expiry natively.

    Falls back gracefully: if the Redis connection fails on any operation,
    the error is logged and an empty result is returned (the request still
    succeeds, just without history context).
    """

    _LUA_APPEND = """
        local raw = redis.call('GET', KEYS[1])
        local msgs = {}
        if raw then msgs = cjson.decode(raw) end
        local msg = cjson.decode(ARGV[1])
        table.insert(msgs, msg)
        local cap = tonumber(ARGV[2])
        while #msgs > cap do table.remove(msgs, 1) end
        redis.call('SETEX', KEYS[1], tonumber(ARGV[3]), cjson.encode(msgs))
        return #msgs
        """

    def __init__(self, redis_url: str, max_history: int, ttl_seconds: int) -> None:
        self.max_history = max_history
        self.ttl_seconds = ttl_seconds
        self._client: Any = None
        try:
            import redis as redis_lib
            self._client = redis_lib.from_url(redis_url, decode_responses=True)
            self._client.ping()
            logger.info("RedisSessionStore connected. url=%s", redis_url)
        except Exception as exc:
            logger.warning(
                "RedisSessionStore: could not connect to Redis (%s). "
                "Session memory will be unavailable.",
                exc,
            )
            self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def get(self, session_id: str) -> list[Message]:
        if not self._client:
            return []
        try:
            raw = self._client.get(self._key(session_id))
            if raw is None:
                return []
            return json.loads(raw)
        except Exception as exc:
            logger.warning("RedisSessionStore.get failed: %s", exc)
            return []

    def append(self, session_id: str, role: str, content: str) -> None:
        if not self._client:
            return
        # Atomic read-modify-write via Lua script to prevent race conditions
        # when two requests for the same session_id arrive concurrently.
        try:
            cap = self.max_history * 2
            self._client.eval(
                self._LUA_APPEND,
                1,
                self._key(session_id),
                json.dumps({"role": role, "content": content}, ensure_ascii=False),
                cap,
                self.ttl_seconds,
            )
        except Exception as exc:
            logger.warning("RedisSessionStore.append failed: %s", exc)

    def delete(self, session_id: str) -> None:
        if not self._client:
            return
        try:
            self._client.delete(self._key(session_id))
        except Exception as exc:
            logger.warning("RedisSessionStore.delete failed: %s", exc)

    def session_count(self) -> int:
        if not self._client:
            return 0
        try:
            count = 0
            for _ in self._client.scan_iter("session:*", count=100):
                count += 1
            return count
        except Exception:
            logger.warning("RedisSessionStore.session_count failed.", exc_info=True)
            return 0


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_session_store(
    redis_url: str | None,
    max_history: int,
    ttl_seconds: int,
) -> SessionStore:
    """
    Return a RedisSessionStore if redis_url is set and Redis is reachable,
    otherwise return an InMemorySessionStore.
    """
    if redis_url:
        store = RedisSessionStore(redis_url, max_history, ttl_seconds)
        if store.available:
            return store
        logger.warning("Falling back to InMemorySessionStore.")
    return InMemorySessionStore(max_history, ttl_seconds)
