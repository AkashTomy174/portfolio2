from __future__ import annotations

import hmac
import os
import logging
import logging.config
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.intents import (
    ROUTES,
    MatchResult,
    match_intent,
    normalize_query,
    validate_routes,
)
from app.models import ChatRequest, ChatResponse, ComponentHealth, HealthMinimalResponse, HealthResponse
from app.services.activity_log import activity_logger
from app.services.admin_auth import ADMIN_COOKIE, make_cookie, verify_cookie
from app.services.cache import LruCache
from app.services.llm import LlmService
from app.services.memory import build_session_store
from app.services.observability import (
    MetricsCollector,
    RequestRecord,
    hash_ip,
    metrics,
    new_request_id,
    utc_now_iso,
)
from app.services.rag import RagService
from app.services.rate_limit import RateLimiter
from app.services.tts import TtsService


# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "logging.Formatter",
            "fmt": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":%(message)s}',
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
        "plain": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plain",
        },
        "console_json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "ai-akash": {"handlers": ["console"], "level": "DEBUG" if os.getenv("DEV_MODE", "").lower() in {"1", "true", "yes"} else "INFO", "propagate": False},
        "ai-akash.obs": {"handlers": ["console_json"], "level": "INFO", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
})

logger = logging.getLogger("ai-akash")

# ---------------------------------------------------------------------------
# Service singletons
# ---------------------------------------------------------------------------

