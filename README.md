# Akash Tomy Portfolio

Personal portfolio website for Akash Tomy. The project combines a polished React frontend with a FastAPI backend powering an AI portfolio assistant named **AI Akash**.

The site is designed to do more than display projects. It documents backend engineering decisions, architecture tradeoffs, production practices, and system design around caching, payments, concurrency, queues, retrieval, AI reliability, observability, and deployment automation.

Live site:

https://akashtomy.com


---

# Project Overview

The application consists of two main systems.

## Frontend Portfolio

The React frontend provides:

- Personal profile
- Engineering projects
- Technical skills
- Architecture explanations
- Recruiter-focused content
- Contact information
- Interactive AI assistant


## Backend AI Service

The backend is a production-oriented AI system that answers questions about Akash using a curated knowledge base.

It supports:

- Deterministic shortcuts for common questions
- Hybrid retrieval
- Gemini-powered generation
- Optional ElevenLabs voice output
- Response caching
- Rate limiting
- Conversation memory
- Observability
- Admin dashboard
- Security controls


---

# Why This Project Is Interesting

This project combines frontend polish with real backend engineering.

The AI assistant evolved beyond a simple chatbot into an operations-aware AI system with an admin dashboard, structured observability, metrics collection, security controls, and automated production deployment.

The system focuses on reliability, explainability, and maintainability rather than only generating responses.


---

# Tech Stack

## Frontend

| Technology | Purpose |
|-|-|
| React 19 | Component-based UI |
| Vite | Build tooling |
| Tailwind CSS 4 | Styling |
| Framer Motion | Animations and interactions |
| JavaScript | Application logic |


## Backend

| Technology | Purpose |
|-|-|
| FastAPI | API framework |
| Uvicorn | ASGI server |
| Python | Backend implementation |
| Google Gemini | Chat generation and embeddings |
| ChromaDB | Vector storage |
| Pydantic | Validation |
| ElevenLabs | Optional text-to-speech |
| Redis | Session/cache storage |


## Infrastructure

| Technology | Purpose |
|-|-|
| Vercel | Frontend hosting |
| AWS EC2 | Backend hosting |
| Docker | Backend containerization |
| Docker Compose | Container orchestration |
| Nginx | Reverse proxy |
| GitHub Actions | CI/CD automation |
| Let's Encrypt / Certbot | HTTPS certificates |


---

# System Architecture

High-level request flow:

```

React Chat Widget

```
    |
    v
```

FastAPI API

```
    |
    v
```

Request Validation

```
    |
    v
```

IP Rate Limiting

```
    |
    v
```

Response Cache

```
    |
    v
```

Intent Routing

```
    |
    v
```

Deterministic Shortcuts
|
|
v

Hybrid Retrieval (RAG)

```
    |
    v
```

Gemini Generation

```
    |
    v
```

Optional Voice Generation

```
    |
    v
```

Frontend Response

```


---

# Frontend Structure

```

src/

├── App.jsx
├── main.jsx
├── index.css
├── siteConfig.js

├── components/
│   ├── HeroSection.jsx
│   ├── SystemArchitectureSection.jsx
│   ├── ProjectsSection.jsx
│   ├── AiChatWidget.jsx
│   ├── AiPromptSection.jsx
│   ├── NowSection.jsx
│   ├── EngineeringNotesSection.jsx
│   ├── RecruiterFitSection.jsx
│   └── NotFoundPage.jsx

├── contexts/

└── data/
├── projects.js
├── skills.js
└── about.js

```


Frontend features:

- Lazy-loaded components
- ErrorBoundary handling
- Scroll progress indicator
- Deferred rendering
- Konami-code easter egg
- Centralized configuration using `siteConfig.js`
- Structured content using `data/`


---

# Backend Architecture

The backend is not only a chat endpoint. It contains multiple production components.


## Intent Routing

`intents.py`

Responsibilities:

- Query classification
- Alias matching
- Similarity policies
- Route validation during startup
- MatchResult telemetry


Features:

- Alias sets for supported questions
- Startup validation using `validate_routes()`
- Routing metrics collection


---

## Retrieval System

The AI assistant uses curated retrieval.

Flow:

```

User Question

```
  |
```

Query Processing

```
  |
```

Hybrid Retrieval

```
  |
```

Relevant Knowledge Chunks

```
  |
```

Gemini Generation

```


---

## Conversation Memory

Supports multiple storage strategies:

```

Memory Factory

```
  |
```

---

|               |
v               v

InMemory       Redis
SessionStore   SessionStore

```


Features:

- Optional `session_id`
- Session TTL
- Configurable history size
- Redis-backed persistence


---

## Observability

The backend includes operational monitoring.

Features:

- Structured JSON logging
- Request-level telemetry
- MetricsCollector
- Latency tracking
- p95/p99 measurements
- Prometheus-compatible metrics


Metrics endpoints:

```

/metrics
/metrics/json

```

These endpoints are admin-protected and should not be publicly scraped without authentication.


