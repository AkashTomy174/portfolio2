# AI Akash Backend

FastAPI backend for the **AI Akash** portfolio assistant.

This service answers recruiter-style questions about Akash Tomy using a curated knowledge base, retrieval logic, Gemini generation, caching, rate limiting, optional voice generation, and regression scripts for behavior checks.

## Tech Stack

| Technology | Purpose |
| --- | --- |
| FastAPI | API framework |
| Uvicorn | ASGI server |
| Pydantic | Request and response validation |
| Google Gemini | Chat completion and embedding generation |
| ChromaDB | Persistent vector collection |
| ElevenLabs | Optional text-to-speech |
| Python | Service implementation |

## Project Structure

```text
backend/
  app/
    main.py
    config.py
    models.py
    services/
      cache.py
      llm.py
      rag.py
      rate_limit.py
      tts.py
  knowledge_base/
    akash.json
  evals/
    retrieval_regression.json
    shortcut_regression.json
    run_retrieval_regression.py
    run_shortcut_regression.py
  requirements.txt
  requirements-chroma.txt
```

## Request Flow

`POST /api/ai-chat`

```text
1. Validate incoming request with Pydantic
2. Read client IP
3. Apply per-IP rate limit
4. Check the in-memory LRU response cache
5. Return deterministic shortcut answers for common intents when possible
6. Retrieve relevant knowledge chunks with RAG
7. Ask Gemini to generate a grounded answer from retrieved context
8. Optionally create voice audio with ElevenLabs
9. Return text, source labels, audio URL, and cache status
```

Example request:

```json
{
  "message": "How does the portfolio chatbot work?",
  "voice": false
}
```

Example response:

```json
{
  "text": "The AI Akash portfolio chatbot is a FastAPI backend connected to a React widget...",
  "audio_url": null,
  "sources": ["projects"],
  "cached": false
}
```

## Core Services

### `main.py`

[`app/main.py`](app/main.py) wires the whole service together:

- creates the RAG, LLM, TTS, cache, and rate-limit services
- initializes RAG during application startup
- exposes `/health`, `/api/ai-chat`, and `/audio/...`
- handles shortcut responses for common questions before invoking retrieval or generation

### `config.py`

[`app/config.py`](app/config.py) loads environment configuration:

- Gemini API settings
- ElevenLabs settings
- allowed CORS origins
- request-limit settings
- cache size
- Chroma and audio storage paths

### `models.py`

[`app/models.py`](app/models.py) defines Pydantic models:

- `ChatRequest`
- `ChatResponse`
- `HealthResponse`

The chat request is constrained to:

- non-empty message
- maximum length of 500 characters
- optional boolean `voice` flag

## Deterministic Shortcut Answers

Before running retrieval or calling Gemini, the backend detects common intents and returns fixed answers immediately.

Shortcut categories include:

- greetings
- small talk
- assistant identity
- profile identity
- availability
- resume download
- contact/social links

Why this exists:

- important recruiter questions stay consistent
- common requests are faster
- repeated simple questions do not spend model tokens
- important facts such as contact details are returned deterministically

The helper functions for this logic are in [`app/main.py`](app/main.py).

## Rate Limiting

Rate limiting is implemented in [`app/services/rate_limit.py`](app/services/rate_limit.py).

### How it works

1. The backend identifies the client IP.
2. It hashes the IP before storing it.
3. Each hashed IP keeps:
   - current request count
   - reset timestamp
4. If the request count reaches the configured maximum before the window resets, the API returns HTTP `429`.

Default configuration:

```env
MAX_REQUESTS_PER_IP=10
RATE_LIMIT_WINDOW_SECONDS=86400
```

That means each IP gets up to 10 requests per 24-hour window by default.

### Important behavior

- The limiter is in-memory.
- It is simple and lightweight for a small portfolio backend.
- Counts reset when the process restarts.
- In a larger multi-instance deployment, Redis or another shared store would be a better choice.

## Response Cache

Caching is implemented in [`app/services/cache.py`](app/services/cache.py).

### How it works

- The service normalizes the user message.
- It combines the normalized message with the `voice` flag.
- It hashes that pair into a cache key.
- Responses are stored in an LRU cache using `OrderedDict`.
- When the cache exceeds its configured size, the least recently used item is evicted.

Default configuration:

```env
RESPONSE_CACHE_MAX_ITEMS=256
```

### Why it exists

- avoids repeated Gemini calls for duplicate questions
- lowers latency
- reduces API cost
- marks repeated responses with `"cached": true`

Like the rate limiter, this cache is in-memory and process-local.

## RAG: Retrieval-Augmented Generation

RAG is implemented in [`app/services/rag.py`](app/services/rag.py).

The chatbot does not send the full knowledge base to the model on every request. Instead, it retrieves only the most relevant chunks from [`knowledge_base/akash.json`](knowledge_base/akash.json).

### Knowledge source

`akash.json` stores curated chunks such as:

- profile summary
- contact details
- education
- internship experience
- project descriptions
- EasyBuy details
- AI Project Judge details
- skills
- recruiter-fit answers

Each chunk contains:

- `id`
- `source`
- `topic`
- `text`

### Retrieval modes

#### 1. Keyword fallback mode

If no Gemini key is configured or ChromaDB is unavailable:

- the backend still loads the curated chunks
- it scores chunks using token overlap, metadata overlap, and phrase boosts
- it returns the highest scoring chunks

This keeps the assistant usable even without vector infrastructure.

