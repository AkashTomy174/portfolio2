# AI Akash Backend

FastAPI backend for the portfolio chat widget.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8001
```

Set `OPENAI_API_KEY` in `.env` for real RAG + LLM responses. Without it, the API still starts and uses keyword retrieval as an offline fallback.

For production ChromaDB retrieval on Linux/EC2, install:

```bash
pip install -r requirements-chroma.txt
```

On Windows with Python 3.13, Chroma may require Microsoft C++ Build Tools because `chroma-hnswlib` may not have a matching wheel.

## API

`POST /api/ai-chat`

```json
{
  "message": "What is EasyBuy?",
  "voice": false
}
```

Response:

```json
{
  "text": "EasyBuy is Akash's full-stack e-commerce platform...",
  "audio_url": null,
  "sources": ["projects"],
  "cached": false
}
```

## Voice

Voice is disabled by default. To enable ElevenLabs:

```env
ENABLE_TTS=true
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
```

Audio files are cached in `backend/data/audio` and served from `/audio/{filename}`.
