# DebateIQ Pakistan — AI Rhetorical Intelligence & Fact-Verification Platform

A free, deployable SaaS: **Next.js frontend (Vercel)** + **FastAPI/NLP backend (Hugging Face Spaces)**.

```
frontend/   Next.js site — landing, login/signup, analyze, scoring settings  → Vercel
backend/    FastAPI + NLP pipeline (auth, tier limits, scoring)              → HF Spaces (Docker)
src/        (legacy) all-in-one Gradio app for quick Colab demos
```

## Why this split
The ML models (torch, DeBERTa, Whisper) are several GB — too big for Vercel's
serverless limits. So the frontend lives on Vercel and calls the model backend
on a free Hugging Face Space. Both tiers are free.

## Free tier limits
- Text: 300 words per analysis
- Audio: first 60 seconds

---

## Deploy the backend (Hugging Face Spaces — free)
1. Create a Space → SDK **Docker**. Upload everything in `backend/`.
2. Space → Settings → Variables & secrets:
   - `JWT_SECRET` = long random string
   - `FRONTEND_ORIGIN` = your Vercel URL (add after step below)
3. Wait for build. Your API is at `https://<user>-<space>.hf.space`.
   First `/analyze` downloads models (~1–2 min, CPU-only on free tier).

## Deploy the frontend (Vercel — free)
1. Push `frontend/` to a GitHub repo, import into Vercel.
2. Vercel → Settings → Environment Variables:
   - `NEXT_PUBLIC_API_URL` = your HF Space URL
3. Deploy. Then set `FRONTEND_ORIGIN` on the Space to your Vercel URL (CORS).

## Run locally
```bash
# backend
cd backend && pip install -r requirements.txt && python -m spacy download en_core_web_sm
uvicorn main:app --port 7860
# frontend (new terminal)
cd frontend && npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:7860" > .env.local
npm run dev   # http://localhost:3000
```



## Plans & revenue (new)
Three tiers defined in `backend/src/tiers.py`:
- **Free** — 300 words / 60s audio, 25 analyses/month.
- **Pro** — 2,000 words / 300s audio, unlimited, Tournament Judge Mode, history.
- **Org** — 6,000 words / 900s audio, for MUN circuits & fact-check desks.

Usage is metered per user per month. `/billing/upgrade` is a **mock checkout**
(flips the tier instantly) — wire Stripe there before charging real money.

## Tournament Judge Mode (Pro/Org)
Create a tournament, paste each speaker's speech, and every speaker is scored and
ranked on a live leaderboard. Export results to CSV. Pages: `/judge`, `/judge/[id]`.
This is the B2B feature for debate societies and MUN organizers.

## Customizable scoring
Each user tunes how their credibility score is computed (Factual / Integrity /
Delivery weights + manipulation sensitivity) on the Scoring page. Saved per-account
and applied to every analysis.

## Upgrade paths (later, still mostly free)
- Persistent users → Supabase free Postgres (swap `src/auth.py`)
- Faster inference → paid HF Space GPU
- Real-time mic streaming, emotion timeline charts
