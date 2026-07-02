import logging
import math
import re
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pathlib import Path

from app.config import settings
from app.models import ChatRequest, ChatResponse, HealthResponse
from app.services.activity_log import activity_logger
from app.services.cache import LruCache
from app.services.llm import LlmService
from app.services.rag import RagService
from app.services.rate_limit import RateLimiter
from app.services.tts import TtsService


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ai-akash")

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
rate_limiter = RateLimiter(settings.max_requests_per_ip, settings.rate_limit_window_seconds)
response_cache = LruCache(settings.response_cache_max_items)


@asynccontextmanager
async def lifespan(app: FastAPI):
  rag.initialize()
  settings.audio_dir.mkdir(parents=True, exist_ok=True)
  logger.info("AI Akash backend started. rag_ready=%s tts_enabled=%s", rag.ready, settings.enable_tts)
  yield


app = FastAPI(title="AI Akash API", version="0.1.0", lifespan=lifespan)
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


@app.middleware("http")
async def log_visits(request: Request, call_next):
  response = await call_next(request)
  if request.url.path not in {"/health", "/favicon.ico"}:
    activity_logger.log_visit(
      path=request.url.path,
      ip=_client_ip(request),
      user_agent=request.headers.get("user-agent"),
    )
  return response


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
  return HealthResponse(ok=True, rag_ready=rag.ready, tts_enabled=settings.enable_tts)


@app.get("/admin/activity")
async def admin_activity(request: Request):
  token = request.headers.get("x-admin-token")
  if not settings.admin_access_token or token != settings.admin_access_token:
    raise HTTPException(status_code=401, detail="Unauthorized")

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
  end = start + per_page
  return items[start:end]


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
  token = request.headers.get("x-admin-token")
  if not settings.admin_access_token or token != settings.admin_access_token:
    raise HTTPException(status_code=401, detail="Unauthorized")

  visits_page = _safe_int(request.query_params.get("visits_page"), 1)
  interactions_page = _safe_int(request.query_params.get("interactions_page"), 1)
  per_page = _safe_int(request.query_params.get("per_page"), 10)
  cached_filter = request.query_params.get("cached_filter", "all")

  recent_visits = activity_logger.read_recent("visits.jsonl", limit=200)
  recent_interactions = activity_logger.read_recent("ai_interactions.jsonl", limit=200)

  filtered_interactions = recent_interactions
  if cached_filter == "cached":
    filtered_interactions = [event for event in recent_interactions if event.get("cached")]
  elif cached_filter == "uncached":
    filtered_interactions = [event for event in recent_interactions if not event.get("cached")]

  paged_visits = _paginate(recent_visits, visits_page, per_page)
  paged_interactions = _paginate(filtered_interactions, interactions_page, per_page)

  cached_count = sum(1 for event in recent_interactions if event.get("cached"))
  latency_values = [
    event.get("response_time_ms")
    for event in recent_interactions
    if isinstance(event.get("response_time_ms"), (int, float)) and event.get("response_time_ms") > 0
  ]
  average_latency = round(sum(latency_values) / len(latency_values), 1) if latency_values else None

  return templates.TemplateResponse(
    request,
    "admin_dashboard.html",
    {
      "summary": {
        "visit_count": len(recent_visits),
        "interaction_count": len(recent_interactions),
        "cached_count": cached_count,
        "average_latency_ms": average_latency,
      },
      "visits": paged_visits,
      "interactions": paged_interactions,
      "visits_page": visits_page,
      "interactions_page": interactions_page,
      "per_page": per_page,
      "cached_filter": cached_filter,
      "total_visits": len(recent_visits),
      "total_interactions": len(filtered_interactions),
    },
  )


