from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
  message: str = Field(..., min_length=1, max_length=500)
  voice: bool = False


class ChatResponse(BaseModel):
  text: str
  audio_url: str | None = None
  sources: list[str] = []
  cached: bool = False


class HealthResponse(BaseModel):
  ok: bool
  rag_ready: bool
  tts_enabled: bool
