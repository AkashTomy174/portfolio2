import logging
import re
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models import ChatRequest, ChatResponse, HealthResponse
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


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
  return HealthResponse(ok=True, rag_ready=rag.ready, tts_enabled=settings.enable_tts)


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
    return ChatResponse(**{**cached, "cached": True})

  # Direct shortcuts — bypass RAG
  msg_lower = payload.message.lower()
  if _is_greeting(msg_lower):
    text = "Hi, I'm AI Akash. I can help with Akash's projects, backend work, experience, skills, or contact details."
    response = ChatResponse(text=text, audio_url=None, sources=[], cached=False)
    response_cache.set(cache_key, response.model_dump())
    return response
  if _is_small_talk(msg_lower):
    text = "I'm doing well, thanks. Ask me anything about Akash's projects, backend work, experience, skills, or contact details."
    response = ChatResponse(text=text, audio_url=None, sources=[], cached=False)
    response_cache.set(cache_key, response.model_dump())
    return response
  if _is_assistant_identity_question(msg_lower):
    text = "I'm AI Akash, the portfolio assistant for Akash Tomy. I answer questions about his projects, backend work, experience, skills, and contact details."
    response = ChatResponse(text=text, audio_url=None, sources=[], cached=False)
    response_cache.set(cache_key, response.model_dump())
    return response
  if _is_profile_identity_question(msg_lower):
    text = "Akash Tomy is a backend-focused full stack developer from Alappuzha, Kerala. He works with Django, FastAPI, Redis, Celery, databases, AWS, and React, and is especially focused on reliable backend systems and AI infrastructure."
    response = ChatResponse(text=text, audio_url=None, sources=["about"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    return response
  if _is_availability_question(msg_lower):
    text = "Akash is actively looking for full-time opportunities and can discuss availability directly. The easiest way to reach him is by email at akashtomy174@gmail.com or on LinkedIn at https://www.linkedin.com/in/akash-tomy-8b51a737b/."
    response = ChatResponse(text=text, audio_url=None, sources=["qa"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    return response
  if any(kw in msg_lower for kw in ["cv", "resume", "curriculum", "download"]):
    text = "You can download Akash's resume here: https://akashtomy.com/AkashTomy-Resume.pdf"
    response = ChatResponse(text=text, audio_url=None, sources=["about"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    return response
  if any(kw in msg_lower for kw in ["github", "git hub", "linkedin", "linkedln", "linked in", "contact", "social", "reach", "email", "connect", "phone", "whatsapp"]):
    text = "You can reach Akash at: akashtomy174@gmail.com | LinkedIn: https://www.linkedin.com/in/akash-tomy-8b51a737b/ | GitHub: https://github.com/AkashTomy174"
    response = ChatResponse(text=text, audio_url=None, sources=["about"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    return response

  chunks = rag.search(payload.message, top_k=4)
  text = llm.answer(payload.message, chunks)
  audio_url = await tts.generate(text) if payload.voice else None
  sources = sorted({chunk.source for chunk in chunks})

  response = ChatResponse(text=text, audio_url=audio_url, sources=sources, cached=False)
  response_cache.set(cache_key, response.model_dump())

  elapsed_ms = round((time.perf_counter() - start) * 1000)
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
  normalized = _normalize_shortcut_message(message)
  greetings = {
    "hi",
    "hii",
    "hello",
    "hey",
  }
  return normalized in greetings


def _is_small_talk(message: str) -> bool:
  normalized = _normalize_shortcut_message(message)
  small_talk = {
    "how are you",
    "hi how are you",
    "hello how are you",
    "hey how are you",
  }
  return normalized in small_talk


def _is_assistant_identity_question(message: str) -> bool:
  normalized = _normalize_shortcut_message(message)
  identity_questions = {
    "who are you",
    "what are you",
    "what is your name",
    "who am i talking to",
  }
  return normalized in identity_questions


def _is_profile_identity_question(message: str) -> bool:
  normalized = _normalize_shortcut_message(message)
  profile_questions = {
    "who is akash",
    "who is akash tomy",
    "tell me about akash",
    "tell me about akash tomy",
  }
  return normalized in profile_questions


def _is_availability_question(message: str) -> bool:
  normalized = _normalize_shortcut_message(message)
  availability_phrases = {
    "available",
    "availability",
    "free for a call",
    "free for call",
    "open to work",
    "open for work",
    "looking for work",
    "looking for a job",
  }
  return any(phrase in normalized for phrase in availability_phrases)


def _normalize_shortcut_message(message: str) -> str:
  lowered = message.lower()
  without_punctuation = re.sub(r"[^\w\s]", " ", lowered)
  return " ".join(without_punctuation.split())
