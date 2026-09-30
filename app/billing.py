"""Stripe billing without the SDK (plain HTTPS), plus webhook verification.

Flows:
  * Pro subscription: Checkout Session (mode=subscription), 14-day trial if the
    account has not already used its trial.
  * Featured listing: Checkout Session (mode=payment).
  * Customer portal for managing/cancelling.
If STRIPE_SECRET_KEY is not set, payment buttons explain that payments are not
configured and admins can grant plans manually.
"""
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request

from flask import current_app

from . import db

API = "https://api.stripe.com/v1/"


class BillingError(RuntimeError):
    pass


def enabled():
    return bool(current_app.config["STRIPE_SECRET_KEY"])


def _flatten(d, prefix=""):
    out = []
    for k, v in d.items():
        key = f"{prefix}[{k}]" if prefix else k
        if isinstance(v, dict):
            out.extend(_flatten(v, key))
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    out.extend(_flatten(item, f"{key}[{i}]"))
                else:
                    out.append((f"{key}[{i}]", str(item)))
        elif v is not None:
            out.append((key, "true" if v is True else "false" if v is False else str(v)))
    return out


def _post(path, data):
    if not enabled():
        raise BillingError("Payments aren't configured on this site yet.")
    body = urllib.parse.urlencode(_flatten(data)).encode()
    req = urllib.request.Request(API + path, data=body, method="POST", headers={
        "Authorization": "Bearer " + current_app.config["STRIPE_SECRET_KEY"],
        "Content-Type": "application/x-www-form-urlencoded",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read())["error"]["message"]
        except Exception:
            msg = str(e)
        raise BillingError(msg)
    except urllib.error.URLError as e:
        raise BillingError(f"Couldn't reach the payment provider: {e.reason}")


def _customer(u):
    if u["stripe_customer_id"]:
        return u["stripe_customer_id"]
    c = _post("customers", {"email": u["email"], "metadata": {"user_id": u["id"]}})
    db.execute("UPDATE users SET stripe_customer_id=? WHERE id=?", (c["id"], u["id"]))
    return c["id"]


def subscription_checkout(u, plan_key):
    plan = current_app.config["PLANS"].get(plan_key)
    if not plan or not plan["stripe_price_id"]:
        raise BillingError("This plan isn't available for purchase yet.")
    site = current_app.config["SITE_URL"]
    data = {
        "mode": "subscription",
        "customer": _customer(u),
        "line_items": [{"price": plan["stripe_price_id"], "quantity": 1}],
        "success_url": site + "/account/billing/?checkout=success",
        "cancel_url": site + "/pricing/?checkout=cancelled",
        "client_reference_id": str(u["id"]),
        "metadata": {"user_id": u["id"], "kind": "subscription", "plan": plan_key},
        "subscription_data": {"metadata": {"user_id": u["id"], "plan": plan_key}},
        "allow_promotion_codes": True,
    }
    if not u["trial_used"]:
        data["subscription_data"]["trial_period_days"] = current_app.config["TRIAL_DAYS"]
    return _post("checkout/sessions", data)["url"]


def featured_checkout(u, listing_id):
    price = current_app.config["FEATURED_LISTING"]["stripe_price_id"]
    if not price:
        raise BillingError("Featured listings aren't available for purchase yet.")
    site = current_app.config["SITE_URL"]
    return _post("checkout/sessions", {
        "mode": "payment",
        "customer": _customer(u),
        "line_items": [{"price": price, "quantity": 1}],
        "success_url": site + "/account/listings/?featured=success",
        "cancel_url": site + "/account/listings/",
        "client_reference_id": str(u["id"]),
        "metadata": {"user_id": u["id"], "kind": "featured", "listing_id": listing_id},
    })["url"]


def portal(u):
    if not u["stripe_customer_id"]:
        raise BillingError("No billing account yet.")
    return _post("billing_portal/sessions", {"customer": u["stripe_customer_id"],
                                             "return_url": current_app.config["SITE_URL"] + "/account/billing/"})["url"]


def verify_signature(payload: bytes, header: str, secret: str, tolerance=300):
    """Stripe-Signature: t=timestamp,v1=signature[,v1=...]"""
    if not secret or not header:
        return False
    parts = dict()
    sigs = []
    for item in header.split(","):
        k, _, v = item.partition("=")
        if k == "v1":
            sigs.append(v)
        else:
            parts[k] = v
    try:
        ts = int(parts.get("t", "0"))
    except ValueError:
        return False
    if abs(time.time() - ts) > tolerance:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sigs)


def handle_event(evt):
    """Idempotent webhook handling. Returns a short string for logs."""
    if db.query("SELECT 1 FROM stripe_events WHERE id=?", (evt["id"],), one=True):
        return "duplicate"
    db.execute("INSERT INTO stripe_events(id, type, received_at) VALUES (?,?,?)", (evt["id"], evt["type"], db.now()))
    obj = evt["data"]["object"]
    t = evt["type"]
    from . import analytics
    if t == "checkout.session.completed":
        md = obj.get("metadata") or {}
        uid = int(md.get("user_id") or obj.get("client_reference_id") or 0)
        if md.get("kind") == "featured" and md.get("listing_id"):
            days = current_app.config["FEATURED_LISTING"]["days"]
            db.execute("UPDATE listings SET is_featured=1, featured_until=? WHERE id=? AND seller_id=?",
                       (db.now() + days * 86400, int(md["listing_id"]), uid))
            analytics.record("premium_listing", props={"listing": md["listing_id"]}, user_id=uid)
        elif md.get("kind") == "subscription" and obj.get("subscription"):
            db.execute("UPDATE users SET stripe_subscription_id=?, plan='pro', trial_used=1 WHERE id=?",
                       (obj["subscription"], uid))
            analytics.record("subscription", props={"plan": md.get("plan")}, user_id=uid)
        return "checkout"
    if t in ("customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"):
        status = obj.get("status")
        u = db.query("SELECT * FROM users WHERE stripe_customer_id=?", (obj.get("customer"),), one=True)
        if not u:
            return "unknown customer"
        plan = "pro" if status in ("active", "trialing", "past_due") else "free"
        db.execute("UPDATE users SET plan=?, subscription_status=?, stripe_subscription_id=?, current_period_end=? "
                   "WHERE id=?", (plan, status, obj.get("id"), obj.get("current_period_end"), u["id"]))
        if status == "trialing":
            db.execute("UPDATE users SET trial_used=1 WHERE id=?", (u["id"],))
        return "subscription " + str(status)
    return "ignored"


def expire_featured():
    db.execute("UPDATE listings SET is_featured=0 WHERE is_featured=1 AND featured_until IS NOT NULL AND featured_until<?",
               (db.now(),))
