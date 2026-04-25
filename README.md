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
