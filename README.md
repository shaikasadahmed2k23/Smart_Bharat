# Smart Bharat — AI-Powered Civic Companion

Built for **DEVENGERS PromptWars 2026** — Round 4.

## Problem Statement
Build a GenAI-powered web platform that helps citizens access government
services, report public issues, and receive personalized assistance through
an intelligent AI companion — with multilingual support, transparency, and
accessibility at the core.

## Features
1. **Ask Sahayak (AI Chat)** — Gemini-powered assistant that answers citizen
   questions about government schemes, procedures, and civic issues in plain
   language, in the user's chosen language.
2. **Find a Service** — Keyword-matched recommendation engine over a curated
   catalog of common Indian public services (Aadhaar, PAN, Ration Card,
   Ayushman Bharat, PM-Kisan, Passport, Voter ID, etc.)
3. **Document Checklist** — Instantly look up exactly which documents are
   needed for a given service, plus a link to the official portal.
4. **Report & Track** — File civic complaints (roads, water, electricity,
   sanitation...) and track their status (submitted → in_review → resolved).
5. **Multilingual UI** — Full interface + AI responses available in
   **English, Hindi, and Telugu**.
6. **Accessibility** — Semantic HTML, ARIA live regions for chat, skip-to-content
   link, 44px minimum touch targets, visible focus rings, reduced-motion support,
   high-contrast color palette.

## Architecture
```
smart-bharat/
├── backend/          FastAPI + SQLite + Gemini
│   ├── main.py            API routes
│   ├── models.py          Pydantic schemas + validation
│   ├── database.py        SQLite connection/init
│   ├── civic_data.py       Curated services + document catalog
│   ├── gemini_client.py    Gemini wrapper (google-genai SDK)
│   └── test_main.py       Pytest suite (8 tests)
└── frontend/         React (Vite)
    ├── src/App.jsx         Tab navigation + language switcher
    ├── src/i18n.js         EN/HI/TE translation strings
    ├── src/api.js          Typed fetch wrapper
    └── src/components/     ChatCompanion, ServiceFinder,
                             DocumentChecklist, ComplaintTracker
```

## Why this design (Prompt Workflow / Strategy)
- **Deterministic core, GenAI where it adds value**: Service recommendation
  and document requirements are backed by a structured, testable data catalog
  rather than pure LLM guesswork — this avoids hallucination on facts like
  "which documents do I need," while Gemini is reserved for open-ended
  citizen queries where natural language understanding genuinely helps.
- **System prompt design**: The Gemini system instruction explicitly tells
  the model to (a) never request sensitive personal data, (b) admit
  uncertainty and redirect to official portals rather than guess, and
  (c) reply only in the requested language — directly serving the
  transparency and multilingual requirements of the problem statement.
- **Security**: CORS is restricted via env var, all inputs are validated with
  Pydantic (length limits, language whitelist, status enum), API key is
  never hardcoded (loaded from `.env`), SQL uses parameterized queries only.
- **Accessibility-first frontend**: built with ARIA roles, semantic
  landmarks, keyboard-navigable tabs, and a skip link from the start rather
  than retrofitted — since Accessibility carries High score impact.

## Local Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # add your GEMINI_API_KEY
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_BASE_URL if backend isn't on localhost:8000
npm run dev
```

## Testing
```bash
cd backend
pytest test_main.py -v
```

## Deployment
- **Backend**: Render / Railway (set `GEMINI_API_KEY` and `ALLOWED_ORIGINS` env vars)
- **Frontend**: Vercel / Netlify (set `VITE_API_BASE_URL` to the deployed backend URL)

## Tech Stack
FastAPI, SQLite, Gemini 2.5 Flash (google-genai SDK), React 19, Vite.
