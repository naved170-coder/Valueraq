"""Accounts, private reports, seller listings, inquiries and billing. All noindex + private."""
import json
import secrets

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for

from .. import ai, analytics, auth, billing, catalog, db, marketplace as M, valuation as V
from ..views.marketplace import LISTING_FIELDS, _read_listing_form

bp = Blueprint("account", __name__)


def _safe_next(default="/account/"):
    nxt = request.values.get("next") or ""
    if nxt.startswith("/") and not nxt.startswith("//"):
        return nxt
    return default


def _r(template, **ctx):
    return render_template(template, **ctx)


# ---------------------------------------------------------------- auth
@bp.route("/signup/", methods=["GET", "POST"])
def signup():
    if g.get("user"):
        return redirect(_safe_next())
    error = None
    if request.method == "POST":
        # No hidden trap field here, so browser autofill works normally.
        if auth.rate_limited("signup", 20, 3600):
            current_app.logger.warning("signup blocked: rate limit")
            return _r("account/signup.html", next=_safe_next(""),
                      error="Too many attempts from this connection. Wait a few minutes and try again."), 429
        email = (request.form.get("email") or "").strip().lower()
        pw = request.form.get("password") or ""
        if "@" not in email or "." not in email.split("@")[-1]:
            error = "Enter a valid email address."
        elif len(pw) < 10:
            error = "Use a password of at least 10 characters."
        elif not request.form.get("agree"):
            error = "Accept the terms and privacy policy to create an account."
        elif db.query("SELECT 1 FROM users WHERE email=?", (email,), one=True):
            error = "An account with this email already exists. Log in instead."
        else:
            uid = auth.create_user(email, pw, (request.form.get("name") or "").strip()[:80] or None)
            u = db.query("SELECT * FROM users WHERE id=?", (uid,), one=True)
            auth.login_user(u)
            g.user = u
            analytics.server_event("signup")
            return redirect(_safe_next())
    return _r("account/signup.html", error=error, next=_safe_next(""))


