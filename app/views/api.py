"""JSON endpoints: analytics beacon, web-vitals, Stripe webhook. All under /api/ (noindex, disallowed)."""
import json

from flask import Blueprint, current_app, jsonify, request

from .. import analytics, auth, billing, db

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.post("/events/")
def events():
    if auth.rate_limited("beacon", 120, 60):
        return "", 204
    try:
        data = json.loads(request.get_data(as_text=True) or "{}")
    except ValueError:
        return "", 204
    name = data.get("n")
    if name not in analytics.EVENTS:
        return "", 204
    host = current_app.config["SITE_URL"].split("//", 1)[-1]
    channel = data.get("ch")
    if name == "page_view" and data.get("first"):
        channel = analytics.classify(data.get("ref"), host, data.get("um"))
    analytics.record(name, path=data.get("p"), props=data.get("x"), session_id=data.get("sid"),
                     channel=channel, landing=data.get("lp"))
    if name == "page_view" and data.get("first") and channel == "organic":
        analytics.record("organic_landing", path=data.get("p"), session_id=data.get("sid"),
                         channel=channel, landing=data.get("p"))
    return jsonify(ch=channel) if data.get("first") else ("", 204)


@bp.post("/vitals/")
def vitals():
    if auth.rate_limited("vitals", 60, 60):
        return "", 204
    try:
        data = json.loads(request.get_data(as_text=True) or "{}")
    except ValueError:
        return "", 204
    metric = data.get("m")
    try:
        value = float(data.get("v"))
    except (TypeError, ValueError):
        return "", 204
    if metric in ("LCP", "CLS", "INP", "TTFB") and 0 <= value < 120000:
        db.execute("INSERT INTO vitals(template, path, metric, value, created_at) VALUES (?,?,?,?,?)",
                   ((data.get("t") or "")[:40], (data.get("p") or "")[:300], metric, value, db.now()))
    return "", 204


@bp.post("/stripe/webhook/")
def stripe_webhook():
    payload = request.get_data()
    if not billing.verify_signature(payload, request.headers.get("Stripe-Signature", ""),
                                    current_app.config["STRIPE_WEBHOOK_SECRET"]):
        return jsonify(error="invalid signature"), 400
    evt = json.loads(payload)
    result = billing.handle_event(evt)
    return jsonify(ok=True, result=result)
