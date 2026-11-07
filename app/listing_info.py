"""The fuller seller form: business presence, private contact details, revenue by segment and a monthly cost
breakdown; the completeness rule a listing must meet before review; and the reminder emails for missing details."""
import json
import re
import threading
import time

from flask import current_app

from . import db

PRESENCE = {"online": "Online only", "physical": "Physical only", "both": "Online and physical"}

# (key, label, hint, shown_for) - shown_for: "all" or "online" (online and both)
EXPENSES = [
    ("product_cost", "Product cost / cost of goods", "Stock, materials, fulfillment, dropshipping supplier cost", "all"),
    ("salaries", "Salaries, staff and contractors", "Writers, developers, support, VAs. Not your own pay", "all"),
    ("marketing", "Marketing and ad spend", "Google, Meta, TikTok, Amazon ads, influencers", "online"),
    ("software", "Software, hosting and apps", "Hosting, domain, Shopify apps, SaaS tools", "online"),
    ("platform_fees", "Platform and payment fees", "Marketplace commission, Stripe or PayPal fees", "online"),
    ("rent", "Rent", "Shop, office or warehouse", "all"),
    ("utilities", "Utilities", "Electricity, internet, phone", "all"),
    ("interest", "Interest on loans", "Business loans and credit lines", "all"),
    ("other", "Other costs", "Accounting, legal, insurance, anything else", "all"),
]
EXP_KEYS = [k for k, *_ in EXPENSES]
MAX_SEGMENTS = 5
PHONE_OK = re.compile(r"^\+?[0-9][0-9 ()\-]{6,20}$")


def _num(v):
    v = (v or "").strip().replace(",", "").replace("$", "")
    if v == "":
        return None
    n = float(v)
    if n < 0:
        raise ValueError
    return n


def read_form(form, errors):
    """Parse the extra fields from a POSTed form. Returns a dict of column values (JSON already encoded)."""
    out = {}
    presence = (form.get("presence") or "").strip()
    out["presence"] = presence if presence in PRESENCE else None
    out["contact_email"] = (form.get("contact_email") or "").strip()[:200] or None
    phone = (form.get("contact_phone") or "").strip()[:30]
    if phone and not PHONE_OK.match(phone):
        errors["contact_phone"] = "Enter the number with country code, for example +92 300 1234567."
    out["contact_phone"] = phone or None
    segs = []
    for i in range(MAX_SEGMENTS):
        name = (form.get(f"seg_name_{i}") or "").strip()[:60]
        raw = form.get(f"seg_amount_{i}")
        try:
            amt = _num(raw)
        except ValueError:
            errors[f"seg_amount_{i}"] = "Enter a number."
            continue
        if amt is not None:
            segs.append({"name": name or f"Revenue stream {i + 1}", "amount": int(round(amt))})
    out["revenue_segments"] = json.dumps(segs) if segs else None
    exp = {}
    for k in EXP_KEYS:
        try:
            v = _num(form.get(f"exp_{k}"))
        except ValueError:
            errors[f"exp_{k}"] = "Enter a number (0 if none)."
            continue
        if v is not None:
            exp[k] = int(round(v))
    out["expenses"] = json.dumps(exp) if exp else None
    for k, cast in (("roas", float), ("owner_hours", int)):
        try:
            v = _num(form.get(k))
            out[k] = None if v is None else cast(v)
        except ValueError:
            errors[k] = "Enter a number."
            out[k] = None
    if out["owner_hours"] is not None and out["owner_hours"] > 168:
        errors["owner_hours"] = "A week has 168 hours."
    # Totals: revenue is the sum of the segments, profit is revenue minus the cost breakdown.
    if segs:
        out["monthly_revenue"] = sum(x["amount"] for x in segs)
    if segs and exp:
        out["monthly_profit"] = out["monthly_revenue"] - sum(exp.values())
    return out


def segments(l):
    try:
        return json.loads(l["revenue_segments"] or "[]")
    except (ValueError, TypeError):
        return []


def expenses(l):
    try:
        return json.loads(l["expenses"] or "{}")
    except (ValueError, TypeError):
        return {}


def is_online(l):
    return (l["presence"] or "online") in ("online", "both")


def expense_rows(l):
    """[(label, amount)] for the listing page and emails, in form order, only the lines that apply."""
    e = expenses(l)
    return [(label, e[k]) for k, label, _h, shown in EXPENSES if k in e and (shown == "all" or is_online(l))]


