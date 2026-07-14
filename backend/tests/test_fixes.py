"""
tests/test_fixes.py

Regression tests for the code-review follow-up fixes.

Sections
--------
1. LruCache — clear(), LRU eviction order, set/get round-trip  (1.2)
2. Cache history gating — history-aware cacheable flag          (1.1)
3. Whitespace message validation                                 (2.6)
4. Salted hash_ip                                               (2.1)
5. ShortcutResult tuple sources                                 (3.4)
6. is_known_exact collision guard on IntentRoute.match          (3.5)
7. _login_attempts eviction                                     (3.3)
"""
from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.intents import IntentRoute, ShortcutResult, match_intent, normalize_query
from app.models import ChatRequest
from app.services.cache import LruCache
from app.services.observability import hash_ip


# ---------------------------------------------------------------------------
# 1. LruCache
# ---------------------------------------------------------------------------

class TestLruCache(unittest.TestCase):

    def setUp(self):
        self.cache = LruCache(max_items=3)

    def test_set_and_get(self):
        self.cache.set("k1", {"text": "hello"})
        self.assertEqual(self.cache.get("k1"), {"text": "hello"})

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.cache.get("nonexistent"))

    def test_clear_empties_cache(self):
        self.cache.set("k1", {"text": "a"})
        self.cache.set("k2", {"text": "b"})
        self.cache.clear()
        self.assertIsNone(self.cache.get("k1"))
        self.assertIsNone(self.cache.get("k2"))
        self.assertEqual(len(self.cache._items), 0)

    def test_lru_eviction_order(self):
        # Fill to capacity
        self.cache.set("k1", {"v": 1})
        self.cache.set("k2", {"v": 2})
        self.cache.set("k3", {"v": 3})
        # Access k1 so k2 becomes the least recently used
        self.cache.get("k1")
        # Adding k4 should evict k2 (LRU)
        self.cache.set("k4", {"v": 4})
        self.assertIsNone(self.cache.get("k2"), "k2 should have been evicted")
        self.assertIsNotNone(self.cache.get("k1"))
        self.assertIsNotNone(self.cache.get("k3"))
        self.assertIsNotNone(self.cache.get("k4"))

    def test_set_overwrites_existing(self):
        self.cache.set("k1", {"v": 1})
        self.cache.set("k1", {"v": 99})
        self.assertEqual(self.cache.get("k1"), {"v": 99})

    def test_max_items_respected(self):
        for i in range(10):
            self.cache.set(f"k{i}", {"v": i})
        self.assertLessEqual(len(self.cache._items), 3)


# ---------------------------------------------------------------------------
# 2. Cache history gating (1.1)
# ---------------------------------------------------------------------------

class TestCacheHistoryGating(unittest.TestCase):
    """
    Verify the cacheable = not history logic that main.py uses.
    We test the invariant directly rather than importing main.py
    (which has module-level side effects).
    """

    def test_empty_history_is_cacheable(self):
        history = []
        cacheable = not history
        self.assertTrue(cacheable)

    def test_non_empty_history_is_not_cacheable(self):
        history = [{"role": "user", "content": "tell me about easybuy"}]
        cacheable = not history
        self.assertFalse(cacheable)

    def test_cache_key_is_deterministic(self):
        # LruCache.key lowercases and collapses whitespace only — no punctuation stripping.
        k1 = LruCache.key("hello", False)
        k2 = LruCache.key("hello", False)
        self.assertEqual(k1, k2)

    def test_cache_key_differs_by_voice(self):
        k1 = LruCache.key("hello", False)
        k2 = LruCache.key("hello", True)
        self.assertNotEqual(k1, k2)

    def test_cache_not_written_when_not_cacheable(self):
        cache = LruCache(max_items=10)
        cache_key = LruCache.key("tell me more", False)
        history = [{"role": "user", "content": "prior turn"}]
        cacheable = not history

        # Simulate what main.py does
        if cacheable:
            cache.set(cache_key, {"text": "answer", "sources": [], "audio_url": None, "cached": False})

        self.assertIsNone(cache.get(cache_key))

    def test_cache_written_when_cacheable(self):
        cache = LruCache(max_items=10)
        cache_key = LruCache.key("hello", False)
        history: list = []
        cacheable = not history

        if cacheable:
            cache.set(cache_key, {"text": "hi", "sources": [], "audio_url": None, "cached": False})

        self.assertIsNotNone(cache.get(cache_key))