@app.post("/api/ai-chat", response_model=ChatResponse)
async def ai_chat(payload: ChatRequest, request: Request):
  start = time.perf_counter()
  ip = _client_ip(request)

  if not rate_limiter.allow(ip):
    return JSONResponse(
      status_code=429,
      content={"error": "rate_limit", "message": "Too many requests. Try again tomorrow."},
    )

  cache_key = response_cache.key(payload.message, payload.voice)
  cached = response_cache.get(cache_key)
  if cached:
    activity_logger.log_interaction(
      ip=ip,
      message=payload.message,
      cached=True,
      response_sources=cached.get("sources", []),
      response_time_ms=0,
    )
    return ChatResponse(**{**cached, "cached": True})

  # Direct shortcuts — bypass RAG
  msg_lower = payload.message.lower()
  if _is_greeting(msg_lower):
    text = "Hi, I'm AI Akash. I can help with Akash's projects, backend work, experience, skills, or contact details."
    response = ChatResponse(text=text, audio_url=None, sources=[], cached=False)
    response_cache.set(cache_key, response.model_dump())
    activity_logger.log_interaction(ip=ip, message=payload.message, cached=False, response_sources=[], response_time_ms=round((time.perf_counter() - start) * 1000))
    return response
  if _is_small_talk(msg_lower):
    text = "I'm doing well, thanks. Ask me anything about Akash's projects, backend work, experience, skills, or contact details."
    response = ChatResponse(text=text, audio_url=None, sources=[], cached=False)
    response_cache.set(cache_key, response.model_dump())
    activity_logger.log_interaction(ip=ip, message=payload.message, cached=False, response_sources=[], response_time_ms=round((time.perf_counter() - start) * 1000))
    return response
  if _is_assistant_identity_question(msg_lower):
    text = "I'm AI Akash, the portfolio assistant for Akash Tomy. I answer questions about his projects, backend work, experience, skills, and contact details."
    response = ChatResponse(text=text, audio_url=None, sources=[], cached=False)
    response_cache.set(cache_key, response.model_dump())
    activity_logger.log_interaction(ip=ip, message=payload.message, cached=False, response_sources=[], response_time_ms=round((time.perf_counter() - start) * 1000))
    return response
  if _is_profile_identity_question(msg_lower):
    text = "Akash Tomy is a backend-focused full stack developer from Alappuzha, Kerala. He works with Django, FastAPI, Redis, Celery, databases, AWS, and React, and is especially focused on reliable backend systems and AI infrastructure."
    response = ChatResponse(text=text, audio_url=None, sources=["about"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    activity_logger.log_interaction(ip=ip, message=payload.message, cached=False, response_sources=["about"], response_time_ms=round((time.perf_counter() - start) * 1000))
    return response
  if _is_experience_question(msg_lower):
    text = "Akash Tomy has experience as a Python Full Stack Developer Intern at SMEC Technologies, with work around backend systems, caching, databases, AWS deployment, and React-based UI work."
    response = ChatResponse(text=text, audio_url=None, sources=["experience"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    activity_logger.log_interaction(ip=ip, message=payload.message, cached=False, response_sources=["experience"], response_time_ms=round((time.perf_counter() - start) * 1000))
    return response
  if _is_availability_question(msg_lower):
    text = "Akash is actively looking for full-time opportunities and can discuss availability directly. The easiest way to reach him is by email at akashtomy174@gmail.com or on LinkedIn at https://www.linkedin.com/in/akash-tomy-8b51a737b/."
    response = ChatResponse(text=text, audio_url=None, sources=["qa"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    activity_logger.log_interaction(ip=ip, message=payload.message, cached=False, response_sources=["qa"], response_time_ms=round((time.perf_counter() - start) * 1000))
    return response
  if any(kw in msg_lower for kw in ["cv", "resume", "curriculum", "download"]):
    text = "You can download Akash's resume here: https://akashtomy.com/AkashTomy-Resume.pdf"
    response = ChatResponse(text=text, audio_url=None, sources=["about"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    activity_logger.log_interaction(ip=ip, message=payload.message, cached=False, response_sources=["about"], response_time_ms=round((time.perf_counter() - start) * 1000))
    return response
  if any(kw in msg_lower for kw in ["github", "git hub", "linkedin", "linkedln", "linked in", "contact", "social", "reach", "email", "connect", "phone", "whatsapp"]):
    text = "You can reach Akash at: akashtomy174@gmail.com | LinkedIn: https://www.linkedin.com/in/akash-tomy-8b51a737b/ | GitHub: https://github.com/AkashTomy174"
    response = ChatResponse(text=text, audio_url=None, sources=["about"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    activity_logger.log_interaction(ip=ip, message=payload.message, cached=False, response_sources=["about"], response_time_ms=round((time.perf_counter() - start) * 1000))
    return response

  chunks = rag.search(payload.message, top_k=4)
  text = llm.answer(payload.message, chunks)
  audio_url = await tts.generate(text) if payload.voice else None
  sources = sorted({chunk.source for chunk in chunks})

  response = ChatResponse(text=text, audio_url=audio_url, sources=sources, cached=False)
  response_cache.set(cache_key, response.model_dump())

  elapsed_ms = round((time.perf_counter() - start) * 1000)
  activity_logger.log_interaction(
    ip=ip,
    message=payload.message,
    cached=False,
    response_sources=sources,
    response_time_ms=elapsed_ms,
  )
  logger.info(
    "chat ip=%s elapsed_ms=%s cache=false sources=%s",
    RateLimiter.ip_hash(ip),
    elapsed_ms,
    ",".join(sources),
  )
  return response


def _client_ip(request: Request) -> str:
  forwarded = request.headers.get("x-forwarded-for")
  if forwarded:
    return forwarded.split(",")[0].strip()
  return request.client.host if request.client else "unknown"


def _is_greeting(message: str) -> bool:
  return _matches_any_phrase(message, {"hi", "hii", "hello", "hey"})


def _is_small_talk(message: str) -> bool:
  return _matches_any_phrase(message, {"how are you", "hi how are you", "hello how are you", "hey how are you"})


def _is_assistant_identity_question(message: str) -> bool:
  return _matches_any_phrase(message, {"who are you", "what are you", "what is your name", "who am i talking to"})


def _is_profile_identity_question(message: str) -> bool:
  return _matches_any_phrase(message, {"who is akash", "who is akash tomy", "tell me about akash", "tell me about akash tomy"})


def _is_experience_question(message: str) -> bool:
  return _matches_any_phrase(message, {"experience", "work experience", "background", "career", "job history", "experiance", "expereince"})


def _is_availability_question(message: str) -> bool:
  return _matches_any_phrase(message, {"available", "availability", "free for a call", "free for call", "open to work", "open for work", "looking for work", "looking for a job"})


def _matches_any_phrase(message: str, phrases: set[str]) -> bool:
  normalized = _normalize_shortcut_message(message)
  if not normalized:
    return False

  if any(normalized == phrase for phrase in phrases):
    return True

  normalized_tokens = normalized.split()
  for phrase in phrases:
    if _matches_phrase(normalized, phrase):
      return True

    if len(normalized_tokens) <= 3:
      synonyms = _build_phrase_synonyms(phrase)
      if any(normalized == synonym for synonym in synonyms):
        return True

  return False


def _matches_phrase(normalized_message: str, phrase: str) -> bool:
  if normalized_message == phrase:
    return True

  message_tokens = normalized_message.split()
  expected_tokens = phrase.split()
  if not message_tokens or not expected_tokens:
    return False

  matches = 0
  for expected_token in expected_tokens:
    if any(_token_matches(message_token, expected_token) for message_token in message_tokens):
      matches += 1

  return matches >= max(1, math.ceil(len(expected_tokens) * 0.6))


def _build_phrase_synonyms(phrase: str) -> set[str]:
  tokens = phrase.split()
  synonyms: set[str] = set()
  for token in tokens:
    if token in {"available", "availability", "work", "job", "name", "akash", "you"}:
      synonyms.add(" ".join(tokens[:tokens.index(token)] + [token[:3]] + tokens[tokens.index(token) + 1:]))
  return synonyms


def _token_matches(message_token: str, expected_token: str) -> bool:
  if message_token == expected_token:
    return True
  if len(message_token) < 2 or len(expected_token) < 2:
    return False
  return _levenshtein_distance(message_token, expected_token) <= 1


def _levenshtein_distance(left: str, right: str) -> int:
  if left == right:
    return 0
  if not left:
    return len(right)
  if not right:
    return len(left)

  previous_row = list(range(len(right) + 1))
  for left_index, left_char in enumerate(left, start=1):
    current_row = [left_index]
    for right_index, right_char in enumerate(right, start=1):
      insertion_cost = current_row[right_index - 1] + 1
      deletion_cost = previous_row[right_index] + 1
      substitution_cost = previous_row[right_index - 1] + (left_char != right_char)
      current_row.append(min(insertion_cost, deletion_cost, substitution_cost))
    previous_row = current_row

  return previous_row[-1]


def _normalize_shortcut_message(message: str) -> str:
  lowered = message.lower()
  without_punctuation = re.sub(r"[^\w\s]", " ", lowered)
  return " ".join(without_punctuation.split())
