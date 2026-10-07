"""Automatic Google Search Console connection.

The owner creates a Google "service account", adds its email address as a user of the
Search Console property, and pastes its key file into the hosting settings as
GSC_SERVICE_ACCOUNT_JSON. From then on the website fetches the search figures itself once
a day (clicks, impressions, searches, pages, position) and submits the sitemap.

No password is involved and the key never leaves the hosting settings. Google's figures
arrive two to three days late; that delay is Google's, not ours.
"""
import base64
import datetime
import json
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from flask import current_app

from . import db

SCOPE = "https://www.googleapis.com/auth/webmasters"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/webmasters/v3"
DAYS = 28
KEEP_DAYS = 480


class GscError(Exception):
    pass


def _key():
    raw = (current_app.config.get("GSC_SERVICE_ACCOUNT_JSON") or "").strip()
    if not raw:
        return None
    for attempt in (lambda: raw, lambda: base64.b64decode(raw).decode()):
        try:
            info = json.loads(attempt())
            if info.get("client_email") and info.get("private_key"):
                return info
        except Exception:
            continue
    raise GscError("The key in GSC_SERVICE_ACCOUNT_JSON could not be read. Paste the whole contents of the key file.")


def configured():
    return bool((current_app.config.get("GSC_SERVICE_ACCOUNT_JSON") or "").strip())


def service_email():
    try:
        k = _key()
        return k["client_email"] if k else None
    except GscError:
        return None


def _b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def _access_token(info, http):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    now = int(time.time())
    head = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = _b64(json.dumps({"iss": info["client_email"], "scope": SCOPE, "aud": TOKEN_URL, "iat": now, "exp": now + 3000}).encode())
    try:
        key = serialization.load_pem_private_key(info["private_key"].encode(), password=None)
    except Exception:
        raise GscError("The private key inside the key file is damaged. Download a new key file from Google.")
    sig = key.sign(head + b"." + claim, padding.PKCS1v15(), hashes.SHA256())
    body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                   "assertion": (head + b"." + claim + b"." + _b64(sig)).decode()}).encode()
    out = http("POST", TOKEN_URL, body, {"Content-Type": "application/x-www-form-urlencoded"})
    if "access_token" not in out:
        raise GscError("Google refused the key. Check that the Search Console API is switched on for the Google project.")
    return out["access_token"]


def _http(method, url, body=None, headers=None):
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read()).get("error", {})
            detail = detail.get("message") if isinstance(detail, dict) else str(detail)
        except Exception:
            pass
        raise GscError(f"Google answered {e.code}: {detail or e.reason}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise GscError(f"Google could not be reached: {e}")


def _pick_site(sites, host):
    """Choose the Search Console property for this website from the ones the key can see."""
    bare = host[4:] if host.startswith("www.") else host
    wanted = [f"sc-domain:{bare}", f"https://{host}/", f"https://{bare}/", f"http://{host}/"]
    have = {s.get("siteUrl"): s.get("permissionLevel") for s in sites}
    for w in wanted:
        if w in have and have[w] != "siteUnverifiedUser":
            return w, have[w]
    return None, None


def fetch(http=None, today=None):
    """Pull the latest figures from Google and store them. Returns the status dict. Raises GscError."""
    http = http or _http
    info = _key()
    if not info:
        raise GscError("Not connected yet: GSC_SERVICE_ACCOUNT_JSON is empty.")
    token = _access_token(info, http)
    auth = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    host = current_app.config["SITE_URL"].split("://", 1)[-1]
    site, level = _pick_site(http("GET", f"{API}/sites", None, auth).get("siteEntry") or [], host)
    if not site:
        raise GscError(f"The key works, but it has not been added to the Search Console property for {host}. In Search "
                       f"Console open Settings, Users and permissions, Add user, and add {info['client_email']}.")
    q = urllib.parse.quote(site, safe="")
    end = (today or datetime.date.today()) - datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=DAYS - 1)

    def query(dimension, limit, s=start):
        body = json.dumps({"startDate": s.isoformat(), "endDate": end.isoformat(), "dimensions": [dimension],
                           "rowLimit": limit, "dataState": "all"}).encode()
        return http("POST", f"{API}/sites/{q}/searchAnalytics/query", body, auth).get("rows") or []

    days = query("date", 500, end - datetime.timedelta(days=89))
    queries = query("query", 500)
    pages = query("page", 500)

    sitemap_note = ""
    sitemap_url = current_app.config["SITE_URL"] + "/sitemap.xml"
    try:
        known = [s.get("path") for s in http("GET", f"{API}/sites/{q}/sitemaps", None, auth).get("sitemap") or []]
        if sitemap_url in known:
            sitemap_note = "Sitemap is registered with Google."
        elif level in ("siteOwner", "siteFullUser"):
            http("PUT", f"{API}/sites/{q}/sitemaps/{urllib.parse.quote(sitemap_url, safe='')}", b"", auth)
            sitemap_note = "Sitemap submitted to Google automatically."
        else:
            sitemap_note = "Sitemap is not registered yet; give the key Full permission so it can be submitted automatically."
    except GscError as e:
        sitemap_note = f"Sitemap check failed: {e}"

    site_url = current_app.config["SITE_URL"]
    conn = db.get_db()
    conn.execute("DELETE FROM gsc_rows WHERE kind IN ('query','page')")
    rows = [("day", r["keys"][0], r.get("clicks", 0), r.get("impressions", 0), r.get("ctr", 0), r.get("position", 0)) for r in days]
    rows += [("query", r["keys"][0][:300], r.get("clicks", 0), r.get("impressions", 0), r.get("ctr", 0), r.get("position", 0)) for r in queries]
    for r in pages:
        path = r["keys"][0]
        path = path[len(site_url):] or "/" if path.startswith(site_url) else path
        rows.append(("page", path[:300], r.get("clicks", 0), r.get("impressions", 0), r.get("ctr", 0), r.get("position", 0)))
    conn.executemany("INSERT INTO gsc_rows(kind, key, clicks, impressions, ctr, position) VALUES (?,?,?,?,?,?) "
                     "ON CONFLICT(kind, key) DO UPDATE SET clicks=excluded.clicks, impressions=excluded.impressions, "
                     "ctr=excluded.ctr, position=excluded.position", rows)
    conn.execute("DELETE FROM gsc_rows WHERE kind='day' AND key < ?",
                 ((end - datetime.timedelta(days=KEEP_DAYS)).isoformat(),))
    conn.commit()
    return _save_status(ok=True, site=site, level=level, note=sitemap_note, period=f"{start.isoformat()} to {end.isoformat()}")


