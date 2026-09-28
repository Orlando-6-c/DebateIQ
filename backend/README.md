---
title: DebateIQ Pakistan API
emoji: 🇵🇰
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# DebateIQ Pakistan — Backend API

FastAPI + NLP pipeline. Deploy as a **Docker** Space on Hugging Face (free).

## Deploy (free)
1. Create a new Space → SDK: **Docker** → push this `backend/` folder.
2. In Space **Settings → Variables and secrets** add:
   - `JWT_SECRET` = any long random string
   - `FRONTEND_ORIGIN` = your Vercel URL (e.g. https://debateiq.vercel.app)
3. The first `/analyze` call downloads models (~1–2 min). CPU-only on free tier.

## Endpoints
`POST /auth/signup` · `POST /auth/login` · `GET /me` · `PUT /settings`
`POST /analyze/text` · `POST /analyze/audio` · `GET /limits` · `GET /health`

All `/analyze` and `/me`/`/settings` routes require `Authorization: Bearer <token>`.