#### 2. Hybrid retrieval mode

When Gemini embeddings and ChromaDB are available:

1. startup reads all curated chunks
2. Gemini creates embeddings
3. embeddings are upserted into a persistent ChromaDB collection
4. each query runs:
   - vector search
   - keyword/topic search
5. results are merged

Current weighting:

```text
70% vector similarity
30% keyword score
```

This hybrid approach combines:

- semantic matching from embeddings
- precision from explicit keywords and topics

### Query normalization

The service also rewrites certain user phrases before retrieval.

Examples:

- `"what is easybuy"` -> `"easybuy ecommerce django react aws"`
- `"how does the portfolio chatbot work"` -> `"portfolio chatbot rag fastapi gemini retrieval cache"`
- `"cloud tools"` -> `"aws nginx gunicorn github actions"`

This improves matching for natural recruiter phrasing.

## LLM Generation

Generation is implemented in [`app/services/llm.py`](app/services/llm.py).

### What Gemini receives

The LLM does **not** receive the entire knowledge base. It receives:

- the system prompt
- only the retrieved chunks
- the user question

The system prompt instructs the assistant to:

- answer only from provided context
- avoid inventing employers, links, credentials, or metrics
- stay concise and recruiter-friendly
- explicitly say when the answer is not available

### Fallback behavior

If Gemini is unavailable or fails:

- the service falls back to the best retrieved chunk
- if no chunk exists, it returns:

```text
I don't have that information - reach out to Akash directly.
```

That gives the assistant graceful degradation instead of total failure.

## Voice Output

Voice generation is implemented in [`app/services/tts.py`](app/services/tts.py).

It is disabled by default.

Enable it with:

```env
ENABLE_TTS=true
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
```

### How it works

1. Hash the answer text.
2. Use the hash as the audio filename.
3. Reuse an existing MP3 if already generated.
4. Otherwise call ElevenLabs.
5. Save the MP3 under `data/audio`.
6. Return `/audio/{filename}` to the frontend.

This keeps repeated spoken answers from being regenerated.

## Regression Checks

The backend includes lightweight regression scripts under [`evals/`](evals/).

### Retrieval regression

Run:

```bash
python evals/run_retrieval_regression.py
```

Or keyword-only mode:

```bash
python evals/run_retrieval_regression.py --keyword-only
```

Purpose:

- verify that prompts still retrieve the expected top topic
- catch knowledge-base or ranking changes that silently worsen answers

The test cases live in [`evals/retrieval_regression.json`](evals/retrieval_regression.json).

### Shortcut regression

Run:

```bash
python evals/run_shortcut_regression.py
```

Purpose:

- verify that greetings, contact questions, resume questions, and availability prompts still map to the expected deterministic shortcut

The test cases live in [`evals/shortcut_regression.json`](evals/shortcut_regression.json).

### Generation quality regression

Run:

```bash
python evals/run_generation_quality_regression.py
```

Purpose:

- verify that obviously truncated Gemini responses are detected before they are returned

The test cases live in [`evals/generation_quality_regression.json`](evals/generation_quality_regression.json).

## API Reference

### `GET /health`

Returns:

```json
{
  "ok": true,
  "rag_ready": true,
  "tts_enabled": false
}
```

### `POST /api/ai-chat`

Request body:

```json
{
  "message": "What is AI Project Judge?",
  "voice": false
}
```

Response body:

```json
{
  "text": "AI Project Judge is Akash's upcoming flagship engineering project...",
  "audio_url": null,
  "sources": ["projects"],
  "cached": false
}
```

### `GET /audio/{filename}`

Serves generated ElevenLabs MP3 files when TTS is enabled.

## Setup

```bash
cd backend
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install base dependencies:

```bash
pip install -r requirements.txt
```

Install optional ChromaDB dependencies:

```bash
pip install -r requirements-chroma.txt
```

Create environment file:

```bash
copy .env.example .env
```

Run the API:

```bash
uvicorn app.main:app --reload --port 8001
```

## Environment Variables

```env
GEMINI_API_KEY=your-gemini-api-key
GEMINI_FALLBACK_API_KEY=your-second-gemini-api-key
GEMINI_CHAT_MODEL=gemini-2.0-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
ENABLE_TTS=false

ALLOWED_ORIGINS=https://akashtomy.com,http://localhost:5173
MAX_REQUESTS_PER_IP=10
RATE_LIMIT_WINDOW_SECONDS=86400
RESPONSE_CACHE_MAX_ITEMS=256

CHROMA_DIR=./data/chroma
AUDIO_DIR=./data/audio
```

## Current Design Tradeoffs

- **In-memory cache and rate limiting** keep the service simple, but they are not shared across multiple backend instances.
- **Curated knowledge** improves answer control, but every major portfolio update should also update `knowledge_base/akash.json`.
- **Hybrid retrieval** improves relevance, but requires both vector and keyword behavior to stay healthy.
- **Regression scripts** are lightweight checks, not a full automated evaluation harness.

## When to Update What

| Change | File to update |
| --- | --- |
| Add or edit chatbot knowledge | `knowledge_base/akash.json` |
| Change shortcut behavior | `app/main.py` |
| Change retrieval ranking | `app/services/rag.py` |
| Change system prompt or generation behavior | `app/services/llm.py` |
| Change limits or storage paths | `app/config.py` |
| Add retrieval regression cases | `evals/retrieval_regression.json` |
| Add shortcut regression cases | `evals/shortcut_regression.json` |
