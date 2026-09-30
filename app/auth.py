"""Accounts, sessions, CSRF, rate limiting and spam traps."""
import secrets
import time
from collections import defaultdict, deque
from functools import wraps

from flask import abort, current_app, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


# ---------------------------------------------------------------- users
def load_user():
    g.user = None
    uid = session.get("uid")
    if uid:
        u = db.query("SELECT * FROM users WHERE id = ?", (uid,), one=True)
        if u:
            g.user = u
            _expire_trial(u)


def _expire_trial(u):
    if u["plan"] == "trial" and u["trial_ends_at"] and u["trial_ends_at"] < db.now():
        db.execute("UPDATE users SET plan='free' WHERE id=?", (u["id"],))
        g.user = db.query("SELECT * FROM users WHERE id = ?", (u["id"],), one=True)


def is_premium(u=None):
    u = u if u is not None else g.get("user")
    if not u:
        return False
    if u["plan"] == "pro" and u["subscription_status"] in ("active", "trialing", "past_due"):
        return True
    if u["plan"] == "trial" and (u["trial_ends_at"] or 0) > db.now():
        return True
    return u["role"] == "admin"


def create_user(email, password, name=None):
    email = email.strip().lower()
    role = "admin" if email in current_app.config["ADMIN_EMAILS"] else "user"
    uid = db.execute(
        "INSERT INTO users(email, password_hash, name, role, created_at) VALUES (?,?,?,?,?)",
        (email, generate_password_hash(password), name, role, db.now()))
    return uid


def verify(email, password):
    u = db.query("SELECT * FROM users WHERE email = ?", (email.strip().lower(),), one=True)
    if u and check_password_hash(u["password_hash"], password):
        return u
    return None


def login_user(u):
    keep = session.get("last_valuation")  # a valuation run before signup/login survives it
    session.clear()
    if keep:
        session["last_valuation"] = keep
    session.permanent = True
    session["uid"] = u["id"]
    session["csrf"] = secrets.token_urlsafe(24)
    db.execute("UPDATE users SET last_login_at=? WHERE id=?", (db.now(), u["id"]))


def start_trial(u):
    if u["trial_used"]:
        return False
    days = current_app.config["TRIAL_DAYS"]
    db.execute("UPDATE users SET plan='trial', trial_used=1, trial_started_at=?, trial_ends_at=? WHERE id=?",
               (db.now(), db.now() + days * 86400, u["id"]))
    return True


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not g.get("user"):
            return redirect(url_for("account.login", next=request.full_path.rstrip("?")))
        return view(*a, **kw)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not g.get("user"):
            return redirect(url_for("account.login", next=request.path))
        if g.user["role"] != "admin":
            abort(404)  # don't reveal the admin area
        return view(*a, **kw)
    return wrapped


# ---------------------------------------------------------------- CSRF
def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]


def check_csrf():
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    if request.path.startswith("/api/stripe/webhook/"):
        return  # verified by signature instead
    if request.path in ("/api/events/", "/api/vitals/"):
        return  # anonymous beacons, no state change for the user
    if request.path.startswith(("/tools/result/", "/calculators/result/")):
        return  # stateless calculations; keeps tool pages cacheable (no per-user token in HTML)
    sent = request.form.get("csrf") or request.headers.get("X-CSRF-Token")
    if not sent or not secrets.compare_digest(sent, session.get("csrf", "")):
        abort(400, description="Your form session expired. Reload the page and try again.")


# ---------------------------------------------------------------- rate limiting
_hits = defaultdict(deque)


def rate_limited(bucket, limit, window_seconds):
    if current_app.config.get("TESTING") and not current_app.config.get("TEST_RATE_LIMITS"):
        return False
    ip = request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For", request.remote_addr or "")
    ip = ip.split(",")[0].strip()
    key = (bucket, ip)
    q = _hits[key]
    t = time.time()
    while q and q[0] < t - window_seconds:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(t)
    return False


def honeypot_tripped():
    """Hidden 'website' field must stay empty; also reject sub-2s submissions."""
    if request.form.get("company_website"):
        return True
    started = request.form.get("t0")
    if current_app.config.get("TESTING"):
        return False
    try:
        if started and time.time() - float(started) < 2:
            return True
    except ValueError:
        return True
    return False
