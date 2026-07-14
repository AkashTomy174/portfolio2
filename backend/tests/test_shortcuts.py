"""
tests/test_shortcuts.py

Sections
--------
1.  Positive tests           - every alias matches its own intent.
2.  Negative tests           - real questions must never match any shortcut.
3.  Collision matrix         - every alias checked against every other route.
4.  Normalization tests      - punctuation and casing must not affect matching.
5.  Startup validation       - validate_routes() rejects broken configurations.
6.  Handler dispatch         - handlers return correct ShortcutResult.
7.  MatchResult telemetry    - match_intent returns correct metadata.
8.  Resume routing           - resume aliases route correctly.
9.  Contact routing          - contact aliases route correctly.
10. False-positive regression - old keyword bugs must not recur.
11. Async compatibility       - handlers are sync callables (async wrapping tested).
12. Intentional decision      - "what are you doing" routing rationale.
13. Benchmark                 - latency comparison.
"""
from __future__ import annotations

import asyncio
import time
import unittest
from unittest.mock import patch

from app.intents import (
    ALL_ALIASES,
    ASSISTANT_IDENTITY_ALIASES,
    AVAILABILITY_ALIASES,
    CONTACT_ALIASES,
    EXPERIENCE_ALIASES,
    GREETING_ALIASES,
    PROFILE_IDENTITY_ALIASES,
    RESUME_ALIASES,
    ROUTES,
    SMALL_TALK_ALIASES,
    IntentRoute,
    MatchResult,
    ShortcutResult,
    match_intent,
    normalize_query,
    validate_routes,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

ALIAS_GROUPS = [
    ("greeting",           GREETING_ALIASES),
    ("small_talk",         SMALL_TALK_ALIASES),
    ("assistant_identity", ASSISTANT_IDENTITY_ALIASES),
    ("profile_identity",   PROFILE_IDENTITY_ALIASES),
    ("experience",         EXPERIENCE_ALIASES),
    ("availability",       AVAILABILITY_ALIASES),
    ("resume",             RESUME_ALIASES),
    ("contact",            CONTACT_ALIASES),
]


def _match(message: str) -> MatchResult | None:
    return match_intent(normalize_query(message))


def _intent(message: str) -> str | None:
    result = _match(message)
    return result.route.name if result else None


# ---------------------------------------------------------------------------
# 1. Positive tests
# ---------------------------------------------------------------------------

class TestGreetingPositive(unittest.TestCase):
    cases = [
        "hi", "hii", "hiii", "hello", "hey", "heya", "hiya", "yo", "sup",
        "good morning", "good afternoon", "good evening", "good day",
        "hi there", "hello there", "hey there", "greetings",
        # similarity pass
        "helo", "heyy", "helo there",
        # casing and punctuation
        "Hello!", "HI", "Hey.", "HELLO",
    ]

    def test_matches(self):
        for msg in self.cases:
            with self.subTest(msg=msg):
                self.assertEqual(_intent(msg), "greeting",
                    f"expected greeting for {msg!r}, got {_intent(msg)!r}")


class TestSmallTalkPositive(unittest.TestCase):
    cases = [
        "how are you", "how are you doing", "how are you today",
        "how are you doing today", "how is it going", "how is everything",
        "how have you been", "how do you do", "hows it going",
        "how are things", "how are things going",
        "hi how are you", "hello how are you", "hey how are you",
        "how are you?", "How Are You?",
    ]

    def test_matches(self):
        for msg in self.cases:
            with self.subTest(msg=msg):
                self.assertEqual(_intent(msg), "small_talk",
                    f"expected small_talk for {msg!r}, got {_intent(msg)!r}")


class TestAssistantIdentityPositive(unittest.TestCase):
    cases = [
        "who are you", "what are you", "what is your name", "whats your name",
        "what do you do", "who am i talking to", "who am i speaking to",
        "who is this", "what is this", "are you a bot", "are you an ai",
        "are you real", "are you human", "tell me about yourself",
        "introduce yourself", "Who Are You?", "WHAT IS YOUR NAME",
    ]

    def test_matches(self):
        for msg in self.cases:
            with self.subTest(msg=msg):
                self.assertEqual(_intent(msg), "assistant_identity",
                    f"expected assistant_identity for {msg!r}, got {_intent(msg)!r}")


class TestProfileIdentityPositive(unittest.TestCase):
    cases = [
        "who is akash", "who is akash tomy", "tell me about akash",
        "tell me about akash tomy", "who is he", "describe akash",
        "describe akash tomy", "give me a summary of akash",
        "give me an overview of akash", "what is akash about",
    ]

    def test_matches(self):
        for msg in self.cases:
            with self.subTest(msg=msg):
                self.assertEqual(_intent(msg), "profile_identity",
                    f"expected profile_identity for {msg!r}, got {_intent(msg)!r}")


class TestExperiencePositive(unittest.TestCase):
    cases = [
        "what is your experience", "what is his experience",
        "tell me about his experience", "tell me about your experience",
        "what experience does he have", "what experience does akash have",
        "work experience", "job history", "career history",
        "where has he worked", "where did he work", "where has akash worked",
        "what is his background", "what is your background",
        "professional background", "internship",
        "where did he intern", "where did akash intern",
    ]

    def test_matches(self):
        for msg in self.cases:
            with self.subTest(msg=msg):
                self.assertEqual(_intent(msg), "experience",
                    f"expected experience for {msg!r}, got {_intent(msg)!r}")


class TestAvailabilityPositive(unittest.TestCase):
    cases = [
        "is he available", "is akash available", "is he open to work",
        "is akash open to work", "is he looking for a job",
        "is he looking for work", "is he open for opportunities",
        "open to work", "open for work", "looking for work",
        "looking for a job", "available for work", "available for hire",
        "free for a call", "free for call",
        "when can he start", "when is he available",
    ]

    def test_matches(self):
        for msg in self.cases:
            with self.subTest(msg=msg):
                self.assertEqual(_intent(msg), "availability",
                    f"expected availability for {msg!r}, got {_intent(msg)!r}")


# ---------------------------------------------------------------------------
# 2. Negative tests
# ---------------------------------------------------------------------------

class TestNegativeCases(unittest.TestCase):
    """
    Legitimate user questions that must fall through to RAG + LLM.
    Any non-None return from match_intent() here is a false positive.
    """
    must_reach_rag = [
        # Original confirmed bug
        "What are your strengths?",
        # Task spec
        "how do you work",
        "what are your skills",
        "what technologies do you use",
        "who is your favorite",
        "are you kidding",
        "what is your backend",
        "what is your architecture",
        "what database do you use",
        # Refactor spec
        "tell me about django",
        "how to deploy django",
        "how does redis work",
        "what is celery",
        "who invented python",
        # Portfolio questions
        "why should we hire him",
        "why should i recruit akash",
        "tell me about his backend skills",
        "explain his backend skills",
        "what projects has he built",
        "what is easybuy",
        "how does the chatbot work",
        "what is ai project judge",
        "what are his strengths",
        "what makes him different",
        "how does he handle concurrency",
        "what is his tech stack",
        "does he know redis",
        "has he deployed to aws",
        "what is his strongest skill",
        "tell me about his projects",
        # Near-misses
        "what are you doing",
        "how do you handle errors",
        "who is your creator",
        "tell me about his skills",
        "what is your experience with django",
    ]

    def test_no_shortcut_fires(self):
        for msg in self.must_reach_rag:
            with self.subTest(msg=msg):
                result = _match(msg)
                intent_name = result.route.name if result is not None else None
                self.assertIsNone(
                    result,
                    f"FALSE POSITIVE: {msg!r} matched intent={intent_name!r}",
                )


# ---------------------------------------------------------------------------
# 3. Collision matrix
# ---------------------------------------------------------------------------

class TestCollisionMatrix(unittest.TestCase):
    """Every alias must match only its own route, never another."""

    def test_no_cross_intent_collision(self):
        for owner_name, aliases in ALIAS_GROUPS:
            for alias in aliases:
                result = _match(alias)
                with self.subTest(alias=alias, owner=owner_name):
                    self.assertIsNotNone(result,
                        f"Alias {alias!r} (owner={owner_name!r}) matched nothing.")
                    self.assertEqual(result.route.name, owner_name,
                        f"COLLISION: {alias!r} (owner={owner_name!r}) "
                        f"fired {result.route.name!r}")


# ---------------------------------------------------------------------------
# 4. Normalization tests
# ---------------------------------------------------------------------------

class TestNormalization(unittest.TestCase):

    def test_strips_punctuation(self):
        cases = [
            ("Hello!", "hello"),
            ("HELLO", "hello"),
            ("Hello...", "hello"),
            ("hello   world", "hello world"),
            ("Who are you???", "who are you"),
            ("  hi  ", "hi"),
            ("How Are You?", "how are you"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_query(raw), expected)

    def test_casing_variants_identical(self):
        for v in ["HELLO", "Hello", "hello", "Hello!", "HELLO!!!"]:
            with self.subTest(v=v):
                result = _match(v)
                self.assertIsNotNone(result)
                self.assertEqual(result.route.name, "greeting")

    def test_punctuation_variants_identical(self):
        for v in ["who are you", "Who are you?", "WHO ARE YOU!", "who are you..."]:
            with self.subTest(v=v):
                result = _match(v)
                self.assertIsNotNone(result)
                self.assertEqual(result.route.name, "assistant_identity")

    def test_whitespace_variants_identical(self):
        for v in ["how are you", "  how are you  ", "how  are  you"]:
            with self.subTest(v=v):
                result = _match(v)
                self.assertIsNotNone(result)
                self.assertEqual(result.route.name, "small_talk")


# ---------------------------------------------------------------------------
# 5. Startup validation
# ---------------------------------------------------------------------------

class TestStartupValidation(unittest.TestCase):

    def _route(self, name: str, aliases: frozenset[str]) -> IntentRoute:
        return IntentRoute(
            name=name,
            aliases=aliases,
            handler=lambda q: ShortcutResult(text="test", sources=[]),
            allow_similarity=False,
            description="test",
        )

    def test_valid_routes_pass(self):
        validate_routes(ROUTES)  # must not raise

    def test_empty_alias_set_raises(self):
        with self.assertRaises(ValueError) as ctx:
            IntentRoute(
                name="empty",
                aliases=frozenset(),
                handler=lambda q: ShortcutResult(text="x", sources=[]),
                allow_similarity=False,
                description="empty",
            )
        self.assertIn("empty alias set", str(ctx.exception))

    def test_non_callable_handler_raises(self):
        with self.assertRaises(ValueError) as ctx:
            IntentRoute(
                name="bad",
                aliases=frozenset({"test"}),
                handler="not_callable",  # type: ignore[arg-type]
                allow_similarity=False,
                description="bad",
            )
        self.assertIn("non-callable handler", str(ctx.exception))

    def test_cross_route_raw_collision_raises(self):
        routes = [
            self._route("a", frozenset({"hello", "hi"})),
            self._route("b", frozenset({"hello", "hey"})),
        ]
        with self.assertRaises(ValueError) as ctx:
            validate_routes(routes)
        self.assertIn("hello", str(ctx.exception))
        self.assertIn("route 1", str(ctx.exception))

    def test_post_normalization_collision_raises(self):
        routes = [
            self._route("a", frozenset({"Hello!"})),
            self._route("b", frozenset({"hello"})),
        ]
        with self.assertRaises(ValueError) as ctx:
            validate_routes(routes)
        self.assertIn("hello", str(ctx.exception))

    def test_intra_route_normalization_collision_raises(self):
        routes = [self._route("a", frozenset({"Hello!", "hello"}))]
        with self.assertRaises(ValueError) as ctx:
            validate_routes(routes)
        self.assertIn("hello", str(ctx.exception))

    def test_disjoint_routes_pass(self):
        routes = [
            self._route("a", frozenset({"alpha", "beta"})),
            self._route("b", frozenset({"gamma", "delta"})),
        ]
        validate_routes(routes)  # must not raise


# ---------------------------------------------------------------------------
# 6. Handler dispatch
# ---------------------------------------------------------------------------

class TestHandlerDispatch(unittest.TestCase):
    """Handlers must return ShortcutResult with correct text and sources."""

    def _dispatch(self, message: str) -> ShortcutResult | None:
        result = _match(message)
        if result is None:
            return None
        return result.route.handler(message)

    def test_greeting_handler(self):
        sr = self._dispatch("hello")
        self.assertIsNotNone(sr)
        self.assertIn("AI Akash", sr.text)
        self.assertEqual(sr.sources, ())

    def test_small_talk_handler(self):
        sr = self._dispatch("how are you")
        self.assertIsNotNone(sr)
        self.assertIn("doing well", sr.text)
        self.assertEqual(sr.sources, ())

    def test_assistant_identity_handler(self):
        sr = self._dispatch("who are you")
        self.assertIsNotNone(sr)
        self.assertIn("AI Akash", sr.text)
        self.assertEqual(sr.sources, ())

    def test_profile_identity_handler(self):
        sr = self._dispatch("who is akash")
        self.assertIsNotNone(sr)
        self.assertIn("Akash Tomy", sr.text)
        self.assertIn("about", sr.sources)

    def test_experience_handler(self):
        sr = self._dispatch("work experience")
        self.assertIsNotNone(sr)
        self.assertIn("SMEC", sr.text)
        self.assertIn("experience", sr.sources)

    def test_availability_handler(self):
        sr = self._dispatch("open to work")
        self.assertIsNotNone(sr)
        self.assertIn("full-time", sr.text)
        self.assertIn("qa", sr.sources)

    def test_resume_handler(self):
        sr = self._dispatch("resume")
        self.assertIsNotNone(sr)
        self.assertIn("AkashTomy-Resume.pdf", sr.text)
        self.assertIn("about", sr.sources)

    def test_contact_handler(self):
        sr = self._dispatch("contact details")
        self.assertIsNotNone(sr)
        self.assertIn("akashtomy174@gmail.com", sr.text)
        self.assertIn("about", sr.sources)

    def test_rag_miss_returns_none(self):
        self.assertIsNone(self._dispatch("what are your strengths"))

    def test_handler_receives_original_query(self):
        """Handler must receive the original query, not the normalized one."""
        received = []

        def capturing_handler(query: str) -> ShortcutResult:
            received.append(query)
            return ShortcutResult(text="ok", sources=[])

        route = IntentRoute(
            name="test",
            aliases=frozenset({"test phrase"}),
            handler=capturing_handler,
            allow_similarity=False,
            description="test",
        )
        result = route.match("test phrase", is_known_exact=False)
        self.assertIsNotNone(result)
        route.handler("Test Phrase!")
        self.assertEqual(received, ["Test Phrase!"])


# ---------------------------------------------------------------------------
# 7. MatchResult telemetry
# ---------------------------------------------------------------------------

class TestMatchResultTelemetry(unittest.TestCase):

    def test_exact_match_fields(self):
        result = _match("hello")
        self.assertIsNotNone(result)
        self.assertEqual(result.route.name, "greeting")
        self.assertEqual(result.normalized, "hello")
        self.assertEqual(result.matched_alias, "hello")
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.match_type, "exact")

    def test_similarity_match_fields(self):
        result = _match("helo")
        self.assertIsNotNone(result)
        self.assertEqual(result.route.name, "greeting")
        self.assertEqual(result.normalized, "helo")
        self.assertEqual(result.match_type, "similarity")
        self.assertGreater(result.score, 0.0)
        self.assertLessEqual(result.score, 1.0)
        self.assertIsNotNone(result.matched_alias)

    def test_no_match_returns_none(self):
        self.assertIsNone(_match("what are your strengths"))

    def test_exact_score_is_1(self):
        for alias in ["hi", "how are you", "who are you", "open to work"]:
            with self.subTest(alias=alias):
                result = _match(alias)
                self.assertIsNotNone(result)
                self.assertEqual(result.score, 1.0)
                self.assertEqual(result.match_type, "exact")

    def test_similarity_score_below_1(self):
        result = _match("heyy")
        self.assertIsNotNone(result)
        self.assertLess(result.score, 1.0)
        self.assertEqual(result.match_type, "similarity")


# ---------------------------------------------------------------------------
# 8. Resume routing
# ---------------------------------------------------------------------------

class TestResumeRouting(unittest.TestCase):

    def test_resume_aliases_match(self):
        cases = [
            "resume", "cv", "curriculum vitae", "download resume", "download cv",
            "get resume", "get cv", "akash resume", "akash cv",
            "his resume", "his cv", "share resume", "share cv",
            "send resume", "send cv", "where is his resume", "where is his cv",
            "can i see his resume", "can i see his cv",
            "do you have a resume", "do you have a cv",
        ]
        for msg in cases:
            with self.subTest(msg=msg):
                self.assertEqual(_intent(msg), "resume",
                    f"expected resume for {msg!r}, got {_intent(msg)!r}")

    def test_resume_response_contains_link(self):
        result = _match("resume")
        self.assertIsNotNone(result)
        sr = result.route.handler("resume")
        self.assertIn("AkashTomy-Resume.pdf", sr.text)


# ---------------------------------------------------------------------------
# 9. Contact routing
# ---------------------------------------------------------------------------

class TestContactRouting(unittest.TestCase):

    def test_contact_aliases_match(self):
        cases = [
            "contact", "contact details", "contact information",
            "how to contact akash", "how to reach akash",
            "how can i contact akash", "how can i reach akash",
            "akash email", "akash linkedin", "akash github",
            "his email", "his linkedin", "his github",
            "email address", "linkedin profile", "github profile",
            "social links", "social media", "get in touch",
            "get in touch with akash", "reach out to akash",
            "connect with akash", "phone number", "whatsapp",
            "akash phone", "akash whatsapp",
        ]
        for msg in cases:
            with self.subTest(msg=msg):
                self.assertEqual(_intent(msg), "contact",
                    f"expected contact for {msg!r}, got {_intent(msg)!r}")

    def test_contact_response_contains_email(self):
        result = _match("contact details")
        self.assertIsNotNone(result)
        sr = result.route.handler("contact details")
        self.assertIn("akashtomy174@gmail.com", sr.text)


# ---------------------------------------------------------------------------
# 10. False-positive regression — old keyword bugs
# ---------------------------------------------------------------------------

class TestFalsePositiveRegression(unittest.TestCase):
    """
    These queries triggered false positives under the old substring-based
    RESUME_KEYWORDS / CONTACT_KEYWORDS approach. They must now reach RAG.
    """
    old_keyword_false_positives = [
        # Old RESUME_KEYWORDS: "cv", "resume", "curriculum", "download"
        "Resume parsing techniques",
        "How does curriculum design work?",
        "Download the latest version",
        "What is a curriculum vitae format?",
        "How to download files from S3?",
        # Old CONTACT_KEYWORDS: "github", "linkedin", "contact", "email", "reach", etc.
        "How do I contact Stripe support?",
        "Can you email the recruiter?",
        "How does GitHub Actions work?",
        "What is LinkedIn's algorithm?",
        "How to reach a consensus in distributed systems?",
        "How do I connect to a database?",
        "What is social proof?",
        "How does phone authentication work?",
        "What is WhatsApp's encryption?",
    ]

    def test_old_keyword_false_positives_reach_rag(self):
        for msg in self.old_keyword_false_positives:
            with self.subTest(msg=msg):
                result = _match(msg)
                intent_name = result.route.name if result is not None else None
                self.assertIsNone(
                    result,
                    f"FALSE POSITIVE REGRESSION: {msg!r} matched intent={intent_name!r}",
                )


# ---------------------------------------------------------------------------
# 11. Async compatibility
# ---------------------------------------------------------------------------

class TestAsyncCompatibility(unittest.TestCase):
    """
    Handlers are sync callables. This test verifies they can be wrapped in
    asyncio.to_thread for use in async contexts without modification.
    """

    def test_handler_callable_in_thread(self):
        async def run():
            result = _match("hello")
            self.assertIsNotNone(result)
            sr = await asyncio.to_thread(result.route.handler, "hello")
            self.assertIn("AI Akash", sr.text)

        asyncio.run(run())

    def test_all_handlers_are_callable(self):
        for route in ROUTES:
            with self.subTest(route=route.name):
                self.assertTrue(callable(route.handler),
                    f"Route '{route.name}' handler is not callable")

    def test_all_handlers_return_shortcut_result(self):
        for route in ROUTES:
            with self.subTest(route=route.name):
                # Use the first alias as a test input
                sample_alias = next(iter(route.aliases))
                result = route.handler(sample_alias)
                self.assertIsInstance(result, ShortcutResult,
                    f"Route '{route.name}' handler did not return ShortcutResult")
                self.assertIsInstance(result.text, str)
                self.assertIsInstance(result.sources, tuple)


# ---------------------------------------------------------------------------
# 12. Intentional decision: "what are you doing" -> RAG
#
# "what are you doing" is not a greeting, not small talk, and not an identity
# question. The closest alias is "what do you do" (assistant_identity), but:
#   SequenceMatcher("what are you doing", "what do you do").ratio() ~ 0.72
# This is below the 0.85 threshold. RAG is the correct destination.
# To change this decision, add "what are you doing" to ASSISTANT_IDENTITY_ALIASES.
# ---------------------------------------------------------------------------

class TestWhatAreYouDoingDecision(unittest.TestCase):
    def test_routes_to_rag(self):
        self.assertIsNone(_match("what are you doing"),
            "'what are you doing' should reach RAG")


# ---------------------------------------------------------------------------
# 13. Benchmark
# ---------------------------------------------------------------------------

class TestBenchmark(unittest.TestCase):
    ITERATIONS = 10_000

    def _time_us(self, message: str) -> float:
        normalized = normalize_query(message)
        start = time.perf_counter()
        for _ in range(self.ITERATIONS):
            match_intent(normalized)
        return (time.perf_counter() - start) / self.ITERATIONS * 1_000_000

    def test_benchmark_and_report(self):
        exact_us    = self._time_us("hello")
        similar_us  = self._time_us("helo")
        rag_miss_us = self._time_us("what are your strengths")

        print(f"\n{'=' * 58}")
        print(f"  Routing benchmark ({self.ITERATIONS:,} iterations each)")
        print(f"{'=' * 58}")
        print(f"  Exact hit    (hello)                 : {exact_us:7.2f} us/call")
        print(f"  Similarity   (helo -> hello)          : {similar_us:7.2f} us/call")
        print(f"  RAG miss     (what are your strengths): {rag_miss_us:7.2f} us/call")
        print(f"{'=' * 58}")

        # Correctness
        self.assertEqual(_intent("hello"), "greeting")
        self.assertEqual(_intent("helo"), "greeting")
        self.assertIsNone(_match("what are your strengths"))

        # Performance guard
        self.assertLess(exact_us, 500,
            "Exact lookup exceeded 500 us — something is wrong")


if __name__ == "__main__":
    unittest.main(verbosity=2)
