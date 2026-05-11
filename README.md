# Akash Tomy - Portfolio

Personal portfolio website for Akash Tomy, built with React, Tailwind CSS, Framer Motion, and a FastAPI backend for the AI portfolio assistant.

Live: [akashtomy.com](https://akashtomy.com)

---

## Tech Stack

### Frontend
- React 19
- Tailwind CSS 4
- Framer Motion 12
- Vite

### Backend
- FastAPI + Uvicorn
- Google Gemini (`gemini-2.0-flash-lite`)
- RAG with keyword search
- Optional ElevenLabs TTS
- Response cache and IP rate limiting

### Infrastructure
- Frontend: Vercel
- Backend: AWS EC2 + Nginx
- SSL: Certbot / Let's Encrypt
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
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

On Windows, activate the virtual environment with:

```powershell
.venv\Scripts\activate
```

---

## Environment Variables

### Frontend (`.env.local`)

```env
VITE_AI_CHAT_ENDPOINT=http://localhost:8001/api/ai-chat
VITE_AI_CHAT_VOICE=false
```

### Backend (`backend/.env`)

```env
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

---

## Project Structure

```text
src/
  components/
    HeroSection.jsx
    AboutSection.jsx
    SkillsSection.jsx
    ProjectsSection.jsx
    AiPromptSection.jsx
    ContactSection.jsx
    NavBar.jsx
    AiChatWidget.jsx
    AnimatedBackground.jsx
    CustomCursor.jsx
    Icons.jsx
  contexts/
    MotionPrefsContext.js
  data/
    about.js
    projects.js
    skills.js
  siteConfig.js
  App.jsx
  index.css
  main.jsx
backend/
  app/
    main.py
    config.py
    models.py
    services/
      llm.py
      rag.py
      cache.py
      rate_limit.py
      tts.py
  knowledge_base/
    akash.json
  requirements.txt
public/
  AkashTomy-Resume.pdf
.github/
  workflows/
    deploy.yml
```

---

## Updating Content

| File | What it controls |
| --- | --- |
| `src/siteConfig.js` | Name, email, GitHub, LinkedIn, site URL |
| `src/data/about.js` | Proof metrics |
| `src/data/projects.js` | EasyBuy case study content |
| `src/data/skills.js` | Capability cards |
| `backend/knowledge_base/akash.json` | AI chatbot knowledge base |

---

## AI Chat Widget

The chat widget in `src/components/AiChatWidget.jsx` connects to the FastAPI backend and answers recruiter questions about Akash using the local knowledge base plus Gemini.

The redesign also includes `src/components/AiPromptSection.jsx`, which opens the same chat widget through a browser event:

```js
window.dispatchEvent(new CustomEvent('open-ai-akash'));
```

To add more knowledge, edit `backend/knowledge_base/akash.json` and restart the backend.

---

## CV / Resume

Place `AkashTomy-Resume.pdf` in the `public/` folder. The download button in the hero section and the chatbot responses can link to it.

---

## Deployment

### Frontend - Vercel

Push to `main` and Vercel auto-deploys.

Set this environment variable in Vercel:

```env
VITE_AI_CHAT_ENDPOINT=https://api.akashtomy.com/api/ai-chat
```

### Backend - AWS EC2

The GitHub Actions workflow in `.github/workflows/deploy.yml` can deploy the backend when files under `backend/` change.

Required GitHub secrets:

| Secret | Value |
| --- | --- |
| `EC2_HOST` | EC2 public IP |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Contents of your `.pem` file |

Example Nginx routes:

```nginx
location /api/ai-chat {
    proxy_pass http://127.0.0.1:8001;
    proxy_read_timeout 30s;
}

location /health {
    proxy_pass http://127.0.0.1:8001;
}
```

Example systemd commands:

```bash
sudo systemctl enable ai-akash
sudo systemctl start ai-akash
sudo systemctl status ai-akash
```
