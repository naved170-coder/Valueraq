"""Bot and spam checks: throwaway email domains, link-stuffed or copy-pasted messages, email confirmation,
an optional Cloudflare Turnstile challenge, and an email to the admins when blocks spike (a likely bot attack)."""
import hashlib
import hmac
import json
import re
import time
import urllib.parse
import urllib.request

from flask import current_app, request

from . import db

# Common throwaway inbox providers. Bots use them to make accounts in bulk.
DISPOSABLE = {
    "mailinator.com", "guerrillamail.com", "guerrillamail.net", "guerrillamail.org", "sharklasers.com",
    "grr.la", "10minutemail.com", "10minutemail.net", "tempmail.com", "temp-mail.org", "temp-mail.io",
    "tempmailo.com", "tempail.com", "throwawaymail.com", "yopmail.com", "yopmail.net", "trashmail.com",
    "trashmail.de", "getnada.com", "nada.email", "dispostable.com", "maildrop.cc", "mailnesia.com",
    "mintemail.com", "fakeinbox.com", "moakt.com", "emailondeck.com", "spamgourmet.com", "mohmal.com",
    "burnermail.io", "mailpoof.com", "discard.email", "tmail.ws", "tmpmail.org", "tmpmail.net",
    "1secmail.com", "1secmail.org", "1secmail.net", "spam4.me", "inboxkitten.com", "mytemp.email",
    "emailfake.com", "fakemail.net", "luxusmail.org", "minuteinbox.com", "tempinbox.com", "jetable.org",
    "mail-temp.com", "easytrashmail.com", "cuvox.de", "armyspy.com", "dayrep.com", "einrot.com",
    "fleckens.hu", "gustr.com", "jourrapide.com", "rhyta.com", "superrito.com", "teleworm.us",
}
LINK_RE = re.compile(r"https?://|www\.|\b[a-z0-9-]+\.(?:com|net|org|io|ru|xyz|top|biz|info|click|link)\b", re.I)
MAX_LINKS = 2
SPIKE_SIGNUPS_PER_HOUR = 25
SPIKE_BLOCKS_PER_HOUR = 60
VERIFY_MAX_AGE = 7 * 86400


def disposable(email):
    domain = (email or "").rsplit("@", 1)[-1].lower().strip()
    return domain in DISPOSABLE or any(domain.endswith("." + d) for d in DISPOSABLE)


def too_many_links(text):
    return len(LINK_RE.findall(text or "")) > MAX_LINKS


def repeated_message(user_id, text, table="inquiries", col="buyer_id", limit=3, window=3600):
    """True when this user already sent the same text `limit` times in the window: copy-paste spam."""
    body = (text or "").strip()[:4000]
    if not body:
        return False
    n = db.query(f"SELECT COUNT(*) n FROM {table} WHERE {col}=? AND message=? AND created_at>?",
                 (user_id, body, db.now() - window), one=True)["n"]
    return n >= limit


# ---------------------------------------------------------------- email confirmation
def _sig(uid, email, exp):
    key = current_app.config["SECRET_KEY"].encode()
    return hmac.new(key, f"email-verify|{uid}|{email}|{exp}".encode(), hashlib.sha256).hexdigest()[:32]


def verify_token(user):
    # Lowercase letters and digits only, so the site's lowercase-URL redirect can't break the link.
    exp = int(time.time()) + VERIFY_MAX_AGE
    return f"{user['id']}-{exp}-{_sig(user['id'], user['email'], exp)}"


def check_token(token):
    """Returns the user id the link belongs to, or None if it is broken, expired or for an old email."""
    try:
        uid, exp, sig = token.split("-")
        uid, exp = int(uid), int(exp)
    except ValueError:
        return None
    if exp < time.time():
        return None
    u = db.query("SELECT id, email FROM users WHERE id=?", (uid,), one=True)
    if not u or not hmac.compare_digest(sig, _sig(uid, u["email"], exp)):
        return None
    return u["id"]


def verify_url(user):
    return current_app.config["SITE_URL"] + f"/verify-email/{verify_token(user)}/"


def needs_verification(user):
    return bool(user) and current_app.config.get("REQUIRE_EMAIL_VERIFICATION", True) \
        and not user["email_verified_at"]


# ---------------------------------------------------------------- Cloudflare Turnstile (optional)
def turnstile_site_key():
    return current_app.config.get("TURNSTILE_SITE_KEY") or ""


def turnstile_ok():
    """Passes when Turnstile isn't set up. When it is, the form's token must check out with Cloudflare.
    If Cloudflare can't be reached, let the person through and log it, so real people aren't locked out."""
    secret = current_app.config.get("TURNSTILE_SECRET") or ""
    if not secret or not turnstile_site_key():
        return True
    token = request.form.get("cf-turnstile-response") or ""
    if not token:
        return False
    from .auth import client_ip
    body = urllib.parse.urlencode({"secret": secret, "response": token, "remoteip": client_ip()}).encode()
    try:
        with urllib.request.urlopen("https://challenges.cloudflare.com/turnstile/v0/siteverify", body, timeout=6) as r:
            return bool(json.loads(r.read()).get("success"))
    except Exception as e:  # network trouble: fail open
        current_app.logger.warning("turnstile check skipped: %s", e)
        return True


# ---------------------------------------------------------------- spike alert
def note_block(bucket):
    """Called whenever a rate limit blocks someone. Counts blocks and emails the admins (once an hour at most)
    when they jump, which usually means a bot is hammering the site."""
    try:
        now = int(time.time())
        db.execute("INSERT INTO rate_hits(bucket, k, ts) VALUES ('blocked', ?, ?)", (bucket.split(":")[0], now))
        n = db.query("SELECT COUNT(*) n FROM rate_hits WHERE bucket='blocked' AND ts>?", (now - 3600,), one=True)["n"]
        current_app.logger.warning("blocked by rate limit: %s (%d blocks in the last hour)", bucket, n)
        if n >= SPIKE_BLOCKS_PER_HOUR:
            alert("blocks", f"{n} requests were blocked in the last hour (latest: {bucket.split(':')[0]}).")
    except Exception as e:
        current_app.logger.error("block counter error: %s", e)


def check_signup_spike():
    n = db.query("SELECT COUNT(*) n FROM users WHERE created_at>?", (db.now() - 3600,), one=True)["n"]
    if n >= SPIKE_SIGNUPS_PER_HOUR:
        alert("signups", f"{n} accounts were created in the last hour. That is unusual and may be bots.")


def alert(kind, what):
    slot = f"guard:{kind}:" + time.strftime("%Y%m%d%H", time.gmtime())
    conn = db.get_db()
    cur = conn.execute("INSERT OR IGNORE INTO seo_alerts(day, sent_at) VALUES (?,?)", (slot, db.now()))
    conn.commit()
    if cur.rowcount:
        from . import mailer
        mailer.admin_bot_alert(what)
