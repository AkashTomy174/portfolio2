"""
tests/test_observability_memory.py

Tests for:
  - MetricsCollector: counters, rates, percentiles, Prometheus output
  - RequestRecord: emit produces valid JSON
  - InMemorySessionStore: append, get, TTL expiry, max_history pruning, cap
  - RedisSessionStore: graceful fallback when Redis is unavailable
  - build_session_store: returns InMemorySessionStore when no Redis URL
"""
from __future__ import annotations

import json
import time
import unittest
from io import StringIO
from unittest.mock import patch

from app.services.observability import (
    MetricsCollector,
    RequestRecord,
    hash_ip,
    new_request_id,
    utc_now_iso,
)
from app.services.memory import (
    InMemorySessionStore,
    RedisSessionStore,
    build_session_store,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _record(**kwargs) -> RequestRecord:
    defaults = dict(
        request_id="abc123",
        timestamp=utc_now_iso(),
        ip_hash=hash_ip("1.2.3.4", "test-salt"),
        session_id=None,
        original_query="hello",
        normalized_query="hello",
    )
    defaults.update(kwargs)
    return RequestRecord(**defaults)


# ---------------------------------------------------------------------------
# MetricsCollector
# ---------------------------------------------------------------------------

class TestMetricsCollector(unittest.TestCase):

    def setUp(self):
        self.m = MetricsCollector()

    def test_initial_state(self):
        self.assertEqual(self.m.total_requests, 0)
        self.assertIsNone(self.m.avg_latency_ms)
        self.assertIsNone(self.m.p95_latency_ms)
        self.assertEqual(self.m.cache_hit_ratio, 0.0)

    def test_rate_limited_increments_counter(self):
        r = _record(status="rate_limited")
        self.m.record_request(r)
        self.assertEqual(self.m.total_requests, 1)
        self.assertEqual(self.m.rate_limited, 1)
        self.assertEqual(self.m.cache_hits, 0)

    def test_cache_hit_increments_cache_hits(self):
        r = _record(cache_hit=True, total_latency_ms=50.0)
        self.m.record_request(r)
        self.assertEqual(self.m.cache_hits, 1)
        self.assertEqual(self.m.shortcut_hits, 0)
        self.assertEqual(self.m.rag_hits, 0)

    def test_shortcut_hit_increments_shortcut_hits(self):
        r = _record(intent_route="greeting", total_latency_ms=1.0)
        self.m.record_request(r)
        self.assertEqual(self.m.shortcut_hits, 1)
        self.assertEqual(self.m.rag_hits, 0)

    def test_rag_hit_increments_rag_hits(self):
        r = _record(total_latency_ms=300.0)
        self.m.record_request(r)
        self.assertEqual(self.m.rag_hits, 1)

    def test_avg_latency(self):
        for ms in [100.0, 200.0, 300.0]:
            self.m.record_request(_record(total_latency_ms=ms))
        self.assertAlmostEqual(self.m.avg_latency_ms, 200.0)

    def test_p95_latency(self):
        for ms in range(1, 101):
            self.m.record_request(_record(total_latency_ms=float(ms)))
        p95 = self.m.p95_latency_ms
        self.assertIsNotNone(p95)
        self.assertGreaterEqual(p95, 94.0)
        self.assertLessEqual(p95, 96.0)

    def test_cache_hit_ratio(self):
        self.m.record_request(_record(cache_hit=True, total_latency_ms=10.0))
        self.m.record_request(_record(total_latency_ms=200.0))
        self.assertAlmostEqual(self.m.cache_hit_ratio, 0.5)

    def test_shortcut_hit_rate(self):
        self.m.record_request(_record(intent_route="greeting", total_latency_ms=1.0))
        self.m.record_request(_record(total_latency_ms=200.0))
        self.assertAlmostEqual(self.m.shortcut_hit_rate, 0.5)

    def test_failure_counters(self):
        self.m.record_llm_failure()
        self.m.record_llm_failure()
        self.m.record_embedding_failure()
        self.m.record_tts_failure()
        self.assertEqual(self.m.llm_failures, 2)
        self.assertEqual(self.m.embedding_failures, 1)
        self.assertEqual(self.m.tts_failures, 1)

    def test_snapshot_keys(self):
        snap = self.m.snapshot()
        required = {
            "total_requests", "shortcut_hits", "rag_hits", "cache_hits",
            "rate_limited", "llm_failures", "embedding_failures", "tts_failures",
            "errors", "shortcut_hit_rate", "rag_hit_rate", "cache_hit_ratio",
            "avg_latency_ms", "p95_latency_ms", "p99_latency_ms",
            "avg_retrieved_chunks", "avg_prompt_tokens",
        }
        self.assertTrue(required.issubset(snap.keys()))

    def test_prometheus_text_format(self):
        self.m.record_request(_record(total_latency_ms=100.0))
        text = self.m.prometheus_text()
        self.assertIn("# HELP ai_akash_requests_total", text)
        self.assertIn("# TYPE ai_akash_requests_total counter", text)
        self.assertIn("ai_akash_requests_total 1", text)
        self.assertIn("ai_akash_p95_latency_ms", text)
        # Must end with newline
        self.assertTrue(text.endswith("\n"))

    def test_prometheus_text_valid_lines(self):
        text = self.m.prometheus_text()
        for line in text.strip().splitlines():
            # Every non-comment line must be "name value"
            if not line.startswith("#"):
                parts = line.split()
                self.assertEqual(len(parts), 2, f"Bad Prometheus line: {line!r}")

    def test_avg_retrieved_chunks(self):
        r1 = _record(retrieved_chunks=3, total_latency_ms=100.0)
        r2 = _record(retrieved_chunks=5, total_latency_ms=100.0)
        self.m.record_request(r1)
        self.m.record_request(r2)
        self.assertAlmostEqual(self.m.avg_retrieved_chunks, 4.0)


# ---------------------------------------------------------------------------
# RequestRecord
# ---------------------------------------------------------------------------

class TestRequestRecord(unittest.TestCase):

    def test_emit_writes_valid_json(self):
        import logging
        record = _record(
            intent_route="greeting",
            matched_alias="hello",
            similarity_score=1.0,
            match_type="exact",
            total_latency_ms=2.5,
        )
        # Capture log output
        buf = StringIO()
        handler = logging.StreamHandler(buf)
        obs_logger = logging.getLogger("ai-akash.obs")
        obs_logger.addHandler(handler)
        obs_logger.setLevel(logging.INFO)
        try:
            record.emit()
        finally:
            obs_logger.removeHandler(handler)

        output = buf.getvalue().strip()
        self.assertTrue(output, "No log output produced")
        # The message part should be valid JSON
        # The formatter wraps it: find the JSON payload
        json_start = output.find("{")
        self.assertGreater(json_start, -1)
        payload = json.loads(output[json_start:])
        self.assertEqual(payload["request_id"], "abc123")
        self.assertEqual(payload["intent_route"], "greeting")

    def test_hash_ip_is_16_chars(self):
        h = hash_ip("192.168.1.1", "test-salt")
        self.assertEqual(len(h), 16)
        self.assertNotEqual(h, "192.168.1.1")

    def test_new_request_id_unique(self):
        ids = {new_request_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_utc_now_iso_format(self):
        ts = utc_now_iso()
        from datetime import datetime
        dt = datetime.fromisoformat(ts)
        self.assertIsNotNone(dt.tzinfo)


# ---------------------------------------------------------------------------
# InMemorySessionStore
# ---------------------------------------------------------------------------

class TestInMemorySessionStore(unittest.TestCase):

    def setUp(self):
        self.store = InMemorySessionStore(max_history=3, ttl_seconds=60)

    def test_get_unknown_session_returns_empty(self):
        self.assertEqual(self.store.get("nonexistent"), [])

    def test_append_and_get(self):
        self.store.append("s1", "user", "hello")
        self.store.append("s1", "assistant", "hi there")
        history = self.store.get("s1")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0], {"role": "user", "content": "hello"})
        self.assertEqual(history[1], {"role": "assistant", "content": "hi there"})

    def test_max_history_pruning(self):
        # max_history=3 means 6 messages max (3 user + 3 assistant)
        for i in range(5):
            self.store.append("s1", "user", f"q{i}")
            self.store.append("s1", "assistant", f"a{i}")
        history = self.store.get("s1")
        self.assertLessEqual(len(history), 6)
        # Most recent messages should be kept
        self.assertEqual(history[-1]["content"], "a4")

    def test_delete_removes_session(self):
        self.store.append("s1", "user", "hello")
        self.store.delete("s1")
        self.assertEqual(self.store.get("s1"), [])

    def test_session_count(self):
        self.store.append("s1", "user", "a")
        self.store.append("s2", "user", "b")
        self.assertEqual(self.store.session_count(), 2)

    def test_ttl_expiry(self):
        store = InMemorySessionStore(max_history=3, ttl_seconds=0)
        store.append("s1", "user", "hello")
        # Force last_access to be in the past
        store._sessions["s1"].last_access = time.monotonic() - 1
        # Next get should evict it
        result = store.get("s1")
        self.assertEqual(result, [])

    def test_get_returns_copy(self):
        """Mutating the returned list must not affect the stored history."""
        self.store.append("s1", "user", "hello")
        history = self.store.get("s1")
        history.append({"role": "user", "content": "injected"})
        self.assertEqual(len(self.store.get("s1")), 1)

    def test_max_sessions_cap(self):
        store = InMemorySessionStore(max_history=2, ttl_seconds=3600)
        store._MAX_SESSIONS = 5
        for i in range(6):
            store.append(f"session_{i}", "user", "msg")
        self.assertLessEqual(store.session_count(), 5)


