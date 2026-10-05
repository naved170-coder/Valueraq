"""SEO automation: the website's side of it.

The writing happens outside the website, in one scheduled run a day. That run
adds markdown files under content/ (with `publish_at` timers and, where a human
should look first, `hold: yes`) and one report file under seo/runs/. This module
reads those files and gives the admin area:

  * Approvals      held pages with Approve / Reject buttons
  * SEO reports    what each day's run did, with links and keywords
  * an alert       a banner and an email when a daily run did not happen
                   (the usual cause is that the Claude usage allowance ran out)
  * IndexNow       tells Bing and partner search engines when a page goes public

Nothing here calls an AI service or needs an API key.
"""
import csv
import datetime
import hashlib
import hmac
import io
import json
import os
import re
import threading
import time
import urllib.request
from functools import lru_cache

from flask import current_app

from . import content, db

SEO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "seo")
RUNS_DIR = os.path.join(SEO_DIR, "runs")
KINDS = ("guides", "glossary")
_DATE_RE = re.compile(r"^\d{4}-\d\d-\d\d$")


def _read_json(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


@lru_cache(maxsize=1)
def config():
    """seo/config.json: {"active": true, "start": "2026-10-09", "tz_hours": 5, "run_hour": 20, ...}"""
    c = dict(active=False, start=None, tz_hours=5, tz_name="Pakistan time", run_hour=20, grace_hours=3)
    c.update(_read_json(os.path.join(SEO_DIR, "config.json"), {}))
    return c


def local_now():
    return datetime.datetime.fromtimestamp(content._now(), datetime.timezone.utc) + datetime.timedelta(hours=config()["tz_hours"])


def local_time(ts):
    """Unix time -> '7 Oct 2026, 12:00 am' in the owner's time zone."""
    if ts is None:
        return ""
    d = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc) + datetime.timedelta(hours=config()["tz_hours"])
    return f"{d.day} {d:%b %Y}, {d.hour % 12 or 12}:{d:%M} {'am' if d.hour < 12 else 'pm'}"


# ---------------------------------------------------------------- pages and their state
def doc_for(path):
    m = re.match(r"^/(guides|glossary)/([a-z0-9-]+)/$", path or "")
    return content.load(m.group(1), m.group(2)) if m else None


def state(doc):
    """(key, label) for a page: live | scheduled | waiting | rejected | missing."""
    if doc is None or doc.meta.get("status", "published") != "published":
        return "missing", "Not on the site"
    if content.is_live(doc):
        return "live", "Live"
    decision = content.decisions().get(doc.path)
    if doc.held and decision == "rejected":
        return "rejected", "Rejected"
    if doc.held and decision != "approved":
        return "waiting", "Waiting for your approval"
    return "scheduled", f"Goes live {local_time(doc.publish_ts)}"


def held_docs():
    out = []
    for kind in KINDS:
        out += [d for d in content.all_docs(kind) if d.held]
    return out


def pending():
    dec = content.decisions(fresh=True)
    docs = [d for d in held_docs() if d.path not in dec]
    docs.sort(key=lambda d: d.publish_ts or 0)
    return docs


def decided(limit=30):
    dec = {r["path"]: r for r in db.query("SELECT * FROM content_approvals ORDER BY decided_at DESC LIMIT ?", (limit,))}
    return [(doc_for(p), r) for p, r in dec.items() if doc_for(p)]


def decide(path, decision, who):
    doc = doc_for(path)
    if doc is None or not doc.held or decision not in ("approved", "rejected"):
        return False
    db.execute("INSERT INTO content_approvals(path, decision, decided_at, decided_by) VALUES (?,?,?,?) "
               "ON CONFLICT(path) DO UPDATE SET decision=excluded.decision, decided_at=excluded.decided_at, "
               "decided_by=excluded.decided_by", (path, decision, db.now(), who))
    content.decisions(fresh=True)
    return True


def upcoming():
    """Pages with a timer still in the future, soonest first."""
    now = content._now()
    out = []
    for kind in KINDS:
        out += [d for d in content.all_docs(kind) if d.publish_ts and d.publish_ts > now]
    out.sort(key=lambda d: d.publish_ts)
    return out


# ---------------------------------------------------------------- daily reports
@lru_cache(maxsize=1)
def run_dates():
    if not os.path.isdir(RUNS_DIR):
        return []
    return sorted((f[:-5] for f in os.listdir(RUNS_DIR) if f.endswith(".json") and _DATE_RE.match(f[:-5])), reverse=True)


@lru_cache(maxsize=None)
def _run_raw(date):
    if not _DATE_RE.match(date or ""):
        return None
    return _read_json(os.path.join(RUNS_DIR, date + ".json"), None)


