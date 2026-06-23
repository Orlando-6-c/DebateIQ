"""DebateIQ Pakistan — FastAPI backend.
Auth + tiers + usage metering + customizable scoring + Tournament Judge Mode.
"""
import os, time, tempfile, io, csv
import jwt
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src import auth, limits, tiers
from src.pipeline import analyze
from src.analyze import detect_speaker_name
from src.transcribe import transcribe

SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
TOKEN_TTL = 60 * 60 * 24 * 7

app = FastAPI(title="DebateIQ Pakistan API")
origins = os.environ.get("FRONTEND_ORIGIN", "*")
app.add_middleware(CORSMiddleware,
    allow_origins=[origins] if origins != "*" else ["*"],
    allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


class Creds(BaseModel):
    username: str
    password: str

class TextIn(BaseModel):
    text: str
    threshold: float = 0.4

class Settings(BaseModel):
    w_factual: int = 60
    w_integrity: int = 25
    w_delivery: int = 15
    manip_sensitivity: float = 1.0

class Upgrade(BaseModel):
    tier: str

class TournamentIn(BaseModel):
    name: str

class EntryIn(BaseModel):
    speaker: str = ""
    text: str


def make_token(u):
    return jwt.encode({"sub": u, "exp": int(time.time()) + TOKEN_TTL}, SECRET, algorithm="HS256")

def current_user(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    try:
        return jwt.decode(authorization[7:], SECRET, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")

def _public(u):
    t = tiers.get(u["tier"])
    return {"username": u["username"], "settings": u["settings"], "tier": u["tier"],
            "tier_label": t["label"],
            "limits": {"word_cap": t["word_cap"], "audio_sec": t["audio_sec"],
                       "monthly_analyses": t["monthly_analyses"], "judge_mode": t["judge_mode"]},
            "usage": {"used": u["usage_count"], "month": u["usage_month"]}}


@app.get("/health")
def health():
    return {"ok": True}

@app.get("/tiers")
def all_tiers():
    return tiers.TIERS

@app.post("/auth/signup")
def signup(c: Creds):
    ok, msg = auth.signup(c.username, c.password)
    if not ok:
        raise HTTPException(400, msg)
    return {"token": make_token(c.username.strip().lower()), "username": c.username.strip().lower()}

@app.post("/auth/login")
def login(c: Creds):
    ok, msg = auth.login(c.username, c.password)
    if not ok:
        raise HTTPException(401, msg)
    return {"token": make_token(c.username.strip().lower()), "username": c.username.strip().lower()}

@app.get("/me")
def me(user: str = Depends(current_user)):
    u = auth.get_user(user)
    if not u:
        raise HTTPException(404, "User not found")
    return _public(u)

@app.put("/settings")
def update_settings(s: Settings, user: str = Depends(current_user)):
    auth.save_settings(user, s.model_dump())
    return {"ok": True, "settings": s.model_dump()}

@app.post("/billing/upgrade")
def upgrade(body: Upgrade, user: str = Depends(current_user)):
    if body.tier not in tiers.TIERS:
        raise HTTPException(400, "Unknown tier")
    auth.set_tier(user, body.tier)  # mock checkout — wire Stripe here before charging
    return _public(auth.get_user(user))


def _run_analysis(user, text=None, audio_path=None, threshold=0.4):
    u = auth.get_user(user)
    t = tiers.get(u["tier"])
    allowed, used, limit = auth.check_and_bump_usage(user, t["monthly_analyses"])
    if not allowed:
        raise HTTPException(402, f"Free limit reached ({limit} analyses this month). Upgrade to Pro for unlimited.")
    if text is not None:
        text, original, truncated = limits.enforce_text(text, t["word_cap"])
        result = analyze(text=text, threshold=threshold, weights=u["settings"])
        result["meta"] = {"original_words": original, "truncated": truncated, "word_cap": t["word_cap"]}
    else:
        path, original_sec, trimmed = limits.enforce_audio(audio_path, t["audio_sec"])
        result = analyze(audio_path=path, threshold=threshold, weights=u["settings"])
        result["meta"] = {"original_seconds": round(original_sec or 0, 1), "trimmed": trimmed, "audio_cap_sec": t["audio_sec"]}
    result["meta"]["usage"] = {"used": used, "limit": limit, "tier": t["label"]}
    return result

@app.post("/analyze/text")
def analyze_text(body: TextIn, user: str = Depends(current_user)):
    return _run_analysis(user, text=body.text, threshold=body.threshold)

@app.post("/analyze/audio")
async def analyze_audio(file: UploadFile = File(...), threshold: float = 0.4,
                        user: str = Depends(current_user)):
    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    tmp = os.path.join(tempfile.gettempdir(), f"upload_{int(time.time())}{suffix}")
    with open(tmp, "wb") as f:
        f.write(await file.read())
    return _run_analysis(user, audio_path=tmp, threshold=threshold)


# ---------- Judge Mode (Pro/Org) ----------
def _require_judge(user):
    u = auth.get_user(user)
    if not tiers.get(u["tier"])["judge_mode"]:
        raise HTTPException(403, "Tournament Judge Mode is a Pro feature. Upgrade to unlock.")
    return u

@app.get("/tournaments")
def list_tournaments(user: str = Depends(current_user)):
    _require_judge(user)
    return auth.list_tournaments(user)

@app.post("/tournaments")
def create_tournament(body: TournamentIn, user: str = Depends(current_user)):
    _require_judge(user)
    tid = auth.create_tournament(user, body.name)
    return {"id": tid, "name": body.name.strip()}

@app.get("/tournaments/{tid}")
def get_tournament(tid: int, user: str = Depends(current_user)):
    _require_judge(user)
    t = auth.get_tournament(tid, user)
    if not t:
        raise HTTPException(404, "Tournament not found")
    return t

@app.post("/tournaments/{tid}/transcribe")
async def transcribe_entry(tid: int, file: UploadFile = File(...), user: str = Depends(current_user)):
    u = _require_judge(user)
    suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    tmp = os.path.join(tempfile.gettempdir(), f"jm_{int(time.time())}{suffix}")
    with open(tmp, "wb") as f:
        f.write(await file.read())
    path, dur, trimmed = limits.enforce_audio(tmp, tiers.get(u["tier"])["audio_sec"])
    text, _ = transcribe(path)
    return {"transcript": text, "suggested_name": detect_speaker_name(text) or "", "trimmed": trimmed}


@app.post("/tournaments/{tid}/entries")
def add_entry(tid: int, body: EntryIn, user: str = Depends(current_user)):
    u = _require_judge(user)
    text, _, _ = limits.enforce_text(body.text, tiers.get(u["tier"])["word_cap"])
    name = (body.speaker or "").strip() or (detect_speaker_name(text) or "")
    if not name:
        t = auth.get_tournament(tid, user)
        name = f"Speaker {(len(t['entries']) if t else 0) + 1}"
    result = analyze(text=text, weights=u["settings"])
    j = result["judge"]
    payload = {"counts": j["counts"], "summary": j["summary"],
               "avg_sources": j["avg_sources"], "subscores": j["subscores"]}
    if not auth.add_entry(tid, user, name, j["score"], payload):
        raise HTTPException(404, "Tournament not found")
    return {"ok": True, "speaker": name, "score": j["score"]}

@app.get("/tournaments/{tid}/export")
def export_tournament(tid: int, user: str = Depends(current_user)):
    _require_judge(user)
    t = auth.get_tournament(tid, user)
    if not t:
        raise HTTPException(404, "Tournament not found")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Rank", "Speaker", "Score", "Supported", "Disputed", "Likely False", "Insufficient"])
    for i, e in enumerate(t["entries"], 1):
        c = e.get("counts", {})
        w.writerow([i, e["speaker"], e["score"], c.get("supported", 0),
                    c.get("disputed", 0), c.get("false", 0), c.get("insufficient", 0)])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{t["name"]}_results.csv"'})
