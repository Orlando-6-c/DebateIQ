"""Auth + tier + usage + tournament storage (SQLite + salted PBKDF2).
Swap for Supabase/Postgres later — function signatures stay the same.
"""
import os, sqlite3, hashlib, json, time
from datetime import datetime, timezone

DB = os.path.join(os.path.dirname(__file__), "..", "users.db")
DEFAULT_SETTINGS = {"w_factual": 60, "w_integrity": 25, "w_delivery": 15,
                    "manip_sensitivity": 1.0}


def _conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY, pw_hash TEXT, salt TEXT, settings TEXT)""")
    # migrations: add columns if missing
    cols = {r[1] for r in c.execute("PRAGMA table_info(users)")}
    for name, default in [("tier", "'free'"), ("usage_count", "0"), ("usage_month", "''")]:
        if name not in cols:
            c.execute(f"ALTER TABLE users ADD COLUMN {name} {'TEXT' if name!='usage_count' else 'INTEGER'} DEFAULT {default}")
    c.execute("""CREATE TABLE IF NOT EXISTS tournaments(
        id INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT, name TEXT, created REAL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS entries(
        id INTEGER PRIMARY KEY AUTOINCREMENT, tournament_id INTEGER, speaker TEXT,
        score REAL, payload TEXT, created REAL)""")
    return c


def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 100_000).hex()


def signup(username, password):
    username = (username or "").strip().lower()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password or "") < 6:
        return False, "Password must be at least 6 characters."
    c = _conn()
    if c.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
        c.close(); return False, "Username already taken."
    salt = os.urandom(16).hex()
    c.execute("INSERT INTO users(username,pw_hash,salt,settings,tier,usage_count,usage_month) VALUES(?,?,?,?,?,?,?)",
              (username, _hash(password, salt), salt, json.dumps(DEFAULT_SETTINGS), "free", 0, ""))
    c.commit(); c.close()
    return True, f"Account created. Welcome, {username}!"


def login(username, password):
    username = (username or "").strip().lower()
    c = _conn()
    row = c.execute("SELECT pw_hash, salt FROM users WHERE username=?", (username,)).fetchone()
    c.close()
    if not row:
        return False, "No such user."
    if _hash(password, row[1]) != row[0]:
        return False, "Incorrect password."
    return True, f"Welcome back, {username}!"


def get_user(username):
    c = _conn()
    row = c.execute("SELECT settings, tier, usage_count, usage_month FROM users WHERE username=?",
                    ((username or "").lower(),)).fetchone()
    c.close()
    if not row:
        return None
    s = DEFAULT_SETTINGS.copy(); s.update(json.loads(row[0] or "{}"))
    return {"username": username, "settings": s, "tier": row[1] or "free",
            "usage_count": row[2] or 0, "usage_month": row[3] or ""}


def get_settings(username):
    u = get_user(username)
    return u["settings"] if u else DEFAULT_SETTINGS.copy()


def save_settings(username, settings):
    c = _conn()
    c.execute("UPDATE users SET settings=? WHERE username=?", (json.dumps(settings), (username or "").lower()))
    c.commit(); c.close()


def set_tier(username, tier):
    c = _conn()
    c.execute("UPDATE users SET tier=? WHERE username=?", (tier, (username or "").lower()))
    c.commit(); c.close()


def check_and_bump_usage(username, monthly_limit):
    """Reset on new month, block if over limit, else increment. Returns (allowed, used, limit)."""
    username = (username or "").lower()
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    c = _conn()
    row = c.execute("SELECT usage_count, usage_month FROM users WHERE username=?", (username,)).fetchone()
    used = (row[0] or 0) if row else 0
    if not row or row[1] != month:
        used = 0
    if monthly_limit is not None and used >= monthly_limit:
        c.close(); return False, used, monthly_limit
    used += 1
    c.execute("UPDATE users SET usage_count=?, usage_month=? WHERE username=?", (used, month, username))
    c.commit(); c.close()
    return True, used, monthly_limit


# ---------- tournaments ----------
def create_tournament(owner, name):
    c = _conn()
    cur = c.execute("INSERT INTO tournaments(owner,name,created) VALUES(?,?,?)",
                    ((owner or "").lower(), name.strip(), time.time()))
    c.commit(); tid = cur.lastrowid; c.close()
    return tid


def list_tournaments(owner):
    c = _conn()
    rows = c.execute("""SELECT t.id,t.name,t.created,COUNT(e.id)
        FROM tournaments t LEFT JOIN entries e ON e.tournament_id=t.id
        WHERE t.owner=? GROUP BY t.id ORDER BY t.created DESC""", ((owner or "").lower(),)).fetchall()
    c.close()
    return [{"id": r[0], "name": r[1], "created": r[2], "entries": r[3]} for r in rows]


def get_tournament(tid, owner):
    c = _conn()
    t = c.execute("SELECT id,name,created FROM tournaments WHERE id=? AND owner=?",
                  (tid, (owner or "").lower())).fetchone()
    if not t:
        c.close(); return None
    rows = c.execute("SELECT speaker,score,payload,created FROM entries WHERE tournament_id=? ORDER BY score DESC",
                     (tid,)).fetchall()
    c.close()
    entries = [{"speaker": r[0], "score": r[1], **json.loads(r[2] or "{}"), "created": r[3]} for r in rows]
    return {"id": t[0], "name": t[1], "created": t[2], "entries": entries}


def add_entry(tid, owner, speaker, score, payload):
    c = _conn()
    t = c.execute("SELECT 1 FROM tournaments WHERE id=? AND owner=?", (tid, (owner or "").lower())).fetchone()
    if not t:
        c.close(); return False
    c.execute("INSERT INTO entries(tournament_id,speaker,score,payload,created) VALUES(?,?,?,?,?)",
              (tid, speaker.strip(), score, json.dumps(payload), time.time()))
    c.commit(); c.close()
    return True
