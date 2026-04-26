# Akash Tomy — Portfolio

Personal portfolio website with an AI-powered chat assistant built with React, Tailwind CSS, Framer Motion, and a FastAPI backend powered by Google Gemini.

Live: [akashtomy.com](https://akashtomy.com)

---

## Tech Stack

### Frontend
- React 19
- Tailwind CSS 4
- Framer Motion 12
- Vite

### Backend (AI Chat)
- FastAPI + Uvicorn
- Google Gemini (`gemini-2.0-flash-lite`)
- RAG with keyword search
- ElevenLabs TTS (optional)

### Infrastructure
- Frontend: Vercel
- Backend: AWS EC2 + Nginx
- SSL: Certbot (Let's Encrypt)
- CI/CD: GitHub Actions

---

## Getting Started

### Frontend

```bash
npm install
npm run dev
```

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in your API keys
uvicorn app.main:app --reload --port 8001
```

---

## Environment Variables

### Frontend (`.env.local`)

```
VITE_AI_CHAT_ENDPOINT=http://localhost:8001/api/ai-chat
VITE_AI_CHAT_VOICE=false
```

### Backend (`backend/.env`)

```
OPENAI_API_KEY=your-gemini-api-key
OPENAI_CHAT_MODEL=gemini-2.0-flash-lite
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

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

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

---

## Project Structure

```
├── src/
│   ├── components/
│   │   ├── HeroSection.jsx
│   │   ├── AboutSection.jsx
│   │   ├── SkillsSection.jsx
│   │   ├── ProjectsSection.jsx
│   │   ├── ContactSection.jsx
│   │   ├── NavBar.jsx
│   │   ├── AiChatWidget.jsx
│   │   ├── AnimatedBackground.jsx
│   │   ├── CustomCursor.jsx
│   │   └── Icons.jsx
│   ├── contexts/
│   │   └── MotionPrefsContext.js
│   ├── data/
│   │   ├── about.js
│   │   ├── projects.js
│   │   └── skills.js
│   ├── siteConfig.js
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   └── services/
│   │       ├── llm.py
│   │       ├── rag.py
│   │       ├── cache.py
│   │       ├── rate_limit.py
│   │       └── tts.py
│   ├── knowledge_base/
│   │   └── akash.json
│   ├── requirements.txt
│   └── .env.example
├── public/
│   └── AkashTomy-Resume.pdf     ← drop your CV here
└── .github/
    └── workflows/
        └── deploy.yml
```

---

## Updating Content

All personal data is in `src/data/` and `src/siteConfig.js`.

| File | What it controls |
|---|---|
| `src/siteConfig.js` | Name, email, GitHub, LinkedIn, site URL |
| `src/data/about.js` | Stats (42% query reduction, etc.) |
| `src/data/projects.js` | Project cards |
| `src/data/skills.js` | Skill categories and levels |
| `backend/knowledge_base/akash.json` | AI chatbot knowledge base |

---

## AI Chat Widget

The chat widget (`AiChatWidget.jsx`) connects to the FastAPI backend and answers recruiter questions about Akash using RAG + Gemini.

**Suggested prompts shown in widget:**
- What is EasyBuy and what did you build?
- What's your experience with Django and AWS?
- What makes you different from other developers?
- Are you open to full-time roles?
- What's your strongest technical skill?
- Can I download your CV or resume?

**To add more knowledge:** edit `backend/knowledge_base/akash.json` and restart the backend.

---

## CV / Resume

Drop `AkashTomy-Resume.pdf` into the `public/` folder. The download button in the hero section and the chatbot link will both work automatically.

---

## Deployment

### Frontend — Vercel
Push to `main` → Vercel auto-deploys.

Set environment variable in Vercel:
```
VITE_AI_CHAT_ENDPOINT = https://api.akashtomy.com/api/ai-chat
```

### Backend — AWS EC2
The GitHub Actions workflow (`.github/workflows/deploy.yml`) auto-deploys the backend on every push that changes `backend/`.

Required GitHub secrets:
| Secret | Value |
|---|---|
| `EC2_HOST` | EC2 public IP |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Contents of your `.pem` file |

### Nginx config (`/etc/nginx/sites-available/api.akashtomy.com`)
```nginx
location /api/ai-chat {
    proxy_pass http://127.0.0.1:8001;
    proxy_read_timeout 30s;
}

location /health {
    proxy_pass http://127.0.0.1:8001;
}
```

### Systemd service
```bash
sudo systemctl enable ai-akash
sudo systemctl start ai-akash
sudo systemctl status ai-akash
```