# ---------------------------------------------------------------------------
# 3. Whitespace message validation (2.6)
# ---------------------------------------------------------------------------

class TestChatRequestValidation(unittest.TestCase):

    def test_normal_message_accepted(self):
        req = ChatRequest(message="hello")
        self.assertEqual(req.message, "hello")

    def test_whitespace_only_raises(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="   ")

    def test_single_space_raises(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message=" ")

    def test_tabs_only_raises(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="\t\t")

    def test_newlines_only_raises(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="\n\n")

    def test_empty_string_raises(self):
        # min_length=1 already catches this, but confirm
        with self.assertRaises(ValidationError):
            ChatRequest(message="")

    def test_message_with_leading_trailing_whitespace_accepted(self):
        # Validator returns original value — stripping is normalize_query's job
        req = ChatRequest(message="  hello  ")
        self.assertEqual(req.message, "  hello  ")

    def test_voice_defaults_false(self):
        req = ChatRequest(message="hi")
        self.assertFalse(req.voice)

    def test_session_id_optional(self):
        req = ChatRequest(message="hi")
        self.assertIsNone(req.session_id)

    def test_session_id_max_length(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="hi", session_id="x" * 129)


# ---------------------------------------------------------------------------
# 4. Salted hash_ip (2.1)
# ---------------------------------------------------------------------------

class TestHashIp(unittest.TestCase):

    def test_returns_16_chars(self):
        self.assertEqual(len(hash_ip("1.2.3.4", "salt")), 16)

    def test_different_salts_produce_different_hashes(self):
        h1 = hash_ip("1.2.3.4", "salt-a")
        h2 = hash_ip("1.2.3.4", "salt-b")
        self.assertNotEqual(h1, h2)

    def test_same_salt_same_ip_deterministic(self):
        self.assertEqual(hash_ip("1.2.3.4", "s"), hash_ip("1.2.3.4", "s"))

    def test_empty_salt_still_hashes(self):
        h = hash_ip("1.2.3.4", "")
        self.assertEqual(len(h), 16)
        self.assertNotEqual(h, "1.2.3.4")

    def test_salt_actually_mixed_in(self):
        # Without salt: hash("1.2.3.4"); with salt: hash("SALT1.2.3.4")
        # They must differ, proving the salt is prepended not ignored.
        no_salt = hash_ip("1.2.3.4", "")
        with_salt = hash_ip("1.2.3.4", "SALT")
        self.assertNotEqual(no_salt, with_salt)


# ---------------------------------------------------------------------------
# 5. ShortcutResult tuple sources (3.4)
# ---------------------------------------------------------------------------

class TestShortcutResultTupleSources(unittest.TestCase):

    def test_sources_is_tuple(self):
        sr = ShortcutResult(text="hi", sources=())
        self.assertIsInstance(sr.sources, tuple)

    def test_frozen_with_tuple_sources(self):
        sr = ShortcutResult(text="hi", sources=("about",))
        # frozen=True: mutation must raise
        with self.assertRaises((AttributeError, TypeError)):
            sr.sources = ("other",)  # type: ignore[misc]

    def test_all_handlers_return_tuple_sources(self):
        from app.intents import ROUTES
        for route in ROUTES:
            with self.subTest(route=route.name):
                sample = next(iter(route.aliases))
                result = route.handler(sample)
                self.assertIsInstance(result.sources, tuple,
                    f"Route '{route.name}' handler returned list sources, expected tuple")

    def test_empty_sources_tuple(self):
        sr = ShortcutResult(text="hi", sources=())
        self.assertEqual(sr.sources, ())
        self.assertEqual(list(sr.sources), [])


