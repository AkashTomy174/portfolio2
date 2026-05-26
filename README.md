# Akash Tomy Portfolio

Personal portfolio website for Akash Tomy. The project combines a polished React frontend with a FastAPI backend that powers an AI portfolio assistant named **AI Akash**.

The site is built to do more than show projects. It explains backend decisions, architecture tradeoffs, and production thinking around caching, payments, concurrency, queues, retrieval, and AI reliability.

Live site: `https://akashtomy.com`

## Project Overview

The application has two main parts:

1. **Frontend portfolio**
   - Presents profile, projects, skills, engineering notes, recruiter-fit content, and contact details.
   - Includes an interactive chat widget for recruiter-style questions.

2. **Backend AI service**
   - Answers questions about Akash using a curated knowledge base.
   - Uses deterministic shortcuts for common questions, hybrid retrieval for broader questions, Gemini for generation, optional ElevenLabs voice output, response caching, and per-IP rate limiting.

## Tech Stack

### Frontend

| Technology | Purpose |
| --- | --- |
| React 19 | Component-based UI |
| Vite | Development server and build tooling |
| Tailwind CSS 4 | Utility-first styling |
| Framer Motion | Motion and interaction |
| JavaScript | Application logic |

### Backend

| Technology | Purpose |
| --- | --- |
| FastAPI | HTTP API |
| Uvicorn | ASGI server |
| Google Gemini | Chat generation and embeddings |
| ChromaDB | Persistent vector storage |
| Pydantic | Request and response validation |
| ElevenLabs | Optional text-to-speech |
| Python | Backend implementation |

### Infrastructure

| Technology | Purpose |
| --- | --- |
| Vercel | Frontend hosting |
| AWS EC2 | Backend hosting |
| Nginx | Reverse proxy |
| systemd | Backend process management in production |
| GitHub Actions | Backend deployment automation |
| Let's Encrypt / Certbot | HTTPS certificates |

## Frontend Structure

```text
src/
  App.jsx
  main.jsx
  siteConfig.js
  index.css
  components/
  contexts/
  data/
```

Important frontend files:

| File | Responsibility |
| --- | --- |
| `src/App.jsx` | Main page composition, boot screen, scroll progress, lazy loading, easter egg, chat widget |
| `src/components/HeroSection.jsx` | Main identity and call-to-action section |
| `src/components/SystemArchitectureSection.jsx` | Visual system design explanation |
| `src/components/ProjectsSection.jsx` | Project case studies and engineering decisions |
| `src/components/AiChatWidget.jsx` | Chat UI that talks to the backend |
| `src/data/projects.js` | Project content |
| `src/data/skills.js` | Skills content |
| `src/siteConfig.js` | Contact links and site metadata |

## Backend Summary

The backend is a small AI system, not only a chat endpoint.

At a high level, a request follows this path:

```text
React chat widget
  -> FastAPI validation
  -> IP rate limit check
  -> LRU response cache check
  -> deterministic shortcut handling when possible
  -> RAG retrieval from curated knowledge
  -> Gemini answer generation
  -> optional ElevenLabs audio generation
  -> JSON response back to the frontend
```

For full backend details, see [`backend/README.md`](backend/README.md).

## Local Setup

### Frontend

```bash
npm install
npm run dev
```

### Backend

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

Install dependencies and run the API:

```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8001
```

For ChromaDB-based vector retrieval:

```bash
pip install -r requirements-chroma.txt
```

## Environment Variables

### Frontend: `.env.local`

```env
VITE_AI_CHAT_ENDPOINT=http://localhost:8001/api/ai-chat
VITE_AI_CHAT_VOICE=false
```

### Backend: `backend/.env`

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

## API Endpoints

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/health` | `GET` | Reports backend readiness |
| `/api/ai-chat` | `POST` | Returns AI Akash responses |
| `/audio/{filename}` | `GET` | Serves generated voice responses when enabled |

Example chat request:

```json
{
  "message": "What is EasyBuy?",
  "voice": false
}
```

Example response:

```json
{
  "text": "EasyBuy is Akash's full-stack e-commerce platform...",
  "audio_url": null,
  "sources": ["projects"],
  "cached": false
}
```

## Updating Content

| File | What it controls |
| --- | --- |
| `src/siteConfig.js` | Name, email, GitHub, LinkedIn, site URL |
| `src/data/about.js` | Portfolio metrics |
| `src/data/projects.js` | Project case study content |
| `src/data/skills.js` | Skills cards |
| `backend/knowledge_base/akash.json` | Chatbot knowledge chunks |

## Deployment

### Frontend

The frontend is deployed on Vercel.

Production frontend environment variable:

```env
VITE_AI_CHAT_ENDPOINT=https://api.akashtomy.com/api/ai-chat
```

### Backend

The backend is deployed to AWS EC2 behind Nginx. The GitHub Actions workflow in `.github/workflows/deploy.yml` deploys backend changes pushed to `main`.

Required GitHub secrets:

| Secret | Purpose |
| --- | --- |
| `EC2_HOST` | EC2 public IP |
| `EC2_USER` | SSH username |
| `EC2_SSH_KEY` | Private key contents |

## Why This Project Is Interesting

- It combines frontend polish with real backend systems work.
- The chatbot is grounded by curated retrieval instead of relying on unrestricted generation.
- The backend has graceful fallback behavior when vector search or Gemini is unavailable.
- It includes lightweight regression checks so retrieval and shortcut behavior can be tested after changes.
- The portfolio content itself is structured around engineering evidence, not only screenshots.