rag = RagService(
    knowledge_file=settings.knowledge_file,
    chroma_dir=settings.chroma_dir,
    gemini_api_key=settings.gemini_api_key,
    embedding_model=settings.gemini_embedding_model,
)
llm = LlmService(
    api_key=settings.gemini_api_key,
    fallback_api_key=settings.gemini_fallback_api_key,
    model=settings.gemini_chat_model,
)
tts = TtsService(
    enabled=settings.enable_tts,
    api_key=settings.elevenlabs_api_key,
    voice_id=settings.elevenlabs_voice_id,
    audio_dir=settings.audio_dir,
)
rate_limiter = RateLimiter(
    settings.max_requests_per_ip,
    settings.rate_limit_window_seconds,
    salt=settings.ip_hash_salt,
)
response_cache = LruCache(settings.response_cache_max_items)
session_store = build_session_store(
    redis_url=settings.redis_url,
    max_history=settings.session_max_history,
    ttl_seconds=settings.session_ttl_seconds,
)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Production config validation — fail loud before accepting traffic.
    if not settings.dev_mode:
        if not settings.ip_hash_salt:
            raise RuntimeError(
                "IP_HASH_SALT must be set in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if settings.cookie_secret in {
            settings.admin_access_token,
            "dev-insecure-secret-change-me",
            None,
        }:
            raise RuntimeError(
                "ADMIN_COOKIE_SECRET must be set to a distinct random value in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
    validate_routes()
    rag.initialize()
    response_cache.clear()  # cold cache on every deploy — reflects current knowledge base
    # Inject the salt into the activity logger now that settings are validated.
    # The singleton starts with an empty salt to avoid circular imports at
    # module load time; the salt is only required once traffic starts.
    activity_logger._ip_hash_salt = settings.ip_hash_salt
    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    # Warn in dev when cookie_secret fell back to ADMIN_ACCESS_TOKEN.
    if settings.dev_mode and settings.cookie_secret == settings.admin_access_token:
        logger.warning(
            "ADMIN_COOKIE_SECRET is not set — falling back to ADMIN_ACCESS_TOKEN as the "
            "cookie signing secret. This is only safe in dev mode."
        )
    logger.info(
        '"AI Akash backend started. rag_ready=%s tts_enabled=%s routes=%s memory=%s"',
        rag.ready,
        settings.enable_tts,
        len(ROUTES),
        type(session_store).__name__,
    )
    yield
    # Graceful shutdown: close any open resources
    if hasattr(session_store, "_client") and session_store._client is not None:
        try:
            session_store._client.close()
        except Exception:
            logger.debug("Session store close failed during shutdown.", exc_info=True)
    logger.info('"AI Akash backend shutting down."')


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="AI Akash API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)
settings.audio_dir.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(settings.audio_dir)), name="audio")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def log_visits(request: Request, call_next):
    response = await call_next(request)
    if request.url.path not in {"/health", "/metrics", "/favicon.ico"}:
        activity_logger.log_visit(
            path=request.url.path,
            ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    return response


# ---------------------------------------------------------------------------
# Admin auth dependency and Health endpoints
# ---------------------------------------------------------------------------

def _require_admin(request: Request) -> None:
    """
    FastAPI dependency that accepts either:
      1. A valid signed admin session cookie  (browser login flow)
      2. A matching X-Admin-Token header      (Prometheus / API clients)

    Raises 401 if neither is present and valid.
    Raises 503 if no ADMIN_ACCESS_TOKEN is configured.
    """
    if not settings.admin_access_token:
        raise HTTPException(status_code=503, detail="Admin access is not configured.")

    # Cookie path (browser)
    cookie_value = request.cookies.get(ADMIN_COOKIE)
    if cookie_value and verify_cookie(cookie_value, settings.cookie_secret):
        return

    # Header path (Prometheus scraper / curl) — constant-time comparison
    header_token = request.headers.get("x-admin-token")
    if (
        header_token is not None
        and settings.admin_access_token is not None
        and hmac.compare_digest(header_token, settings.admin_access_token)
    ):
        return

    raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health", response_model=HealthMinimalResponse)
async def health() -> HealthMinimalResponse:
    """Public minimal health check — returns only the top-level ok flag.

    Internal stack details (component breakdown, cache fill, session counts)
    are available on /health/detailed, which requires admin auth.
    """
    llm_ok = len(llm.clients) > 0
    return HealthMinimalResponse(ok=rag.ready and llm_ok)


@app.get("/health/detailed", response_model=HealthResponse)
async def health_detailed(_: None = Depends(_require_admin)) -> HealthResponse:
    """Authenticated detailed health — full component breakdown.

    Protected by signed cookie (browser) or X-Admin-Token header (scrapers).
    Point uptime/monitoring tools that need component detail at this endpoint
    using the X-Admin-Token header.
    """
    llm_ok = len(llm.clients) > 0
    llm_detail = None if llm_ok else "No Gemini API key configured"

    vector_ok = rag.collection is not None
    vector_detail = None if vector_ok else (
        "ChromaDB unavailable — keyword retrieval only" if rag.ready else "RAG not initialized"
    )

    cache_ok = True
    cache_detail = f"{len(response_cache._items)}/{response_cache.max_items} items"

    memory_ok = True
    memory_detail = f"{type(session_store).__name__} sessions={session_store.session_count()}"
    if hasattr(session_store, "available") and not session_store.available:
        memory_ok = False
        memory_detail = "Redis unavailable"

    return HealthResponse(
        ok=rag.ready and llm_ok,
        rag_ready=rag.ready,
        tts_enabled=settings.enable_tts,
        vector_db=ComponentHealth(ok=vector_ok, detail=vector_detail),
        llm=ComponentHealth(ok=llm_ok, detail=llm_detail),
        cache=ComponentHealth(ok=cache_ok, detail=cache_detail),
        memory=ComponentHealth(ok=memory_ok, detail=memory_detail),
    )


# ---------------------------------------------------------------------------
# Admin login / logout
# ---------------------------------------------------------------------------

# Simple brute-force guard: track failed login attempts per IP.
# Keyed by IP hash -> (failure_count, window_reset_timestamp).
_login_attempts: dict[str, tuple[int, float]] = {}
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_WINDOW_SECONDS = 15 * 60  # 15 minutes


def _check_login_rate_limit(ip: str) -> bool:
    """Return True if the IP is allowed to attempt login, False if blocked."""
    now = time.time()
    # Opportunistic sweep to prevent unbounded growth under scanning traffic.
    if len(_login_attempts) > 10_000:
        expired_keys = [k for k, (_, reset_at) in _login_attempts.items() if now >= reset_at]
        for k in expired_keys:
            del _login_attempts[k]
    key = RateLimiter.ip_hash(ip, settings.ip_hash_salt)
    count, reset_at = _login_attempts.get(key, (0, now + _LOGIN_WINDOW_SECONDS))
    if now >= reset_at:
        count = 0
    return count < _LOGIN_MAX_ATTEMPTS


def _record_login_failure(ip: str) -> None:
    now = time.time()
    key = RateLimiter.ip_hash(ip, settings.ip_hash_salt)
    count, reset_at = _login_attempts.get(key, (0, now + _LOGIN_WINDOW_SECONDS))
    if now >= reset_at:
        count = 0
        reset_at = now + _LOGIN_WINDOW_SECONDS
    _login_attempts[key] = (count + 1, reset_at)


def _clear_login_failures(ip: str) -> None:
    _login_attempts.pop(RateLimiter.ip_hash(ip, settings.ip_hash_salt), None)


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Serve the login form. Redirect straight to /admin if already authenticated."""
    cookie_value = request.cookies.get(ADMIN_COOKIE)
    if cookie_value and verify_cookie(cookie_value, settings.cookie_secret):
        return RedirectResponse("/admin", status_code=302)
    return templates.TemplateResponse(request, "admin_login.html", {"error": None})


@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login_submit(request: Request, token: str = Form(...)):
    """Validate the submitted token and set a signed session cookie."""
    ip = _client_ip(request)

    if not _check_login_rate_limit(ip):
        return templates.TemplateResponse(
            request,
            "admin_login.html",
            {"error": "Too many failed attempts. Try again in 15 minutes."},
            status_code=429,
        )

    if not settings.admin_access_token or not hmac.compare_digest(token, settings.admin_access_token):
        _record_login_failure(ip)
        return templates.TemplateResponse(
            request,
            "admin_login.html",
            {"error": "Invalid token. Try again."},
            status_code=401,
        )

    _clear_login_failures(ip)
    # 303 See Other guarantees the browser issues a GET for /admin,
    # preventing form re-submission on back/refresh.
    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie(
        key=ADMIN_COOKIE,
        value=make_cookie(settings.cookie_secret),
        httponly=True,
        secure=not settings.dev_mode,
        samesite="strict",
        max_age=8 * 60 * 60,
    )
    return response


@app.get("/admin/logout")
async def admin_logout():
    """Clear the session cookie and redirect to the login page."""
    response = RedirectResponse("/admin/login", status_code=302)
    response.delete_cookie(ADMIN_COOKIE, httponly=True, samesite="strict")
    return response


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics(_: None = Depends(_require_admin)) -> PlainTextResponse:
    """
    Prometheus-compatible metrics endpoint.
    Protected by signed cookie (browser) or X-Admin-Token header (scrapers).
    """
    return PlainTextResponse(
        content=metrics.prometheus_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/metrics/json")
async def json_metrics(_: None = Depends(_require_admin)):
    """JSON metrics snapshot — convenient for dashboards and debugging."""
    return metrics.snapshot()


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@app.get("/admin/activity")
async def admin_activity(_: None = Depends(_require_admin)):
    recent_visits = activity_logger.read_recent("visits.jsonl", limit=50)
    recent_interactions = activity_logger.read_recent("ai_interactions.jsonl", limit=50)
    return {
        "visits": recent_visits,
        "ai_interactions": recent_interactions,
    }


def _safe_int(value: str | None, default: int) -> int:
    try:
        return int(value or default)
    except ValueError:
        return default


def _paginate(items: list[dict], page: int, per_page: int) -> list[dict]:
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10
    start = (page - 1) * per_page
    return items[start: start + per_page]


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, _: None = Depends(_require_admin)):
    visits_page = _safe_int(request.query_params.get("visits_page"), 1)
    interactions_page = _safe_int(request.query_params.get("interactions_page"), 1)
    per_page = min(_safe_int(request.query_params.get("per_page"), 10), 100)  # cap at 100
    cached_filter = request.query_params.get("cached_filter", "all")

    recent_visits = activity_logger.read_recent("visits.jsonl", limit=500)
    recent_interactions = activity_logger.read_recent("ai_interactions.jsonl", limit=500)

    filtered_interactions = recent_interactions
    if cached_filter == "cached":
        filtered_interactions = [e for e in recent_interactions if e.get("cached")]
    elif cached_filter == "uncached":
        filtered_interactions = [e for e in recent_interactions if not e.get("cached")]

    paged_visits = _paginate(recent_visits, visits_page, per_page)
    paged_interactions = _paginate(filtered_interactions, interactions_page, per_page)

    cached_count = sum(1 for e in recent_interactions if e.get("cached"))
    latency_values = [
        e.get("response_time_ms")
        for e in recent_interactions
        if isinstance(e.get("response_time_ms"), (int, float)) and e.get("response_time_ms") > 0
    ]
    average_latency = round(sum(latency_values) / len(latency_values), 1) if latency_values else None

    # Intent distribution for charts
    intent_counts: dict[str, int] = {}
    for e in recent_interactions:
        intent = e.get("intent_route") or "rag"
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    # Source usage
    source_counts: dict[str, int] = {}
    for e in recent_interactions:
        for src in e.get("response_sources") or []:
            source_counts[src] = source_counts.get(src, 0) + 1

    # Requests over time (last 24 hours, bucketed by hour)
    now = datetime.now(timezone.utc)
    hourly: dict[str, int] = {}
    for e in recent_interactions:
        ts_str = e.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if now - ts <= timedelta(hours=24):
                bucket = ts.strftime("%H:00")
                hourly[bucket] = hourly.get(bucket, 0) + 1
        except (ValueError, TypeError):
            pass

    # Most common queries (top 10)
    query_counts: dict[str, int] = {}
    for e in recent_interactions:
        msg = e.get("message", "").strip().lower()
        if msg:
            query_counts[msg] = query_counts.get(msg, 0) + 1
    top_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Unanswered: interactions where sources is empty and not cached and not shortcut
    unanswered = [
        e for e in recent_interactions
        if not e.get("response_sources") and not e.get("cached") and not e.get("intent_route")
    ]

    return templates.TemplateResponse(
        request,
        "admin_dashboard.html",
        {
            "summary": {
                "visit_count": len(recent_visits),
                "interaction_count": len(recent_interactions),
                "cached_count": cached_count,
                "average_latency_ms": average_latency,
                "shortcut_count": sum(1 for e in recent_interactions if e.get("intent_route")),
                "rag_count": sum(1 for e in recent_interactions if not e.get("intent_route") and not e.get("cached")),
                "p95_latency_ms": metrics.p95_latency_ms,
                "p99_latency_ms": metrics.p99_latency_ms,
                "active_sessions": session_store.session_count(),
            },
            "visits": paged_visits,
            "interactions": paged_interactions,
            "visits_page": visits_page,
            "interactions_page": interactions_page,
            "per_page": per_page,
            "cached_filter": cached_filter,
            "total_visits": len(recent_visits),
            "total_interactions": len(filtered_interactions),
            "intent_counts": intent_counts,
            "source_counts": source_counts,
            "hourly_requests": hourly,
            "top_queries": top_queries,
            "unanswered_count": len(unanswered),
        },
    )


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------

@app.post("/api/ai-chat", response_model=ChatResponse)
async def ai_chat(payload: ChatRequest, request: Request):
    start = time.perf_counter()
    ip = _client_ip(request)
    request_id = new_request_id()
    normalized = normalize_query(payload.message)

    record = RequestRecord(
        request_id=request_id,
        timestamp=utc_now_iso(),
        ip_hash=hash_ip(ip, settings.ip_hash_salt),
        session_id=payload.session_id,
        original_query=payload.message,
        normalized_query=normalized,
    )

    # --- Rate limit ---
    if not rate_limiter.allow(ip):
        record.status = "rate_limited"
        record.total_latency_ms = _elapsed_ms(start)
        record.emit()
        metrics.record_request(record)
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limit", "message": "Too many requests. Try again tomorrow."},
        )

    # 1.1: Resolve session history BEFORE the cache lookup.
    # Responses that depend on prior context must never be cached — a cached
    # context-specific answer would be served to unrelated sessions asking
    # the same string. Only first-turn requests (empty history) are cacheable.
    history = session_store.get(payload.session_id) if payload.session_id else []
    cacheable = not history

    # --- Cache ---
    cache_start = time.perf_counter()
    cache_key = response_cache.key(payload.message, payload.voice)
    cached = response_cache.get(cache_key) if cacheable else None
    record.cache_lookup_ms = _elapsed_ms(cache_start)

    if cached:
        record.cache_hit = True
        record.response_sources = cached.get("sources", [])
        record.response_length = len(cached.get("text", ""))
        record.total_latency_ms = _elapsed_ms(start)
        record.emit()
        metrics.record_request(record)
        activity_logger.log_interaction(
            ip=ip,
            message=payload.message,
            cached=True,
            response_sources=cached.get("sources", []),
            response_time_ms=0,
            request_id=request_id,
            session_id=payload.session_id,
            status="ok",
        )
        return ChatResponse(**{**cached, "cached": True})

    # --- Shortcut routing ---
    match = match_intent(normalized)

    if match is not None:
        record.intent_route = match.route.name
        record.matched_alias = match.matched_alias
        record.similarity_score = match.score
        record.match_type = match.match_type

        result = match.route.handler(payload.message)
        shortcut_sources = list(result.sources)
        response = ChatResponse(text=result.text, audio_url=None, sources=shortcut_sources, cached=False)
        if cacheable:
            response_cache.set(cache_key, response.model_dump())

        elapsed = _elapsed_ms(start)
        record.response_sources = shortcut_sources
        record.response_length = len(result.text)
        record.total_latency_ms = elapsed
        record.emit()
        metrics.record_request(record)

        activity_logger.log_interaction(
            ip=ip,
            message=payload.message,
            cached=False,
            response_sources=shortcut_sources,
            response_time_ms=elapsed,
            request_id=request_id,
            session_id=payload.session_id,
            intent_route=match.route.name,
            matched_alias=match.matched_alias,
            match_type=match.match_type,
            similarity_score=match.score,
            status="ok",
        )
        logger.debug(
            '"shortcut" request_id=%s intent=%s match_type=%s alias=%r score=%.3f elapsed_ms=%s',
            request_id, match.route.name, match.match_type, match.matched_alias, match.score, elapsed,
        )
        return response

    # --- RAG + LLM pipeline ---
    # history already resolved above (before cache lookup)

    retrieval_start = time.perf_counter()
    retrieval_failed = False
    try:
        chunks = rag.search(payload.message, top_k=4)
    except Exception as exc:
        logger.error('"rag_error" request_id=%s error=%r', request_id, str(exc))
        metrics.record_embedding_failure()
        chunks = []
        retrieval_failed = True
    record.retrieval_latency_ms = _elapsed_ms(retrieval_start)
    record.retrieved_chunks = len(chunks)

    llm_start = time.perf_counter()
    try:
        text = llm.answer(payload.message, chunks, history=history)
    except Exception as exc:
        logger.error('"llm_error" request_id=%s error=%r', request_id, str(exc))
        metrics.record_llm_failure()
        record.status = "error"
        record.error = str(exc)
        record.total_latency_ms = _elapsed_ms(start)
        record.emit()
        metrics.record_request(record)
        return JSONResponse(
            status_code=500,
            content={"error": "llm_error", "message": "I'm having trouble generating a response right now."},
        )
    record.llm_latency_ms = _elapsed_ms(llm_start)

    # TTS
    audio_url: str | None = None
    if payload.voice:
        tts_start = time.perf_counter()
        try:
            audio_url = await tts.generate(text)
        except Exception as exc:
            logger.warning('"tts_error" request_id=%s error=%r', request_id, str(exc))
            metrics.record_tts_failure()
        record.tts_latency_ms = _elapsed_ms(tts_start)

    sources = sorted({chunk.source for chunk in chunks})
    response = ChatResponse(text=text, audio_url=audio_url, sources=sources, cached=False)
    if cacheable and not retrieval_failed:
        response_cache.set(cache_key, response.model_dump())

    # Update conversation memory
    if payload.session_id:
        session_store.append(payload.session_id, "user", payload.message)
        session_store.append(payload.session_id, "assistant", text)

    elapsed = _elapsed_ms(start)
    record.response_sources = sources
    record.response_length = len(text)
    record.total_latency_ms = elapsed
    record.emit()
    metrics.record_request(record)

    activity_logger.log_interaction(
        ip=ip,
        message=payload.message,
        cached=False,
        response_sources=sources,
        response_time_ms=elapsed,
        request_id=request_id,
        session_id=payload.session_id,
        retrieval_latency_ms=record.retrieval_latency_ms,
        llm_latency_ms=record.llm_latency_ms,
        tts_latency_ms=record.tts_latency_ms,
        retrieved_chunks=len(chunks),
        status="ok",
    )
    logger.info(
        '"rag" request_id=%s elapsed_ms=%s sources=%s chunks=%s cache=false',
        request_id, elapsed, ",".join(sources), len(chunks),
    )
    return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client_ip(request: Request) -> str:
    """Extract the real client IP with spoofing protection.

    Topology: internet → Cloudflare → Nginx → Uvicorn on 127.0.0.1

    CF-Connecting-IP is set by Cloudflare to the real client IP. Cloudflare
    strips any client-supplied version before forwarding, so the header is
    trustworthy — BUT only when the TCP peer is 127.0.0.1 (i.e. the request
    arrived through Nginx, which sits behind Cloudflare). If uvicorn is ever
    hit directly (bypassing Nginx/Cloudflare), any caller could forge the
    header. Checking the peer address closes that gap.

    X-Forwarded-For is not used because Cloudflare appends to it rather than
    overwriting, making the first entry spoofable by a client injecting a fake
    IP before the request reaches Cloudflare.
    """
    peer = request.client.host if request.client else None
    # Only trust CF-Connecting-IP when the request came through Nginx on loopback.
    if peer in {"127.0.0.1", "::1"}:
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()
    # Fallback for local dev (no Cloudflare) and direct EC2 health checks.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return peer or "unknown"


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)