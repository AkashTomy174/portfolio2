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

Set `GEMINI_API_KEY` in `.env` to enable both vector indexing and generated answers. Without it, the API still starts and uses keyword retrieval as an offline fallback.

For fuller RAG retrieval on Linux/EC2, install:

```bash
pip install -r requirements-chroma.txt
```

On Windows with Python 3.13, Chroma may require Microsoft C++ Build Tools because `chroma-hnswlib` may not have a matching wheel.

When ChromaDB is installed and `GEMINI_API_KEY` is available, startup will:

1. read the curated chunks from `knowledge_base/akash.json`
2. generate embeddings with `GEMINI_EMBEDDING_MODEL`
3. upsert them into a persistent ChromaDB collection under `CHROMA_DIR`
4. answer queries with hybrid retrieval: vector similarity plus keyword/topic overlap

If ChromaDB or the embedding client is unavailable, the service logs a warning and keeps serving keyword retrieval.

## Retrieval Regression

Run the curated prompt set after changing retrieval logic or `knowledge_base/akash.json`:

```bash
cd backend
python evals/run_retrieval_regression.py
```

The prompt cases live in `evals/retrieval_regression.json`. Each case asserts the expected top retrieved topic so wording regressions are caught before they show up in the chat UI.

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
