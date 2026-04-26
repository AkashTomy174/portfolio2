import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
  value = os.getenv(name)
  if value is None:
    return default
  return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str, default: str) -> list[str]:
  return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


class Settings:
  openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
  openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gemini-1.5-flash")
  openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

  elevenlabs_api_key: str | None = os.getenv("ELEVENLABS_API_KEY")
  elevenlabs_voice_id: str | None = os.getenv("ELEVENLABS_VOICE_ID")
  enable_tts: bool = _bool("ENABLE_TTS", False)

  allowed_origins: list[str] = _csv("ALLOWED_ORIGINS", "http://localhost:5173,https://akashtomy.com")
  max_requests_per_ip: int = int(os.getenv("MAX_REQUESTS_PER_IP", "10"))
  rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "86400"))
  response_cache_max_items: int = int(os.getenv("RESPONSE_CACHE_MAX_ITEMS", "256"))

  chroma_dir: Path = (BASE_DIR / os.getenv("CHROMA_DIR", "./data/chroma")).resolve()
  audio_dir: Path = (BASE_DIR / os.getenv("AUDIO_DIR", "./data/audio")).resolve()
  knowledge_file: Path = BASE_DIR / "knowledge_base" / "akash.json"


settings = Settings()
