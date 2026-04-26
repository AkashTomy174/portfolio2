# Akash Tomy — Portfolio

Personal portfolio website built with React, Tailwind CSS, and Framer Motion.

Live: [akashtomy.com](https://akashtomy.com)

## Tech Stack

- React 19
- Tailwind CSS 4
- Framer Motion 12
- Vite

## Getting Started

```bash
npm install
npm run dev
```

## AI Akash Widget

The chat widget posts to `/api/ai-chat` by default. Override it locally with:

```bash
VITE_AI_CHAT_ENDPOINT=http://localhost:8001/api/ai-chat
VITE_AI_CHAT_VOICE=true
```

Voice requests are off by default so the backend can skip TTS costs until enabled.

## Project Structure

```
src/
├── components/
│   ├── HeroSection.jsx
│   ├── AboutSection.jsx
│   ├── SkillsSection.jsx
│   ├── ProjectsSection.jsx
│   ├── ContactSection.jsx
│   ├── NavBar.jsx
│   ├── AnimatedBackground.jsx
│   ├── CustomCursor.jsx
│   └── Icons.jsx
├── contexts/
│   └── MotionPrefsContext.js
├── data/
│   ├── about.js
│   ├── projects.js
│   └── skills.js
├── siteConfig.js
├── App.jsx
├── index.css
└── main.jsx
```

## Updating Content

All personal data is in `src/data/` and `src/siteConfig.js` — no need to touch components.

| File | What it controls |
|---|---|
| `src/siteConfig.js` | Name, email, GitHub, LinkedIn, site URL |
| `src/data/about.js` | Stats (42% query reduction, etc.) |
| `src/data/projects.js` | Project cards |
| `src/data/skills.js` | Skill categories and levels |