@bp.route("/login/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if auth.rate_limited("login", 20, 900):
            current_app.logger.warning("login blocked: rate limit")
            return _r("account/login.html", next=_safe_next(""),
                      error="Too many attempts from this connection. Wait a few minutes and try again."), 429
        u = auth.verify(request.form.get("email") or "", request.form.get("password") or "")
        if u:
            auth.login_user(u)
            return redirect(_safe_next())
        error = "That email and password don't match an account."
    return _r("account/login.html", error=error, next=_safe_next(""))


@bp.post("/logout/")
def logout():
    session.clear()
    return redirect("/")


# ---------------------------------------------------------------- settings
@bp.route("/account/settings/", methods=["GET", "POST"])
@auth.login_required
def settings():
    errors = {}
    if request.method == "POST":
        if auth.rate_limited(f"pwchange:{g.user['id']}", 10, 900):
            return _r("account/settings.html", errors={"_": "Too many attempts. Wait a few minutes and try again."}), 429
        cur = request.form.get("current_password") or ""
        new = request.form.get("new_password") or ""
        confirm = request.form.get("confirm_password") or ""
        from werkzeug.security import check_password_hash
        if not check_password_hash(g.user["password_hash"], cur):
            errors["current_password"] = "That isn't your current password."
        if len(new) < 10:
            errors["new_password"] = "Use at least 10 characters."
        elif new == cur:
            errors["new_password"] = "Choose a password different from your current one."
        if not errors.get("new_password") and new != confirm:
            errors["confirm_password"] = "The two new passwords don't match."
        if not errors:
            auth.change_password(g.user, new)
            current_app.logger.info("password changed for user %s", g.user["id"])
            flash("Your password has been changed. Other devices have been signed out.", "ok")
            return redirect(url_for("account.settings"))
    return _r("account/settings.html", errors=errors), (422 if errors else 200)


# ---------------------------------------------------------------- dashboard
@bp.get("/account/")
@auth.login_required
def home():
    u = g.user
    reports = db.query("SELECT * FROM reports WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (u["id"],))
    listings = db.query("SELECT * FROM listings WHERE seller_id=? ORDER BY updated_at DESC LIMIT 5", (u["id"],))
    inbox = db.query("SELECT COUNT(*) n FROM inquiries i JOIN listings l ON l.id=i.listing_id WHERE l.seller_id=? "
                     "AND i.status='new'", (u["id"],), one=True)["n"]
    return _r("account/home.html", reports=reports, listings=listings, inbox=inbox,
              tools=catalog.TOOLS, trial_days=_trial_days_left(u))


def _trial_days_left(u):
    if u["plan"] == "trial" and u["trial_ends_at"]:
        return max(0, (u["trial_ends_at"] - db.now() + 86399) // 86400)
    return None


# ---------------------------------------------------------------- reports
@bp.get("/account/reports/")
@auth.login_required
def reports():
    rows = db.query("SELECT * FROM reports WHERE user_id=? ORDER BY created_at DESC", (g.user["id"],))
    return _r("account/reports.html", reports=rows, limit=None if auth.is_premium() else
              current_app.config["FREE_SAVED_REPORTS"])


@bp.get("/account/reports/new/")
@auth.login_required
def report_new():
    pending = session.get("last_valuation")
    if not pending:
        flash("Run a valuation first, then open the detailed report.", "error")
        return redirect("/tools/")
    from flask import current_app
    if not auth.is_premium():
        n = db.query("SELECT COUNT(*) n FROM reports WHERE user_id=?", (g.user["id"],), one=True)["n"]
        if n >= current_app.config["FREE_SAVED_REPORTS"]:
            flash(f"Free accounts keep {current_app.config['FREE_SAVED_REPORTS']} saved reports. Start the free "
                  f"{current_app.config['TRIAL_DAYS']}-day Pro trial or delete an old report to save this one.", "error")
            return redirect(url_for("account.reports"))
    tool = pending["tool"]
    x = pending["inputs"]
    try:
        r = V.value_business(tool, x)
    except V.ValuationError as e:
        flash(str(e), "error")
        return redirect("/tools/")
    token = secrets.token_hex(16)  # lowercase: URLs are case-normalised
    title = f"{V.TYPE_LABEL[tool]} valuation"
    commentary = ai.commentary(r) if auth.is_premium() else None
    db.execute("INSERT INTO reports(token, user_id, tool, title, inputs_json, result_json, ai_commentary, "
               "methodology_version, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
               (token, g.user["id"], tool, title, json.dumps(x), json.dumps(r), commentary, V.METHODOLOGY_VERSION,
                db.now()))
    session.pop("last_valuation", None)
    return redirect(url_for("account.report", token=token))


@bp.get("/reports/private/<token>/")
@auth.login_required
def report(token):
    rep = db.query("SELECT * FROM reports WHERE token=?", (token,), one=True)
    if not rep or (rep["user_id"] != g.user["id"] and g.user["role"] != "admin"):
        abort(404)  # never reveal that a private report exists
    r = json.loads(rep["result_json"])
    analytics.server_event("report_viewed", {"tool": rep["tool"]})
    t = catalog.TOOLS_BY_KEY[rep["tool"]]
    return _r("account/report.html", rep=rep, r=r, t=t, cat=catalog.CAT_BY_TOOL[rep["tool"]],
              checklist=CHECKLISTS.get(rep["tool"], []) + CHECKLISTS["all"], ai_enabled=ai.enabled())


@bp.post("/reports/private/<token>/delete/")
@auth.login_required
def report_delete(token):
    db.execute("DELETE FROM reports WHERE token=? AND user_id=?", (token, g.user["id"]))
    flash("Report deleted.", "ok")
    return redirect(url_for("account.reports"))


@bp.post("/reports/private/<token>/commentary/")
@auth.login_required
def report_commentary(token):
    rep = db.query("SELECT * FROM reports WHERE token=? AND user_id=?", (token, g.user["id"]), one=True)
    if not rep:
        abort(404)
    if not auth.is_premium():
        flash("AI commentary is part of Pro. Start the free trial to add it.", "error")
    else:
        c = ai.commentary(json.loads(rep["result_json"]))
        if c:
            db.execute("UPDATE reports SET ai_commentary=? WHERE id=?", (c, rep["id"]))
        else:
            flash("Commentary couldn't be generated right now. Try again later.", "error")
    return redirect(url_for("account.report", token=token))


CHECKLISTS = {
    "all": [
        "Profit and loss statements for the last 24 months, reconciled to bank or payment-processor deposits.",
        "Proof of ownership for the domain, code, accounts and trademarks being transferred.",
        "A list of every recurring expense, contractor and tool subscription the buyer will inherit.",
        "A written summary of the tasks the owner performs each week, with time estimates.",
    ],
    "website": ["Analytics access (read-only) covering at least 12 months, with traffic by channel.",
                "Search Console history showing clicks and any manual actions.",
                "Affiliate or ad-network dashboards matching the revenue claimed."],
    "saas": ["MRR by month with new, expansion, contraction and churned MRR.",
             "Customer list with plan, start date and contract terms (anonymised if needed).",
             "Hosting and third-party service costs, to confirm gross margin."],
    "ai": ["Model and API providers used, their terms of service and monthly usage cost.",
           "Evidence of what the product adds beyond the underlying model (data, workflow, integrations).",
           "MRR by month with churned revenue."],
    "app": ["App Store and Google Play console access showing downloads, revenue and ratings.",
            "Active-user trend and retention by cohort.",
            "Paid acquisition spend and cost per install, if any."],
    "newsletter": ["Email platform access showing list growth, opens and clicks over 12 months.",
                   "Sponsor list with rates, repeat bookings and payment records.",
                   "Subscriber acquisition sources and any paid growth spend."],
    "ecommerce": ["Supplier contracts, lead times and landed cost per SKU.",
                  "Inventory count and valuation method at closing.",
                  "Marketplace account health (for example Amazon) and ad spend by channel."],
}


# ---------------------------------------------------------------- seller listings
@bp.get("/account/listings/")
@auth.login_required
def listings():
    rows = db.query("SELECT * FROM listings WHERE seller_id=? ORDER BY updated_at DESC", (g.user["id"],))
    decorated = []
    for r in rows:
        d = dict(r)
        d["path"] = M.listing_path(r)
        d["flags"] = M.decode_flags(r["quality_flags"])
        d["inquiries"] = db.query("SELECT COUNT(*) n FROM inquiries WHERE listing_id=?", (r["id"],), one=True)["n"]
        decorated.append(d)
    from flask import current_app
    return _r("account/listings.html", listings=decorated, billing_enabled=billing.enabled(),
              featured_plans=current_app.config["FEATURED_PLANS"],
              featured_ok=request.args.get("featured") == "success")


@bp.route("/account/listings/<int:lid>/edit/", methods=["GET", "POST"])
@auth.login_required
def listing_edit(lid):
    l = db.query("SELECT * FROM listings WHERE id=? AND seller_id=?", (lid, g.user["id"]), one=True)
    if not l or l["status"] in ("removed", "suspended"):
        abort(404)
    errors = {}
    data = dict(l)
    if request.method == "POST":
        data, errors = _read_listing_form()
        if not errors:
            if data["title"] != l["title"]:
                M.change_slug(lid, data["title"], by=f"user:{g.user['id']}")
            sets = ", ".join(f"{f}=?" for f in LISTING_FIELDS)
            # Material edits to a live listing go back through moderation.
            new_status = "pending" if l["status"] in ("published", "rejected") else l["status"]
            db.execute(f"UPDATE listings SET {sets}, status=?, updated_at=? WHERE id=?",
                       (*[data[f] for f in LISTING_FIELDS], new_status, db.now(), lid))
            M.refresh(lid)
            flash("Changes saved. Edited listings are re-checked before they go live again.", "ok")
            return redirect(url_for("account.listings"))
    return _r("sell_form_page.html", data=data, errors=errors, cats=catalog.CATEGORIES,
              models=catalog.BUSINESS_MODELS, editing=l)


@bp.post("/account/listings/<int:lid>/status/")
@auth.login_required
def listing_status(lid):
    l = db.query("SELECT * FROM listings WHERE id=? AND seller_id=?", (lid, g.user["id"]), one=True)
    if not l:
        abort(404)
    action = request.form.get("action")
    if action == "sold" and l["status"] == "published":
        M.set_status(lid, "sold", by=f"user:{g.user['id']}")
        flash("Marked as sold. The page stays visible with a sold notice and leaves search results.", "ok")
    elif action == "withdraw":
        M.set_status(lid, "removed", by=f"user:{g.user['id']}", note="withdrawn by seller")
        flash("Listing withdrawn.", "ok")
    elif action == "submit" and l["status"] == "draft":
        M.set_status(lid, "pending", by=f"user:{g.user['id']}")
    return redirect(url_for("account.listings"))


@bp.post("/account/listings/<int:lid>/feature/")
@auth.login_required
def listing_feature(lid):
    l = db.query("SELECT * FROM listings WHERE id=? AND seller_id=? AND status='published'", (lid, g.user["id"]), one=True)
    if not l:
        abort(404)
    try:
        plan = request.form.get("plan", "featured_monthly")
        return redirect(billing.featured_checkout(g.user, lid, plan), 303)
    except billing.BillingError as e:
        flash(str(e), "error")
        return redirect(url_for("account.listings"))


# ---------------------------------------------------------------- inquiries
@bp.get("/account/inquiries/")
@auth.login_required
def inquiries():
    received = db.query("SELECT i.*, l.title, l.id lid, u.email buyer_email FROM inquiries i JOIN listings l ON "
                        "l.id=i.listing_id JOIN users u ON u.id=i.buyer_id WHERE l.seller_id=? ORDER BY i.created_at DESC",
                        (g.user["id"],))
    sent = db.query("SELECT i.*, l.title, l.slug, l.category, l.id lid FROM inquiries i JOIN listings l ON "
                    "l.id=i.listing_id WHERE i.buyer_id=? ORDER BY i.created_at DESC", (g.user["id"],))
    db.execute("UPDATE inquiries SET status='read' WHERE status='new' AND listing_id IN "
               "(SELECT id FROM listings WHERE seller_id=?)", (g.user["id"],))
    return _r("account/inquiries.html", received=received, sent=sent)


# ---------------------------------------------------------------- billing
@bp.get("/account/billing/")
@auth.login_required
def billing_page():
    from flask import current_app
    return _r("account/billing.html", plans=current_app.config["PLANS"], enabled=billing.enabled(),
              featured_plans=current_app.config["FEATURED_PLANS"],
              trial_days=_trial_days_left(g.user), trial_ends=g.user["trial_ends_at"],
              checkout=request.args.get("checkout"))


@bp.post("/account/trial/")
@auth.login_required
def trial():
    if auth.start_trial(g.user):
        analytics.server_event("trial_started")
        flash(f"Your {current_app.config['TRIAL_DAYS']}-day Pro trial has started. No card needed.", "ok")
    else:
        flash("This account has already used its free trial.", "error")
    return redirect(_safe_next("/account/billing/"))


@bp.post("/checkout/<plan>/")
@auth.login_required
def checkout(plan):
    try:
        return redirect(billing.subscription_checkout(g.user, plan), 303)
    except billing.BillingError as e:
        flash(str(e), "error")
        return redirect(url_for("account.billing_page"))


@bp.post("/account/billing/portal/")
@auth.login_required
def portal():
    try:
        return redirect(billing.portal(g.user), 303)
    except billing.BillingError as e:
        flash(str(e), "error")
        return redirect(url_for("account.billing_page"))
