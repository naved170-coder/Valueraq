"""First-party analytics (§55, §82, §83). No third-party scripts.

The browser beacon (static/js/v.js) sets two first-party cookies on the first
page view of a visit: vq_sid (random id) and vq_ch (acquisition channel) plus
vq_lp (landing path). Server-side events read those cookies, so funnels can be
split by organic vs other channels without any cross-site tracking.
"""
import json
import re
from urllib.parse import urlsplit

from flask import g, request

from . import db

SEARCH_ENGINES = re.compile(r"(^|\.)(google|bing|duckduckgo|yahoo|yandex|baidu|ecosia|brave|startpage|qwant)\.")
AI_REFERRERS = re.compile(r"(chatgpt\.com|chat\.openai\.com|perplexity\.ai|claude\.ai|gemini\.google\.com|"
                          r"copilot\.microsoft\.com|you\.com|phind\.com)")
SOCIAL = re.compile(r"(facebook|instagram|t\.co|twitter|x\.com|linkedin|reddit|youtube|tiktok|pinterest)\.")

EVENTS = {
    "page_view", "organic_landing", "tool_started", "tool_completed", "valuation_generated", "report_viewed",
    "signup", "trial_started", "subscription", "marketplace_search", "listing_viewed", "listing_inquiry",
    "seller_registration", "listing_created", "premium_listing", "affiliate_click",
}


def classify(referrer, own_host, utm_medium=None):
    if utm_medium:
        m = utm_medium.lower()
        if m in ("cpc", "ppc", "paid", "paidsearch", "display"):
            return "paid"
        if m == "email":
            return "email"
        if m == "social":
            return "social"
    if not referrer:
        return "direct"
    host = (urlsplit(referrer).hostname or "").lower()
    if not host or host == own_host:
        return "internal"
    if AI_REFERRERS.search(host):
        return "ai"
    if SEARCH_ENGINES.search(host + "."):
        return "organic"
    if SOCIAL.search(host + "."):
        return "social"
    return "referral"


def record(name, path=None, props=None, session_id=None, channel=None, landing=None, user_id=None):
    if name not in EVENTS:
        return
    db.execute(
        "INSERT INTO events(name, path, session_id, user_id, channel, landing_path, props, created_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (name, (path or "")[:300], (session_id or "")[:64] or None, user_id, channel, (landing or "")[:300] or None,
         json.dumps(props)[:2000] if props else None, db.now()))


def server_event(name, props=None):
    """Record an event from a server view, attributing it via first-party cookies."""
    try:
        if request.headers.get("X-VQ-Audit"):
            return  # internal crawler traffic is not analytics
        u = g.get("user")
        record(name, path=request.path, props=props, session_id=request.cookies.get("vq_sid"),
               channel=request.cookies.get("vq_ch"), landing=request.cookies.get("vq_lp"),
               user_id=u["id"] if u else None)
    except Exception:
        pass  # analytics must never break a request


def funnel(days=30, channel=None):
    since = db.now() - days * 86400
    steps = [("organic_landing", "Landing (organic)"), ("page_view", "Page views"), ("tool_started", "Tool started"),
             ("valuation_generated", "Valuation generated"), ("report_viewed", "Report viewed"), ("signup", "Signup"),
             ("trial_started", "Trial started"), ("subscription", "Subscription")]
    market = [("marketplace_search", "Marketplace search"), ("listing_viewed", "Listing viewed"),
              ("listing_inquiry", "Buyer inquiry"), ("seller_registration", "Seller registration"),
              ("listing_created", "Listing created"), ("premium_listing", "Featured listing purchased")]

    def count(name):
        sql = "SELECT COUNT(DISTINCT COALESCE(session_id, id)) n FROM events WHERE name=? AND created_at>=?"
        args = [name, since]
        if channel:
            sql += " AND channel=?"
            args.append(channel)
        return db.query(sql, args, one=True)["n"]

    return ([(label, count(n)) for n, label in steps], [(label, count(n)) for n, label in market])


def landing_pages(days=30, channel="organic", limit=25):
    since = db.now() - days * 86400
    return db.query(
        "SELECT landing_path, COUNT(DISTINCT session_id) sessions, "
        " SUM(CASE WHEN name='valuation_generated' THEN 1 ELSE 0 END) valuations, "
        " SUM(CASE WHEN name='signup' THEN 1 ELSE 0 END) signups "
        "FROM events WHERE channel=? AND created_at>=? AND landing_path IS NOT NULL "
        "GROUP BY landing_path ORDER BY sessions DESC LIMIT ?", (channel, since, limit))


def vitals_summary(days=28):
    since = db.now() - days * 86400
    rows = db.query("SELECT template, metric, value FROM vitals WHERE created_at>=? ORDER BY template, metric, value",
                    (since,))
    groups = {}
    for r in rows:
        groups.setdefault((r["template"] or "?", r["metric"]), []).append(r["value"])
    out = []
    thresholds = {"LCP": (2500, 4000), "CLS": (0.1, 0.25), "INP": (200, 500), "TTFB": (800, 1800)}
    for (tpl, metric), vals in sorted(groups.items()):
        p75 = vals[min(len(vals) - 1, int(len(vals) * 0.75))]
        good, poor = thresholds.get(metric, (0, 0))
        rating = "good" if p75 <= good else "poor" if p75 > poor else "needs improvement"
        out.append(dict(template=tpl, metric=metric, p75=p75, n=len(vals), rating=rating))
    return out
