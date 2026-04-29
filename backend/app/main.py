import logging
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
  openai_api_key=settings.openai_api_key,
  embedding_model=settings.openai_embedding_model,
)
llm = LlmService(api_key=settings.openai_api_key, model=settings.openai_chat_model)
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
  if any(kw in msg_lower for kw in ["cv", "resume", "curriculum", "download"]):
    text = "You can download Akash's resume here: https://akashtomy.com/AkashTomy-Resume.pdf"
    response = ChatResponse(text=text, audio_url=None, sources=["about"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    return response
  if any(kw in msg_lower for kw in ["github", "git hub", "linkedin", "linkedln", "linked in", "contact", "social", "reach", "email", "hire", "connect", "phone", "whatsapp"]):
    text = "You can reach Akash at: akashtomy174@gmail.com | LinkedIn: https://www.linkedin.com/in/akash-tomy-8b51a737b/ | GitHub: https://github.com/AkashTomy174"
    response = ChatResponse(text=text, audio_url=None, sources=["about"], cached=False)
    response_cache.set(cache_key, response.model_dump())
    return response

  chunks = rag.search(payload.message, top_k=3)
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