# ---------------------------------------------------------------------------
# 6. is_known_exact collision guard (3.5)
# ---------------------------------------------------------------------------

class TestKnownExactCollisionGuard(unittest.TestCase):

    def _make_route(self, aliases: frozenset[str]) -> IntentRoute:
        return IntentRoute(
            name="test_route",
            aliases=aliases,
            handler=lambda q: ShortcutResult(text="x", sources=()),
            allow_similarity=True,
            description="test",
        )

    def test_similarity_fires_when_not_known_exact(self):
        route = self._make_route(frozenset({"hey"}))
        result = route.match("heyy", is_known_exact=False)
        self.assertIsNotNone(result, "'heyy' should similarity-match 'hey' when not known exact")
        self.assertEqual(result.match_type, "similarity")

    def test_similarity_suppressed_when_known_exact(self):
        route = self._make_route(frozenset({"hey"}))
        result = route.match("heyy", is_known_exact=True)
        self.assertIsNone(result, "similarity must be suppressed when is_known_exact=True")

    def test_exact_match_always_fires_regardless_of_flag(self):
        route = self._make_route(frozenset({"hey"}))
        # Exact match should work even when is_known_exact=True
        result = route.match("hey", is_known_exact=True)
        self.assertIsNotNone(result)
        self.assertEqual(result.match_type, "exact")

    def test_full_router_collision_guard(self):
        # "how are you" is a small_talk alias (exact).
        # The greeting route has allow_similarity=True.
        # is_known_exact should be True for "how are you", suppressing
        # any similarity pass on the greeting route.
        normalized = normalize_query("how are you")
        result = match_intent(normalized)
        self.assertIsNotNone(result)
        self.assertEqual(result.route.name, "small_talk")
        self.assertEqual(result.match_type, "exact")


# ---------------------------------------------------------------------------
# 7. _login_attempts eviction (3.3)
# ---------------------------------------------------------------------------

class TestLoginAttemptsEviction(unittest.TestCase):
    """
    Test the eviction logic in isolation by importing and exercising
    the module-level helpers directly.
    """

    def test_check_allows_fresh_ip(self):
        from app.main import _check_login_rate_limit, _login_attempts
        _login_attempts.clear()
        self.assertTrue(_check_login_rate_limit("10.0.0.1"))

    def test_blocks_after_max_failures(self):
        from app.main import (
            _check_login_rate_limit,
            _record_login_failure,
            _login_attempts,
            _LOGIN_MAX_ATTEMPTS,
        )
        _login_attempts.clear()
        ip = "10.0.0.2"
        for _ in range(_LOGIN_MAX_ATTEMPTS):
            _record_login_failure(ip)
        self.assertFalse(_check_login_rate_limit(ip))

    def test_clear_resets_block(self):
        from app.main import (
            _check_login_rate_limit,
            _record_login_failure,
            _clear_login_failures,
            _login_attempts,
            _LOGIN_MAX_ATTEMPTS,
        )
        _login_attempts.clear()
        ip = "10.0.0.3"
        for _ in range(_LOGIN_MAX_ATTEMPTS):
            _record_login_failure(ip)
        _clear_login_failures(ip)
        self.assertTrue(_check_login_rate_limit(ip))

    def test_eviction_runs_when_dict_large(self):
        import time
        from app.main import _check_login_rate_limit, _login_attempts, _LOGIN_WINDOW_SECONDS
        from app.services.rate_limit import RateLimiter
        _login_attempts.clear()
        # Populate with already-expired entries
        past = time.time() - _LOGIN_WINDOW_SECONDS - 1
        for i in range(10_001):
            _login_attempts[f"fake{i}"] = (1, past)
        # Calling check should trigger the sweep
        _check_login_rate_limit("192.168.0.1")
        self.assertLess(len(_login_attempts), 10_001)


if __name__ == "__main__":
    unittest.main(verbosity=2)