def _save_status(ok, error="", **extra):
    prev = status() or {}
    data = dict(prev, checked_at=db.now(), ok=bool(ok), error=error, **extra)
    if ok:
        data["last_ok_at"] = db.now()
    conn = db.get_db()
    conn.execute("INSERT INTO gsc_rows(kind, key, clicks, impressions, ctr, position, extra) VALUES ('status','status',0,0,0,0,?) "
                 "ON CONFLICT(kind, key) DO UPDATE SET extra=excluded.extra", (json.dumps(data),))
    conn.commit()
    return data


def status():
    r = db.query("SELECT extra FROM gsc_rows WHERE kind='status' AND key='status'", one=True)
    try:
        return json.loads(r["extra"]) if r and r["extra"] else None
    except ValueError:
        return None


def run(http=None):
    """Fetch and never raise; the outcome is stored for the admin page."""
    try:
        return fetch(http=http)
    except GscError as e:
        current_app.logger.warning("search console: %s", e)
        return _save_status(ok=False, error=str(e))
    except Exception as e:  # never let a scheduler thread die on this
        current_app.logger.error("search console unexpected error: %s", e)
        return _save_status(ok=False, error="Unexpected error; see Admin, Errors.")


def summary(days=28):
    """Figures for the admin page and for the automatic reports."""
    rows = db.query("SELECT key, clicks, impressions, position FROM gsc_rows WHERE kind='day' ORDER BY key DESC")

    def total(part):
        clicks = sum(r["clicks"] for r in part)
        imps = sum(r["impressions"] for r in part)
        pos = (sum(r["position"] * r["impressions"] for r in part) / imps) if imps else None
        return dict(clicks=int(clicks), impressions=int(imps), ctr=round(clicks / imps * 100, 2) if imps else None,
                    position=round(pos, 1) if pos else None, days=len(part))
    top = lambda kind, n: [dict(key=r["key"], clicks=int(r["clicks"]), impressions=int(r["impressions"]),
                                position=round(r["position"], 1)) for r in db.query(
        "SELECT key, clicks, impressions, position FROM gsc_rows WHERE kind=? ORDER BY clicks DESC, impressions DESC LIMIT ?", (kind, n))]
    return dict(status=status(), last=total(rows[:days]), previous=total(rows[days:days * 2]),
                daily=[dict(date=r["key"], clicks=int(r["clicks"]), impressions=int(r["impressions"])) for r in rows[:days]][::-1],
                queries=top("query", 100), pages=top("page", 100),
                pages_with_impressions=db.query("SELECT COUNT(*) n FROM gsc_rows WHERE kind='page'", one=True)["n"])


def feed_token():
    return current_app.config.get("SEO_FEED_TOKEN") or ""


def feed_ok(token):
    real = feed_token()
    return bool(real) and len(real) >= 24 and secrets.compare_digest(str(token), real)


def start_scheduler(app):
    if app.config.get("TESTING") or app.extensions.get("gsc_scheduler"):
        return

    def loop():
        time.sleep(120)
        while True:
            try:
                with app.app_context():
                    if configured():
                        st = status() or {}
                        if db.now() - (st.get("checked_at") or 0) > 20 * 3600:
                            slot = "gsc:" + time.strftime("%Y%m%d")
                            conn = db.get_db()
                            cur = conn.execute("INSERT OR IGNORE INTO seo_alerts(day, sent_at) VALUES (?,?)", (slot, db.now()))
                            conn.commit()
                            if cur.rowcount:
                                run()
            except Exception as e:
                app.logger.error("search console scheduler error: %s", e)
            time.sleep(1800)

    t = threading.Thread(target=loop, name="gsc-scheduler", daemon=True)
    app.extensions["gsc_scheduler"] = t
    t.start()