def missing(l):
    """Plain-language list of what still has to be filled in before the listing can be reviewed."""
    out = []
    if not l["presence"]:
        out.append("whether the business is online, physical or both")
    if not l["contact_phone"]:
        out.append("a phone number (private, for our reviewers only)")
    if l["monthly_revenue"] is None and not segments(l):
        out.append("monthly revenue by source")
    e = expenses(l)
    need = [k for k, _l, _h, shown in EXPENSES if shown == "all" or is_online(l)]
    if not e or any(k not in e for k in need):
        out.append("the monthly cost breakdown (enter 0 for costs you don't have)")
    if l["monthly_profit"] is None and not (segments(l) and e):
        out.append("monthly profit")
    if l["asking_price"] in (None, ""):
        out.append("asking price")
    if l["age_years"] in (None, ""):
        out.append("business age")
    if is_online(l) and l["monthly_traffic"] in (None, ""):
        out.append("monthly website or app visits")
    if is_online(l) and e.get("marketing") and l["roas"] is None:
        out.append("return on ad spend (ROAS), because you spend on ads")
    if l["owner_hours"] is None:
        out.append("hours a week you work on the business")
    return out


def mark(listing_id):
    """Start or stop the reminder clock after a save."""
    l = db.query("SELECT * FROM listings WHERE id=?", (listing_id,), one=True)
    if not l:
        return []
    gaps = missing(l)
    if gaps and not l["info_missing_since"]:
        db.execute("UPDATE listings SET info_missing_since=? WHERE id=?", (db.now(), listing_id))
    elif not gaps and l["info_missing_since"]:
        db.execute("UPDATE listings SET info_missing_since=NULL, info_reminders=0, info_reminded_at=NULL WHERE id=?",
                   (listing_id,))
    return gaps


# ---------------------------------------------------------------- reminders
FIRST_AFTER = 24 * 3600        # first reminder 24 hours after the gap appeared
SECOND_AFTER = 48 * 3600       # second reminder two days after the first (day 3); then stop
MAX_REMINDERS = 2


def due_reminders(now=None):
    now = now or db.now()
    rows = db.query("SELECT l.*, u.email seller_email FROM listings l JOIN users u ON u.id=l.seller_id "
                    "WHERE l.is_test=0 AND l.status IN ('draft','pending','published') "
                    "AND l.info_missing_since IS NOT NULL AND l.info_reminders < ?", (MAX_REMINDERS,))
    out = []
    for l in rows:
        if l["info_reminders"] == 0 and now - l["info_missing_since"] >= FIRST_AFTER:
            out.append(l)
        elif l["info_reminders"] == 1 and now - (l["info_reminded_at"] or 0) >= SECOND_AFTER:
            out.append(l)
    return out


def send_reminders(now=None):
    from . import mailer
    from . import marketplace as M
    sent = 0
    for l in due_reminders(now):
        gaps = missing(l)
        if not gaps:
            db.execute("UPDATE listings SET info_missing_since=NULL WHERE id=?", (l["id"],))
            continue
        # Claim the reminder atomically so two workers never send the same email.
        conn = db.get_db()
        cur = conn.execute("UPDATE listings SET info_reminders=info_reminders+1, info_reminded_at=? "
                           "WHERE id=? AND info_reminders=?", (db.now(), l["id"], l["info_reminders"]))
        conn.commit()
        if not cur.rowcount:
            continue
        to = l["contact_email"] or l["seller_email"]
        mailer.listing_missing_info(to, l["title"], gaps, l["info_reminders"] + 1,
                                    current_app.config["SITE_URL"] + f"/account/listings/{l['id']}/edit/",
                                    is_live=l["status"] == "published")
        current_app.logger.info("listing reminder %s sent for listing %s", l["info_reminders"] + 1, l["id"])
        sent += 1
    return sent


def fix_legacy(now=None):
    """One-off, run at start-up: a live listing without revenue or profit goes back to draft (buyers can't judge it),
    and every listing with gaps gets the reminder clock started so the seller is emailed promptly."""
    from . import marketplace as M
    now = now or db.now()
    conn = db.get_db()
    cur = conn.execute("INSERT OR IGNORE INTO seo_alerts(day, sent_at) VALUES ('listing-info-fix-v1', ?)", (now,))
    conn.commit()
    if not cur.rowcount:
        return 0
    n = 0
    for l in db.query("SELECT * FROM listings WHERE is_test=0 AND status IN ('published','pending')"):
        gaps = missing(l)
        if not gaps:
            continue
        if l["monthly_revenue"] is None or l["monthly_profit"] is None:
            M.set_status(l["id"], "draft", by="system",
                         note="Moved back to draft: monthly revenue and profit are needed before the listing can be live.")
            n += 1
        db.execute("UPDATE listings SET info_missing_since=? WHERE id=? AND info_missing_since IS NULL",
                   (now - FIRST_AFTER, l["id"]))
    return n


def start_scheduler(app):
    if app.config.get("TESTING") or app.extensions.get("listing_info_scheduler"):
        return

    def loop():
        time.sleep(90)
        while True:
            try:
                with app.app_context():
                    fix_legacy()
                    send_reminders()
            except Exception as e:
                app.logger.error("listing reminder scheduler error: %s", e)
            time.sleep(1800)

    t = threading.Thread(target=loop, name="listing-info-scheduler", daemon=True)
    app.extensions["listing_info_scheduler"] = t
    t.start()