---

## Admin Dashboard

Admin features:

- Cookie-based authentication
- Activity monitoring
- Metrics visualization
- Security controls


Routes:

```

/admin
/admin/activity

```


---

# Security

Production security controls:

## IP Hashing

Production requires:

```

IP_HASH_SALT=your-secret-here

````

IP addresses are hashed before storage.


## Trusted Proxy Handling

`CF-Connecting-IP` is only trusted when requests originate from loopback infrastructure through Nginx.

This prevents client IP spoofing.


## Admin Security

Implemented:

- Cookie-based sessions
- Brute-force login protection
- HMAC constant-time token comparison
- Protected metrics endpoints


---

# Environment Variables

## Frontend

`.env.local`

```env
VITE_AI_CHAT_ENDPOINT=your-api-endpoint
VITE_AI_CHAT_VOICE=your-setting
````

## Backend

`backend/.env`

```env
GEMINI_API_KEY=your-secret-here
GEMINI_FALLBACK_API_KEY=your-secret-here

GEMINI_CHAT_MODEL=your-model
GEMINI_EMBEDDING_MODEL=your-model


ELEVENLABS_API_KEY=your-secret-here
ELEVENLABS_VOICE_ID=your-secret-here

ENABLE_TTS=your-setting


ALLOWED_ORIGINS=your-origins


MAX_REQUESTS_PER_IP=your-number
RATE_LIMIT_WINDOW_SECONDS=your-number

RESPONSE_CACHE_MAX_ITEMS=your-number


CHROMA_DIR=your-path
AUDIO_DIR=your-path


ADMIN_ACCESS_TOKEN=your-secret-here
ADMIN_COOKIE_SECRET=your-secret-here
IP_HASH_SALT=your-secret-here


REDIS_URL=your-redis-url

SESSION_MAX_HISTORY=your-number
SESSION_TTL_SECONDS=your-number


DEV_MODE=your-setting
```

Never commit real credentials.

---

# API Reference

| Endpoint            | Method | Purpose                       |
| ------------------- | ------ | ----------------------------- |
| `/health`           | GET    | Basic health check            |
| `/health/detailed`  | GET    | Authenticated detailed health |
| `/api/ai-chat`      | POST   | AI chat endpoint              |
| `/audio/{filename}` | GET    | Voice output                  |
| `/admin/login`      | GET    | Admin login page              |
| `/admin/login`      | POST   | Admin authentication          |
| `/admin/logout`     | GET    | Logout                        |
| `/admin`            | GET    | Admin dashboard               |
| `/admin/activity`   | GET    | Activity logs                 |
| `/metrics`          | GET    | Admin protected metrics       |
| `/metrics/json`     | GET    | JSON metrics                  |

Example request:

```json
{
  "message": "What is EasyBuy?",
  "voice": false,
  "session_id": "optional-session-id"
}
```

Example response:

```json
{
  "text": "EasyBuy is Akash's full-stack e-commerce platform",
  "audio_url": null,
  "sources": [
    "projects"
  ],
  "cached": false
}
```

---

# Local Setup

## Frontend

```bash
npm install
npm run dev
```

## Backend

```bash
cd backend

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8001
```

For ChromaDB:

```bash
pip install -r requirements-chroma.txt
```

---

# Deployment

## Production Architecture

```
GitHub Push

      |

GitHub Actions

      |

SSH into EC2

      |

Docker Compose Build

      |

FastAPI Container

      |

Nginx Reverse Proxy

      |

api.akashtomy.com
```

## Deployment Workflow

The deployment pipeline:

1. GitHub Actions triggers on `main`
2. Connects to EC2
3. Updates repository
4. Runs Docker Compose deployment
5. Performs health validation

Deployment command:

```bash
docker compose up -d --build
```

Health validation:

* Polls `/health`
* Retries 15 times
* Uses curl checks
* On failure:

  * Runs `docker compose ps`
  * Dumps container logs
  * Fails deployment

Required GitHub secrets:

| Secret      | Purpose         |
| ----------- | --------------- |
| EC2_HOST    | EC2 address     |
| EC2_USER    | SSH username    |
| EC2_SSH_KEY | SSH private key |

---

# Updating Content

| File                              | Purpose               |
| --------------------------------- | --------------------- |
| src/siteConfig.js                 | Site metadata         |
| src/data/about.js                 | Portfolio information |
| src/data/projects.js              | Project content       |
| src/data/skills.js                | Skills                |
| backend/knowledge_base/akash.json | AI knowledge base     |

---

# When to Update What

## intents.py

Update when:

* Adding new query types
* Adding aliases
* Changing routing logic

## observability.py

Update when:

* Adding metrics
* Changing telemetry

## memory.py

Update when:

* Changing session storage
* Updating TTL logic

## admin_auth.py

Update when:

* Changing authentication
* Updating admin security

## Query Aliases

Update when:

* New user questions appear
* Intent matching needs refinement

---

# License

Personal portfolio project.

```

