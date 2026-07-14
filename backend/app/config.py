from __future__ import annotations

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


def _int(name: str, default: int) -> int:
    """Read an integer env var with a clear error message on bad input."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(
            f"Environment variable {name}={raw!r} is not a valid integer "
            f"(expected an int, default is {default})."
        ) from None


class Settings:
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    gemini_fallback_api_key: str | None = os.getenv("GEMINI_FALLBACK_API_KEY")
    gemini_chat_model: str = os.getenv(
        "GEMINI_CHAT_MODEL",
        os.getenv("OPENAI_CHAT_MODEL", "gemini-2.0-flash-lite"),
    )
    gemini_embedding_model: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

    elevenlabs_api_key: str | None = os.getenv("ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str | None = os.getenv("ELEVENLABS_VOICE_ID")
    enable_tts: bool = _bool("ENABLE_TTS", False)

    allowed_origins: list[str] = _csv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,https://akashtomy.com,https://www.akashtomy.com,https://akashtomy.vercel.app,https://www.akashtomy.vercel.app",
    )
    max_requests_per_ip: int = _int("MAX_REQUESTS_PER_IP", 10)
    rate_limit_window_seconds: int = _int("RATE_LIMIT_WINDOW_SECONDS", 86400)
    response_cache_max_items: int = _int("RESPONSE_CACHE_MAX_ITEMS", 256)
    admin_access_token: str | None = os.getenv("ADMIN_ACCESS_TOKEN")
    cookie_secret: str = (
        os.getenv("ADMIN_COOKIE_SECRET")
        or os.getenv("ADMIN_ACCESS_TOKEN")
        or "dev-insecure-secret-change-me"
    )
    dev_mode: bool = _bool("DEV_MODE", False)
    # Salt for IP hashing in logs. Required in production (enforced at startup).
    # Generate: python -c "import secrets; print(secrets.token_hex(32))"
    ip_hash_salt: str = os.getenv("IP_HASH_SALT", "")

    chroma_dir: Path = (BASE_DIR / os.getenv("CHROMA_DIR", "./data/chroma")).resolve()
    audio_dir: Path = (BASE_DIR / os.getenv("AUDIO_DIR", "./data/audio")).resolve()
    knowledge_file: Path = BASE_DIR / "knowledge_base" / "akash.json"

    # Conversation memory
    redis_url: str | None = os.getenv("REDIS_URL") or None
    session_max_history: int = _int("SESSION_MAX_HISTORY", 6)
    session_ttl_seconds: int = _int("SESSION_TTL_SECONDS", 3600)


settings = Settings()
