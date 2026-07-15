"""
app/intents.py — Intent routing configuration for the AI Akash chatbot.

Architecture
------------
Routing is separated from presentation.

  IntentRoute   — routing metadata: aliases, handler, similarity policy.
  ShortcutResult — what a handler returns: text and source tags.
  MatchResult   — what the router returns: the matched route plus full
                  telemetry (normalized query, matched alias, score, match type).

The router (match_intent) accepts a pre-normalized string so normalization
happens exactly once in the request path. main.py normalizes, then passes
the result here. No double work.

Similarity policy
-----------------
Similarity matching (difflib.SequenceMatcher) is allowed ONLY for the
greeting intent.

Why greetings allow similarity
  Users commonly mistype short words: "helo", "heyy", "hellp". The aliases
  are structurally unlike any real question (they are 1-2 tokens, contain no
  verbs of inquiry, and carry no semantic content). A false positive here
  returns "Hi, I'm AI Akash" — a low-cost mistake. The threshold (0.85) is
  conservative enough to reject "hi there" matching "hi" at 0.67.

Why identity does NOT allow similarity
  "who are you" and "how are you" have a SequenceMatcher ratio of ~0.91.
  A false positive here returns a hardcoded identity response instead of
  routing a real question to RAG. The cost is high. Exact-only is correct.

Why availability does NOT allow similarity
  "is he available" and "is he able" are structurally similar. Exact-only
  prevents accidental matches on questions about capability.

Why experience does NOT allow similarity
  "tell me about his experience" and "tell me about his experiments" differ
  by one word. Exact-only is the only safe policy for multi-word phrases.

Adding a new intent
-------------------
1. Define a frozenset of aliases (all lowercase, no punctuation).
2. Write a handler function: (original_query: str) -> ShortcutResult.
3. Append an IntentRoute to ROUTES with allow_similarity=False unless the
   intent consists exclusively of very short single-word inputs.
4. Run the test suite. validate_routes() catches alias collisions at startup.

Modifying an existing intent
-----------------------------
1. Add or remove entries from the relevant frozenset.
2. Run the test suite. The collision matrix catches cross-intent conflicts.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Callable


# ---------------------------------------------------------------------------
# Handler return type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShortcutResult:
    """
    The data a handler returns.

    Keeping this separate from IntentRoute means handlers can be dynamic:
    they can read from a database, check feature flags, or vary the response
    based on context. The router never owns response text.
    """
    text: str
    sources: tuple[str, ...]


# ---------------------------------------------------------------------------
# Match telemetry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MatchResult:
    """
    Everything the router knows about a successful match.

    Returned by match_intent(). main.py uses this to log rich diagnostics
    and to invoke the handler. Nothing is discarded silently.

    Fields
    ------
    route         : The matched IntentRoute.
    normalized    : The normalized query string that was matched.
    matched_alias : The exact alias that triggered the match.
    score         : 1.0 for exact matches, SequenceMatcher ratio for similarity.
    match_type    : "exact" or "similarity".
    """
    route: IntentRoute
    normalized: str
    matched_alias: str
    score: float
    match_type: str  # "exact" | "similarity"


# ---------------------------------------------------------------------------
# IntentRoute
# ---------------------------------------------------------------------------

# Similarity threshold for the greeting intent.
# 0.85 catches "helo"→"hello" (ratio≈0.89) and "heyy"→"hey" (ratio≈0.86)
# while rejecting structurally different inputs.
GREETING_SIMILARITY_THRESHOLD: float = 0.85


@dataclass(frozen=True)
class IntentRoute:
    """
    Routing metadata for a single shortcut intent.

    Fields
    ------
    name            : Unique identifier used in logs and tests.
    aliases         : Exact normalized phrases that trigger this intent.
    handler         : Callable[(original_query: str) -> ShortcutResult].
                      Receives the original (un-normalized) query so handlers
                      can use it for personalization or logging if needed.
                      Designed to be sync now; async support is added in
                      main.py by wrapping in asyncio.to_thread if required.
    allow_similarity: When True, a SequenceMatcher pass runs after exact
                      lookup. Only enable for intents whose aliases are short
                      single words where typos are common (greetings only).
    description     : Human-readable explanation of what this intent covers
                      and why the similarity policy is set as it is.
    """
    name: str
    aliases: frozenset[str]
    handler: Callable[[str], ShortcutResult]
    allow_similarity: bool
    description: str

    def __post_init__(self) -> None:
        if not self.aliases:
            raise ValueError(
                f"IntentRoute '{self.name}' has an empty alias set. "
                "Every route must have at least one alias."
            )
        if not callable(self.handler):
            raise ValueError(
                f"IntentRoute '{self.name}' has a non-callable handler."
            )

    def match(self, normalized: str, is_known_exact: bool) -> MatchResult | None:
        """
        Attempt to match a pre-normalized query against this route.

        Returns a MatchResult on success, None on failure.

        Parameters
        ----------
        normalized      : Already-normalized query (normalize_query was called
                          by the caller — this method never normalizes again).
        is_known_exact  : True if the normalized query is an exact alias in
                          ANY route's alias set. Used as a collision guard:
                          if True, the similarity pass is skipped so that
                          "how are you" (small_talk alias) cannot accidentally
                          score >= 0.85 against "who are you" (assistant_identity).
        """
        # Fast path: O(1) exact set lookup
        if normalized in self.aliases:
            return MatchResult(
                route=self,
                normalized=normalized,
                matched_alias=normalized,
                score=1.0,
                match_type="exact",
            )

        # Slow path: similarity — only for opted-in routes and only when the
        # query is not already a known exact alias in another set.
        if self.allow_similarity and not is_known_exact:
            best_alias = None
            best_ratio = 0.0
            for alias in self.aliases:
                ratio = difflib.SequenceMatcher(None, normalized, alias).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_alias = alias
            if best_ratio >= GREETING_SIMILARITY_THRESHOLD and best_alias is not None:
                return MatchResult(
                    route=self,
                    normalized=normalized,
                    matched_alias=best_alias,
                    score=best_ratio,
                    match_type="similarity",
                )

        return None


# ---------------------------------------------------------------------------
# Alias sets
# ---------------------------------------------------------------------------

GREETING_ALIASES: frozenset[str] = frozenset({
    "hi",
    "hii",
    "hiii",
    "hello",
    "hey",
    "heya",
    "hiya",
    "yo",
    "sup",
    "good morning",
    "good afternoon",
    "good evening",
    "good day",
    "hi there",
    "hello there",
    "hey there",
    "greetings",
})

SMALL_TALK_ALIASES: frozenset[str] = frozenset({
    "how are you",
    "how are you doing",
    "how are you today",
    "how are you doing today",
    "how re you",
    "howre you",
    "how is it going",
    "how is everything",
    "how have you been",
    "how do you do",
    "hows it going",
    "how are things",
    "how are things going",
    "hi how are you",
    "hello how are you",
    "hey how are you",
})

ASSISTANT_IDENTITY_ALIASES: frozenset[str] = frozenset({
    "who are you",
    "what are you",
    "what is your name",
    "whats your name",
    "what do you do",
    "who am i talking to",
    "who am i speaking to",
    "who is this",
    "what is this",
    "are you a bot",
    "are you an ai",
    "are you real",
    "are you human",
    "tell me about yourself",
    "introduce yourself",
})

PROFILE_IDENTITY_ALIASES: frozenset[str] = frozenset({
    "who is akash",
    "who is akash tomy",
    "tell me about akash",
    "tell me about akash tomy",
    "who is he",
    "describe akash",
    "describe akash tomy",
    "give me a summary of akash",
    "give me an overview of akash",
    "what is akash about",
})

EXPERIENCE_ALIASES: frozenset[str] = frozenset({
    "what is your experience",
    "what is his experience",
    "tell me about his experience",
    "tell me about your experience",
    "what experience does he have",
    "what experience does akash have",
    "work experience",
    "job history",
    "career history",
    "where has he worked",
    "where did he work",
    "where has akash worked",
    "what is his background",
    "what is your background",
    "professional background",
    "internship",
    "where did he intern",
    "where did akash intern",
})

AVAILABILITY_ALIASES: frozenset[str] = frozenset({
    "is he available",
    "is akash available",
    "is he open to work",
    "is akash open to work",
    "is he looking for a job",
    "is he looking for work",
    "is he open for opportunities",
    "open to work",
    "open for work",
    "looking for work",
    "looking for a job",
    "available for work",
    "available for hire",
    "free for a call",
    "free for call",
    "when can he start",
    "when is he available",
    "will he be free for a call",
})

# Resume and contact use explicit alias sets instead of substring containment.
# The old RESUME_KEYWORDS / CONTACT_KEYWORDS approach matched any message
# containing "email", "contact", "resume", etc. as a substring, producing
# false positives like:
#   "How do I contact Stripe support?"  -> returned Akash's contact details
#   "Resume parsing techniques"         -> returned Akash's resume link
#   "Can you email the recruiter?"      -> returned Akash's email
# Explicit aliases eliminate this class of false positive entirely.
RESUME_ALIASES: frozenset[str] = frozenset({
    "resume",
    "cv",
    "curriculum vitae",
    "download resume",
    "download cv",
    "get resume",
    "get cv",
    "akash resume",
    "akash cv",
    "his resume",
    "his cv",
    "share resume",
    "share cv",
    "send resume",
    "send cv",
    "where is his resume",
    "where is his cv",
    "where is the resume",
    "where is the cv",
    "can i see his resume",
    "can i see his cv",
    "can i download his resume",
    "can i download his cv",
    "do you have a resume",
    "do you have a cv",
})

CONTACT_ALIASES: frozenset[str] = frozenset({
    "contact",
    "contact details",
    "contact information",
    "how to contact akash",
    "how to reach akash",
    "how can i contact akash",
    "how can i reach akash",
    "how can i contact him",
    "how can i reach him",
    "akash email",
    "akash linkedin",
    "akash github",
    "his email",
    "his linkedin",
    "his github",
    "what is his email",
    "what is his linkedin",
    "what is his github",
    "share his linkedin",
    "share his github",
    "share his email",
    "email address",
    "linkedin profile",
    "github profile",
    "social links",
    "social media",
    "get in touch",
    "get in touch with akash",
    "reach out to akash",
    "connect with akash",
    "phone number",
    "whatsapp",
    "akash phone",
    "akash whatsapp",
})


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
# Each handler is a plain function: (original_query: str) -> ShortcutResult.
# Handlers own the response text. The router owns nothing about presentation.
# To make a handler async in the future, wrap it in asyncio.to_thread in
# main.py — the IntentRoute interface does not need to change.

def _handle_greeting(_query: str) -> ShortcutResult:
    return ShortcutResult(
        text=(
            "Hi, I'm AI Akash. I can help with Akash's projects, backend work, "
            "experience, skills, or contact details."
        ),
        sources=(),
    )


def _handle_small_talk(_query: str) -> ShortcutResult:
    return ShortcutResult(
        text=(
            "I'm doing well, thanks. Ask me anything about Akash's projects, "
            "backend work, experience, skills, or contact details."
        ),
        sources=(),
    )


def _handle_assistant_identity(_query: str) -> ShortcutResult:
    return ShortcutResult(
        text=(
            "I'm AI Akash, the portfolio assistant for Akash Tomy. I answer "
            "questions about his projects, backend work, experience, skills, and "
            "contact details."
        ),
        sources=(),
    )


def _handle_profile_identity(_query: str) -> ShortcutResult:
    return ShortcutResult(
        text=(
            "Akash Tomy is a backend-focused full stack developer from Alappuzha, "
            "Kerala. He works with Django, FastAPI, Redis, Celery, databases, AWS, "
            "and React, and is especially focused on reliable backend systems and "
            "AI infrastructure."
        ),
        sources=("about",),
    )


def _handle_experience(_query: str) -> ShortcutResult:
    return ShortcutResult(
        text=(
            "Akash Tomy has experience as a Python Full Stack Developer Intern at "
            "SMEC Technologies, with work around backend systems, caching, "
            "databases, AWS deployment, and React-based UI work."
        ),
        sources=("experience",),
    )


def _handle_availability(_query: str) -> ShortcutResult:
    return ShortcutResult(
        text=(
            "Akash is actively looking for full-time opportunities and can discuss "
            "availability directly. The easiest way to reach him is by email at "
            "akashtomy174@gmail.com or on LinkedIn at "
            "https://www.linkedin.com/in/akash-tomy-8b51a737b/."
        ),
        sources=("qa",),
    )


def _handle_resume(_query: str) -> ShortcutResult:
    return ShortcutResult(
        text="You can download Akash's resume here: https://akashtomy.com/AkashTomy-Resume.pdf",
        sources=("about",),
    )


def _handle_contact(_query: str) -> ShortcutResult:
    return ShortcutResult(
        text=(
            "You can reach Akash at: akashtomy174@gmail.com | "
            "LinkedIn: https://www.linkedin.com/in/akash-tomy-8b51a737b/ | "
            "GitHub: https://github.com/AkashTomy174"
        ),
        sources=("about",),
    )


# ---------------------------------------------------------------------------
# Route registry
# ---------------------------------------------------------------------------
# Order determines priority: the first matching route wins.
# Greetings first — most common short input, cheapest to check.
# Resume and contact last — their aliases are longer and more specific.

ROUTES: list[IntentRoute] = [
    IntentRoute(
        name="greeting",
        aliases=GREETING_ALIASES,
        handler=_handle_greeting,
        allow_similarity=True,
        description=(
            "Matches simple greetings. Similarity is enabled because users "
            "commonly mistype short words like 'hello' or 'hey'. The risk of a "
            "false positive is low: greeting aliases are structurally unlike any "
            "real question (1-2 tokens, no interrogative structure)."
        ),
    ),
    IntentRoute(
        name="small_talk",
        aliases=SMALL_TALK_ALIASES,
        handler=_handle_small_talk,
        allow_similarity=False,
        description=(
            "Matches social pleasantries. Exact-only: 'how are you' and 'who are "
            "you' score ~0.91 on SequenceMatcher — similarity would cause "
            "cross-intent collisions."
        ),
    ),
    IntentRoute(
        name="assistant_identity",
        aliases=ASSISTANT_IDENTITY_ALIASES,
        handler=_handle_assistant_identity,
        allow_similarity=False,
        description=(
            "Matches questions about the assistant itself. Exact-only: multi-word "
            "identity phrases are too similar to real questions for safe fuzzy "
            "matching."
        ),
    ),
    IntentRoute(
        name="profile_identity",
        aliases=PROFILE_IDENTITY_ALIASES,
        handler=_handle_profile_identity,
        allow_similarity=False,
        description="Matches questions about who Akash is. Exact-only.",
    ),
    IntentRoute(
        name="experience",
        aliases=EXPERIENCE_ALIASES,
        handler=_handle_experience,
        allow_similarity=False,
        description=(
            "Matches questions about work history. Exact-only: experience phrases "
            "are long and semantically close to real RAG questions."
        ),
    ),
    IntentRoute(
        name="availability",
        aliases=AVAILABILITY_ALIASES,
        handler=_handle_availability,
        allow_similarity=False,
        description="Matches questions about job availability. Exact-only.",
    ),
    IntentRoute(
        name="resume",
        aliases=RESUME_ALIASES,
        handler=_handle_resume,
        allow_similarity=False,
        description=(
            "Matches requests for Akash's resume or CV. Exact-only with explicit "
            "aliases. Replaces the old substring check on 'cv', 'resume', "
            "'curriculum', 'download' which produced false positives on queries "
            "like 'Resume parsing techniques'."
        ),
    ),
    IntentRoute(
        name="contact",
        aliases=CONTACT_ALIASES,
        handler=_handle_contact,
        allow_similarity=False,
        description=(
            "Matches requests for Akash's contact details. Exact-only with "
            "explicit aliases. Replaces the old substring check on 'email', "
            "'contact', 'github', etc. which matched unrelated queries like "
            "'How do I contact Stripe support?'."
        ),
    ),
]

# Union of all alias sets — used as a collision guard in match_intent().
# If a query is an exact alias in ANY set, the similarity pass is skipped
# for all other sets, preventing cross-intent fuzzy collisions.
ALL_ALIASES: frozenset[str] = frozenset().union(*(r.aliases for r in ROUTES))


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_query(message: str) -> str:
    """
    Normalize a raw user message for intent matching.

    Steps:
    1. Lowercase.
    2. Replace all non-word, non-space characters with a space (strips punctuation).
    3. Collapse whitespace.

    Intentionally minimal. Goal: "Hello!" == "hello", "Who are you?" == "who are you".
    Not semantic normalization — that is RAG's job.

    Called ONCE per request in main.py. match_intent() accepts the result
    directly and never calls normalize_query() again.
    """
    lowered = message.lower()
    without_punctuation = re.sub(r"[^\w\s]", " ", lowered)
    return " ".join(without_punctuation.split())


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def match_intent(normalized: str) -> MatchResult | None:
    """
    Return a MatchResult for the first matching route, or None.

    Parameters
    ----------
    normalized : Pre-normalized query string. The caller (main.py) is
                 responsible for calling normalize_query() exactly once
                 before passing the result here.

    Algorithm
    ---------
    1. Compute is_known_exact: O(1) lookup in ALL_ALIASES.
       If True, the similarity pass is skipped for all routes (collision guard).
    2. For each route in ROUTES (registration order):
       a. Delegate to route.match(normalized, is_known_exact).
       b. Return the first MatchResult.
    3. Return None — caller routes to RAG + LLM.

    Returning None is the correct and expected outcome for any real question.
    """
    if not normalized:
        return None

    is_known_exact = normalized in ALL_ALIASES

    for route in ROUTES:
        result = route.match(normalized, is_known_exact)
        if result is not None:
            return result

    return None


# ---------------------------------------------------------------------------
# Startup validator
# ---------------------------------------------------------------------------

def validate_routes(routes: list[IntentRoute] = ROUTES) -> None:
    """
    Validate the route registry at application startup.

    Checks
    ------
    1. No route has an empty alias set.
    2. Every route has a callable handler.
    3. No raw alias appears in more than one route.
    4. No alias from one route normalizes to the same string as an alias
       from another route (post-normalization cross-route collision).
    5. No two aliases in the same route normalize to the same string
       (intra-route normalization collision).

    Raises ValueError with a descriptive message on the first violation.
    Called during FastAPI lifespan so the application refuses to start
    with a broken configuration.
    """
    for route in routes:
        if not route.aliases:
            raise ValueError(
                f"[intents] Route '{route.name}' has an empty alias set."
            )
        if not callable(route.handler):
            raise ValueError(
                f"[intents] Route '{route.name}' has a non-callable handler."
            )

    seen_raw: dict[str, str] = {}
    seen_normalized: dict[str, tuple[str, str]] = {}

    for route in routes:
        for raw_alias in route.aliases:
            if raw_alias in seen_raw:
                raise ValueError(
                    f"[intents] Alias collision detected.\n"
                    f"  alias   : '{raw_alias}'\n"
                    f"  route 1 : '{seen_raw[raw_alias]}'\n"
                    f"  route 2 : '{route.name}'\n"
                    "Remove the duplicate from one of the alias sets."
                )
            seen_raw[raw_alias] = route.name

            norm = normalize_query(raw_alias)
            if norm in seen_normalized:
                prev_raw, prev_route = seen_normalized[norm]
                if prev_route != route.name:
                    raise ValueError(
                        f"[intents] Post-normalization alias collision.\n"
                        f"  normalized : '{norm}'\n"
                        f"  alias 1    : '{prev_raw}' (route: '{prev_route}')\n"
                        f"  alias 2    : '{raw_alias}' (route: '{route.name}')\n"
                        "Both normalize to the same string. Remove or rename one."
                    )
            seen_normalized[norm] = (raw_alias, route.name)

    for route in routes:
        norm_seen: dict[str, str] = {}
        for raw_alias in route.aliases:
            norm = normalize_query(raw_alias)
            if norm in norm_seen:
                raise ValueError(
                    f"[intents] Intra-route normalization collision in '{route.name}'.\n"
                    f"  normalized : '{norm}'\n"
                    f"  alias 1    : '{norm_seen[norm]}'\n"
                    f"  alias 2    : '{raw_alias}'\n"
                    "Both normalize to the same string. Remove one."
                )
            norm_seen[norm] = raw_alias
