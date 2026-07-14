from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# Allowed session_id characters: alphanumeric plus hyphen and underscore.
# Minimum 8 chars so IDs are never trivially guessable; maximum 128 chars
# enforced separately by Field.  Rejects spaces, newlines, Redis-special
# characters (: * ? [ ]), and null bytes.
_SESSION_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{8,128}$")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    voice: bool = False
    session_id: Optional[str] = Field(None, max_length=128)

    @field_validator("message")
    @classmethod
    def _message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be blank")
        return v  # return original so normalize_query handles whitespace itself

    @field_validator("session_id")
    @classmethod
    def _validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not _SESSION_ID_RE.match(v):
            raise ValueError(
                "session_id must be 8-128 characters containing only "
                "letters, digits, hyphens, or underscores"
            )
        return v


class ChatResponse(BaseModel):
    text: str
    audio_url: Optional[str] = None
    sources: list[str] = []
    cached: bool = False


class ComponentHealth(BaseModel):
    ok: bool
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    ok: bool
    rag_ready: bool
    tts_enabled: bool
    # Expanded component status
    vector_db: ComponentHealth = ComponentHealth(ok=False)
    llm: ComponentHealth = ComponentHealth(ok=False)
    cache: ComponentHealth = ComponentHealth(ok=False)
    memory: ComponentHealth = ComponentHealth(ok=False)


class HealthMinimalResponse(BaseModel):
    """Public minimal health response — no internal stack detail."""
    ok: bool