# ---------------------------------------------------------------------------
# RedisSessionStore — fallback behavior
# ---------------------------------------------------------------------------

class TestRedisSessionStoreFallback(unittest.TestCase):
    """
    RedisSessionStore must degrade gracefully when Redis is unavailable.
    All operations should return safe defaults and not raise.
    """

    def setUp(self):
        # Use an invalid URL so the connection always fails
        self.store = RedisSessionStore(
            redis_url="redis://localhost:19999",
            max_history=3,
            ttl_seconds=60,
        )

    def test_not_available(self):
        self.assertFalse(self.store.available)

    def test_get_returns_empty(self):
        self.assertEqual(self.store.get("s1"), [])

    def test_append_does_not_raise(self):
        self.store.append("s1", "user", "hello")  # must not raise

    def test_delete_does_not_raise(self):
        self.store.delete("s1")  # must not raise

    def test_session_count_returns_zero(self):
        self.assertEqual(self.store.session_count(), 0)


# ---------------------------------------------------------------------------
# build_session_store
# ---------------------------------------------------------------------------

class TestBuildSessionStore(unittest.TestCase):

    def test_no_redis_url_returns_in_memory(self):
        store = build_session_store(redis_url=None, max_history=4, ttl_seconds=600)
        self.assertIsInstance(store, InMemorySessionStore)

    def test_empty_redis_url_returns_in_memory(self):
        store = build_session_store(redis_url="", max_history=4, ttl_seconds=600)
        self.assertIsInstance(store, InMemorySessionStore)

    def test_unreachable_redis_falls_back_to_in_memory(self):
        store = build_session_store(
            redis_url="redis://localhost:19999",
            max_history=4,
            ttl_seconds=600,
        )
        self.assertIsInstance(store, InMemorySessionStore)


if __name__ == "__main__":
    unittest.main(verbosity=2)
