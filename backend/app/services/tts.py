import hashlib
import logging
from pathlib import Path

import httpx

logger = logging.getLogger("ai-akash")


class TtsService:
  def __init__(
    self,
    enabled: bool,
    api_key: str | None,
    voice_id: str | None,
    audio_dir: Path,
  ) -> None:
    self.enabled = enabled
    self.api_key = api_key
    self.voice_id = voice_id
    self.audio_dir = audio_dir

  async def generate(self, text: str) -> str | None:
    if not self.enabled or not self.api_key or not self.voice_id or len(text) < 20:
      return None

    self.audio_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{hashlib.md5(text.encode('utf-8')).hexdigest()}.mp3"
    path = self.audio_dir / filename
    if path.exists():
      return f"/audio/{filename}"

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
    payload = {
      "text": text,
      "model_id": "eleven_multilingual_v2",
      "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
    }
    headers = {
      "xi-api-key": self.api_key,
      "accept": "audio/mpeg",
      "content-type": "application/json",
    }

    try:
      async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
      path.write_bytes(response.content)
      return f"/audio/{filename}"
    except Exception as exc:
      logger.warning("TTS generation failed: %s", exc)
      return None