def run(date):
    """One day's report with each item's current state filled in, or None."""
    raw = _run_raw(date)
    if not isinstance(raw, dict):
        return None
    items = []
    for it in raw.get("items") or []:
        it = dict(it)
        doc = doc_for(it.get("path"))
        it["state"], it["state_label"] = state(doc)
        it["title"] = it.get("title") or (doc.title if doc else it.get("path"))
        it["keywords"] = it.get("keywords") or (doc.keywords if doc else None) or []
        it["words"] = it.get("words") or (doc.words if doc else None)
        it["when"] = local_time(doc.publish_ts) if doc and doc.publish_ts else ""
        items.append(it)
    return dict(date=date, summary=raw.get("summary", ""), model=raw.get("model", ""), notes=raw.get("notes") or [],
                checks=raw.get("checks") or [], items=items)


def run_index():
    out = []
    for d in run_dates():
        r = run(d)
        if r:
            out.append(dict(date=d, summary=r["summary"], count=len(r["items"]),
                            new=sum(1 for i in r["items"] if i.get("action", "new") == "new"),
                            waiting=sum(1 for i in r["items"] if i["state"] == "waiting")))
    return out


def export_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Date", "What was done", "Title", "Link", "Type", "Words", "Quality score", "Keywords", "Goes live", "Status"])
    site = current_app.config["SITE_URL"]
    for d in run_dates():
        r = run(d)
        for i in (r["items"] if r else []):
            w.writerow([d, i.get("action", "new"), i["title"], site + (i.get("path") or ""), i.get("type", ""),
                        i.get("words") or "", i.get("score") or "", "; ".join(i["keywords"]), i["when"], i["state_label"]])
    return buf.getvalue()


# ---------------------------------------------------------------- missed-run alert
def alert():
    """Describe a missed daily run, or return None when everything is on schedule."""
    c = config()
    if not c["active"] or not c["start"]:
        return None
    now = local_now()
    today = now.date()
    # The run for a given day is due by run_hour; allow some grace before raising the alarm.
    due = today if now.hour >= c["run_hour"] + c["grace_hours"] else today - datetime.timedelta(days=1)
    try:
        start = datetime.date.fromisoformat(c["start"])
    except ValueError:
        return None
    if due < start:
        return None
    dates = run_dates()
    last = dates[0] if dates else None
    if last and last >= due.isoformat():
        return None
    left = upcoming()
    return dict(day=due.isoformat(), last=last, queued=len(left),
                queue_ends=local_time(left[-1].publish_ts) if left else None)


def send_alert_once():
    a = alert()
    if not a:
        return False
    conn = db.get_db()
    cur = conn.execute("INSERT OR IGNORE INTO seo_alerts(day, sent_at) VALUES (?,?)", (a["day"], db.now()))
    conn.commit()
    if not cur.rowcount:
        return False
    from . import mailer
    mailer.seo_run_missed(a)
    return True


# ---------------------------------------------------------------- IndexNow (Bing and partners)
def indexnow_key():
    return hmac.new(str(current_app.config["SECRET_KEY"]).encode(), b"indexnow", hashlib.sha256).hexdigest()[:32]


def _post_json(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status


def indexnow_tick(post=None):
    """Announce public pages that have not been announced yet. Returns the paths sent."""
    cfg = current_app.config
    if not cfg.get("INDEXNOW"):
        return []
    from . import linkgraph
    done = {r["path"] for r in db.query("SELECT path FROM indexnow_pings")}
    todo = [p for p in linkgraph.registry() if p not in done][:500]
    if not todo:
        return []
    site = cfg["SITE_URL"]
    host = site.split("://", 1)[-1]
    try:
        status = (post or _post_json)("https://api.indexnow.org/indexnow", dict(
            host=host, key=indexnow_key(), keyLocation=f"{site}/indexnow-key.txt", urlList=[site + p for p in todo]))
    except Exception as e:  # network trouble: try again on the next tick
        current_app.logger.warning("indexnow failed: %s", e)
        return []
    conn = db.get_db()
    conn.executemany("INSERT OR IGNORE INTO indexnow_pings(path, pinged_at, status) VALUES (?,?,?)",
                     [(p, db.now(), str(status)) for p in todo])
    conn.commit()
    current_app.logger.info("indexnow: announced %d pages (%s)", len(todo), status)
    return todo


# ---------------------------------------------------------------- background checks
def start_scheduler(app):
    if app.config.get("TESTING") or app.extensions.get("seo_scheduler"):
        return

    def loop():
        time.sleep(90)
        while True:
            try:
                with app.app_context():
                    send_alert_once()
                    # Only one worker should announce: claim the ten-minute slot through the database.
                    slot = "indexnow:" + time.strftime("%Y%m%d%H") + str(int(time.strftime("%M")) // 10)
                    conn = db.get_db()
                    cur = conn.execute("INSERT OR IGNORE INTO seo_alerts(day, sent_at) VALUES (?,?)", (slot, db.now()))
                    conn.commit()
                    if cur.rowcount:
                        conn.execute("DELETE FROM seo_alerts WHERE day LIKE 'indexnow:%' AND day != ?", (slot,))
                        conn.commit()
                        indexnow_tick()
            except Exception as e:
                app.logger.error("seo scheduler error: %s", e)
            time.sleep(600)

    t = threading.Thread(target=loop, name="seo-scheduler", daemon=True)
    app.extensions["seo_scheduler"] = t
    t.start()
