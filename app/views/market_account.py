"""Buyer and seller account features: watchlist, message threads, seller analytics
and verification requests. All private (login required, noindex)."""
import datetime
import secrets

from flask import Blueprint, Response, abort, current_app, flash, g, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from .. import activity, analytics, auth, backup, catalog, db, mailer, marketplace as M, ownership
from ..storage import StorageError

bp = Blueprint("market_account", __name__)

VERIFY_TYPES = {
    "revenue_verified": "Revenue",
    "traffic_verified": "Traffic",
    "fully_verified": "Revenue, traffic and ownership (full)",
}
VERIFY_LABELS = {"unverified": "Unverified", "revenue_verified": "Revenue verified",
                 "traffic_verified": "Traffic verified", "fully_verified": "Fully verified"}


def _published_listing(slug_id):
    lid = slug_id.rpartition("-")[2]
    l = db.query("SELECT * FROM listings WHERE id=?", (int(lid) if lid.isdigit() else 0,), one=True)
    if not l or l["status"] not in M.PUBLIC_STATUSES:
        abort(404)
    return l


# ---------------------------------------------------------------- watchlist
def is_saved(user, listing_id):
    return bool(user and db.query("SELECT 1 FROM watchlist WHERE user_id=? AND listing_id=?",
                                  (user["id"], listing_id), one=True))


@bp.post("/marketplace/<cat>/<slug_id>/save/")
@auth.login_required
def save_listing(cat, slug_id):
    l = _published_listing(slug_id)
    if l["seller_id"] == g.user["id"]:
        flash("This is your own listing.", "error")
    elif is_saved(g.user, l["id"]):
        db.execute("DELETE FROM watchlist WHERE user_id=? AND listing_id=?", (g.user["id"], l["id"]))
        flash("Removed from your watchlist.", "ok")
    else:
        if db.query("SELECT COUNT(*) n FROM watchlist WHERE user_id=?", (g.user["id"],), one=True)["n"] >= 200:
            flash("Your watchlist is full (200 listings). Remove some to add more.", "error")
        else:
            db.execute("INSERT INTO watchlist(user_id, listing_id, created_at, last_price) VALUES (?,?,?,?)",
                       (g.user["id"], l["id"], db.now(), l["asking_price"]))
            analytics.server_event("listing_saved", {"listing": l["id"]})
            flash("Saved to your watchlist. We'll email you if the price drops or it sells.", "ok")
    nxt = request.form.get("next") or ""
    return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else M.listing_path(l))


@bp.get("/account/watchlist/")
@auth.login_required
def watchlist():
    rows = db.query("SELECT l.*, w.created_at saved_at, w.last_price FROM watchlist w JOIN listings l ON l.id=w.listing_id "
                    "WHERE w.user_id=? ORDER BY w.created_at DESC", (g.user["id"],))
    out = []
    for r in rows:
        d = dict(r)
        d["path"] = M.listing_path(r)
        d["category_name"] = catalog.CATS_BY_SLUG[r["category"]]["name"].replace(" for Sale", "")
        d["available"] = r["status"] in M.PUBLIC_STATUSES
        out.append(d)
    searches = [dict(s, label=search_label(s), url=search_url(s)) for s in
                db.query("SELECT * FROM saved_searches WHERE user_id=? ORDER BY created_at DESC", (g.user["id"],))]
    return render_template("account/watchlist.html", rows=out, searches=searches)


def notify_watchers(listing_id, old_status=None):
    """Email buyers watching a listing when it sells or its asking price drops.
    Called after a status change or a re-approval; safe to call any time."""
    l = db.query("SELECT * FROM listings WHERE id=?", (listing_id,), one=True)
    if not l:
        return 0
    sent = 0
    watchers = db.query("SELECT w.*, u.email FROM watchlist w JOIN users u ON u.id=w.user_id WHERE w.listing_id=?",
                        (listing_id,))
    for w in watchers:
        if l["status"] == "sold" and old_status != "sold":
            mailer.watch_alert(w["email"], l["title"], "sold", M.listing_path(l))
            sent += 1
        elif l["status"] == "published" and l["asking_price"] and w["last_price"] and l["asking_price"] < w["last_price"]:
            mailer.watch_alert(w["email"], l["title"], "price", M.listing_path(l), w["last_price"], l["asking_price"],
                               l["currency"])
            sent += 1
        if l["status"] == "published" and l["asking_price"] != w["last_price"]:
            db.execute("UPDATE watchlist SET last_price=? WHERE user_id=? AND listing_id=?",
                       (l["asking_price"], w["user_id"], listing_id))
    return sent


# ---------------------------------------------------------------- saved searches
SEARCH_LIMIT = 20


def _int(v):
    try:
        return int(float(v)) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def search_label(s):
    """Plain-English description of a saved search, e.g. 'SaaS businesses, up to $500,000, verified only'."""
    from ..filters import money
    cat = catalog.CATS_BY_SLUG.get(s["category"] or "")
    bits = [cat["name"].replace(" for Sale", "") if cat else "All businesses"]
    if s["model"]:
        bits.append(s["model"])
    if s["price_max"]:
        bits.append(f"up to {money(s['price_max'])}")
    if s["profit_min"]:
        bits.append(f"profit from {money(s['profit_min'])} a month")
    if s["age_min"]:
        bits.append(f"at least {s['age_min']:g} years old")
    if s["verified"]:
        bits.append("verified only")
    return ", ".join(bits)


def search_url(s):
    from urllib.parse import urlencode
    cat = catalog.CATS_BY_SLUG.get(s["category"] or "")
    q = {k: v for k, v in (("price_max", s["price_max"]), ("profit_min", s["profit_min"]),
                           ("age_min", f"{s['age_min']:g}" if s["age_min"] else None), ("model", s["model"]),
                           ("verified", "1" if s["verified"] else None)) if v}
    return (cat["path"] if cat else "/marketplace/") + ("?" + urlencode(q) if q else "")


def search_matches(s, l):
    if s["category"] and s["category"] != l["category"]:
        return False
    if s["price_max"] and (l["asking_price"] is None or l["asking_price"] > s["price_max"]):
        return False
    if s["profit_min"] and (l["monthly_profit"] is None or l["monthly_profit"] < s["profit_min"]):
        return False
    if s["age_min"] and (l["age_years"] is None or l["age_years"] < s["age_min"]):
        return False
    if s["model"] and s["model"] != l["business_model"]:
        return False
    if s["verified"] and l["verification"] == "unverified":
        return False
    return True


@bp.post("/account/searches/save/")
@auth.login_required
def save_search():
    f = request.form
    cat = f.get("category") or None
    if cat and cat not in catalog.CATS_BY_SLUG:
        abort(400)
    age = None
    try:
        age = float(f.get("age_min")) if f.get("age_min") else None
    except ValueError:
        pass
    row = dict(category=cat, price_max=_int(f.get("price_max")), profit_min=_int(f.get("profit_min")), age_min=age,
               model=(f.get("model") or "")[:80] or None, verified=1 if f.get("verified") == "1" else 0)
    back = search_url(row)
    n = db.query("SELECT COUNT(*) n FROM saved_searches WHERE user_id=?", (g.user["id"],), one=True)["n"]
    same = db.query("SELECT 1 FROM saved_searches WHERE user_id=? AND IFNULL(category,'')=? AND IFNULL(price_max,0)=? "
                    "AND IFNULL(profit_min,0)=? AND IFNULL(age_min,0)=? AND IFNULL(model,'')=? AND verified=?",
                    (g.user["id"], cat or "", row["price_max"] or 0, row["profit_min"] or 0, age or 0,
                     row["model"] or "", row["verified"]), one=True)
    if same:
        flash("You've already saved this search.", "ok")
    elif n >= SEARCH_LIMIT:
        flash(f"You can keep {SEARCH_LIMIT} saved searches. Delete one in your watchlist to add another.", "error")
    else:
        db.execute("INSERT INTO saved_searches(user_id, category, price_max, profit_min, age_min, model, verified, created_at) "
                   "VALUES (?,?,?,?,?,?,?,?)", (g.user["id"], cat, row["price_max"], row["profit_min"], age, row["model"],
                                                row["verified"], db.now()))
        analytics.server_event("search_saved", {"category": cat})
        flash("Search saved. We'll email you when a new listing matches. Manage it in your watchlist.", "ok")
    return redirect(back)


@bp.post("/account/searches/<int:sid>/delete/")
@auth.login_required
def delete_search(sid):
    db.execute("DELETE FROM saved_searches WHERE id=? AND user_id=?", (sid, g.user["id"]))
    flash("Saved search deleted.", "ok")
    return redirect(url_for("market_account.watchlist"))


def notify_saved_searches(listing_id):
    """Email each buyer whose saved search matches a newly published listing (one email per buyer)."""
    from ..filters import money
    l = db.query("SELECT * FROM listings WHERE id=?", (listing_id,), one=True)
    if not l or l["status"] != "published" or l["is_test"]:
        return 0
    sent, seen = 0, set()
    for s in db.query("SELECT s.*, u.email FROM saved_searches s JOIN users u ON u.id=s.user_id ORDER BY s.id"):
        if s["user_id"] in seen or s["user_id"] == l["seller_id"] or not search_matches(s, l):
            continue
        seen.add(s["user_id"])
        price = f"Asking {money(l['asking_price'], l['currency'])}" if l["asking_price"] else "Price on request"
        if l["monthly_profit"]:
            price += f" · profit {money(l['monthly_profit'], l['currency'])} a month"
        mailer.search_alert(s["email"], search_label(s), l["title"], M.listing_path(l), price)
        sent += 1
    return sent


# ---------------------------------------------------------------- messages
def unread_count(user):
    if not user:
        return 0
    a = db.query("SELECT COUNT(*) n FROM inquiries i JOIN listings l ON l.id=i.listing_id WHERE l.seller_id=? "
                 "AND i.status='new'", (user["id"],), one=True)["n"]
    b = db.query("SELECT COUNT(*) n FROM messages m JOIN inquiries i ON i.id=m.inquiry_id JOIN listings l ON "
                 "l.id=i.listing_id WHERE m.read_at IS NULL AND m.sender_id!=? AND (i.buyer_id=? OR l.seller_id=?)",
                 (user["id"], user["id"], user["id"]), one=True)["n"]
    return a + b


def _thread(iid):
    t = db.query("SELECT i.*, l.title, l.slug, l.category, l.id lid, l.seller_id, l.status listing_status, "
                 "b.email buyer_email, b.name buyer_name, s.email seller_email FROM inquiries i "
                 "JOIN listings l ON l.id=i.listing_id JOIN users b ON b.id=i.buyer_id JOIN users s ON s.id=l.seller_id "
                 "WHERE i.id=?", (iid,), one=True)
    if not t or g.user["id"] not in (t["buyer_id"], t["seller_id"]):
        abort(404)
    return t


@bp.get("/account/inquiries/")
@auth.login_required
def inquiries():
    uid = g.user["id"]
    rows = db.query(
        "SELECT i.id, i.message, i.created_at, i.status, i.buyer_id, l.title, l.seller_id, b.email buyer_email, "
        "b.name buyer_name, "
        "(SELECT COUNT(*) FROM messages m WHERE m.inquiry_id=i.id) replies, "
        "(SELECT MAX(m.created_at) FROM messages m WHERE m.inquiry_id=i.id) last_reply_at, "
        "(SELECT m.body FROM messages m WHERE m.inquiry_id=i.id ORDER BY m.created_at DESC, m.id DESC LIMIT 1) last_body, "
        "(SELECT COUNT(*) FROM messages m WHERE m.inquiry_id=i.id AND m.read_at IS NULL AND m.sender_id!=?) unread "
        "FROM inquiries i JOIN listings l ON l.id=i.listing_id JOIN users b ON b.id=i.buyer_id "
        "WHERE i.buyer_id=? OR l.seller_id=? ORDER BY COALESCE("
        "(SELECT MAX(m.created_at) FROM messages m WHERE m.inquiry_id=i.id), i.created_at) DESC LIMIT 300",
        (uid, uid, uid))
    threads = []
    for r in rows:
        d = dict(r)
        d["i_am_seller"] = r["seller_id"] == uid
        d["other"] = (r["buyer_name"] or r["buyer_email"]) if d["i_am_seller"] else "Seller"
        d["unread"] = r["unread"] + (1 if d["i_am_seller"] and r["status"] == "new" else 0)
        d["last_at"] = r["last_reply_at"] or r["created_at"]
        d["snippet"] = (r["last_body"] or r["message"])[:140]
        threads.append(d)
    return render_template("account/inquiries.html", threads=threads)


# File types allowed in a thread, with the bytes each must start with (None = plain text, checked separately).
ATTACH_TYPES = {"pdf": b"%PDF", "png": b"\x89PNG", "jpg": b"\xff\xd8\xff", "jpeg": b"\xff\xd8\xff",
                "xlsx": b"PK\x03\x04", "docx": b"PK\x03\x04", "csv": None, "txt": None}


def _file_store():
    """Private file storage for attachments (the same bucket as backups), or None when it isn't set up."""
    store = current_app.extensions.get("file_store")
    if store is None and backup.configured():
        store = backup.client()
    return store


def attachments_enabled():
    return _file_store() is not None


def _read_upload(fs):
    """Validate one uploaded file. Returns (name, data, error)."""
    name = secure_filename(fs.filename or "")[:80]
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ATTACH_TYPES:
        return None, None, "That file type isn't allowed. Use PDF, PNG, JPG, CSV, TXT, XLSX or DOCX."
    limit = current_app.config["ATTACH_MAX_BYTES"]
    data = fs.stream.read(limit + 1)
    if len(data) > limit:
        return None, None, f"That file is too big. The limit is {limit // (1024 * 1024)} MB."
    if not data:
        return None, None, "That file is empty."
    magic = ATTACH_TYPES[ext]
    if magic is not None:
        ok = data.startswith(magic)
    else:
        try:
            ok = b"\x00" not in data and bool(data.decode("utf-8"))
        except UnicodeDecodeError:
            ok = False
    if not ok:
        return None, None, "That file doesn't look like the type its name says. Save it again and retry."
    return name, data, None


@bp.get("/account/inquiries/<int:iid>/files/<int:fid>/")
@auth.login_required
def thread_file(iid, fid):
    _thread(iid)  # 404 unless the signed-in user is the buyer or the seller
    f = db.query("SELECT * FROM message_files WHERE id=? AND inquiry_id=?", (fid, iid), one=True)
    store = _file_store()
    if not f or store is None:
        abort(404)
    try:
        data = store.get(f["object_key"])
    except (StorageError, KeyError):
        flash("That file couldn't be fetched just now. Try again in a minute.", "error")
        return redirect(url_for("market_account.thread", iid=iid))
    # Always a download, never shown inside the site, so a file can't run as a page.
    return Response(data, mimetype="application/octet-stream", headers={
        "Content-Disposition": f'attachment; filename="{f["name"]}"', "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-store"})


@bp.route("/account/inquiries/<int:iid>/", methods=["GET", "POST"])
@auth.login_required
def thread(iid):
    t = _thread(iid)
    uid = g.user["id"]
    i_am_seller = t["seller_id"] == uid
    if request.method == "POST":
        if auth.rate_limited(f"message:{uid}", 30, 3600):
            abort(429)
        body = (request.form.get("message") or "").strip()
        fs = request.files.get("file")
        name = data = err = None
        store = _file_store()
        if fs and fs.filename and store is not None:
            name, data, err = _read_upload(fs)
            if not err and db.query("SELECT COUNT(*) n FROM message_files WHERE inquiry_id=?", (iid,), one=True)["n"] \
                    >= current_app.config["ATTACH_PER_THREAD"]:
                err = "This conversation has reached its limit of files."
            if not err:
                key = f"attachments/{iid}/{secrets.token_hex(8)}-{name}"
                try:
                    store.put(key, data)
                except StorageError:
                    err = "The file couldn't be stored just now. Your message was not sent; please try again."
        if err:
            flash(err, "error")
        elif len(body) < 2 and not data:
            flash("Write a message first.", "error")
        else:
            mid = db.execute("INSERT INTO messages(inquiry_id, sender_id, body, created_at) VALUES (?,?,?,?)",
                             (iid, uid, body[:4000], db.now()))
            if data:
                db.execute("INSERT INTO message_files(inquiry_id, message_id, uploader_id, name, bytes, object_key, "
                           "created_at) VALUES (?,?,?,?,?,?,?)", (iid, mid, uid, name, len(data), key, db.now()))
                activity.record("file_attached", target=f"conversation #{iid}", detail=f"{name} ({len(data)} bytes)")
            to = t["buyer_email"] if i_am_seller else t["seller_email"]
            note = (body[:4000] + ("\n\n" if body else "") + (f"[File attached: {name}]" if data else "")).strip()
            mailer.message_notification(to, t["title"], "the seller" if i_am_seller else "the buyer", note, iid)
            analytics.server_event("message_sent", {"listing": t["lid"]})
            flash("Message sent.", "ok")
        return redirect(url_for("market_account.thread", iid=iid))
    # Opening the thread marks what the other person wrote as read.
    db.execute("UPDATE messages SET read_at=? WHERE inquiry_id=? AND sender_id!=? AND read_at IS NULL",
               (db.now(), iid, uid))
    if i_am_seller and t["status"] == "new":
        db.execute("UPDATE inquiries SET status='read' WHERE id=?", (iid,))
    msgs = [dict(sender_id=t["buyer_id"], body=t["message"], created_at=t["created_at"])]
    msgs += [dict(m) for m in db.query("SELECT * FROM messages WHERE inquiry_id=? ORDER BY created_at, id", (iid,))]
    files = {}
    for f in db.query("SELECT * FROM message_files WHERE inquiry_id=? ORDER BY id", (iid,)):
        files.setdefault(f["message_id"], []).append(f)
    for m in msgs:
        m["files"] = files.get(m.get("id"), [])
        m["mine"] = m["sender_id"] == uid
        m["who"] = "You" if m["mine"] else ("Buyer" if m["sender_id"] == t["buyer_id"] else "Seller")
    other = (t["buyer_name"] or t["buyer_email"]) if i_am_seller else "the seller"
    return render_template("account/thread.html", t=t, msgs=msgs, i_am_seller=i_am_seller, other=other,
                           can_attach=attachments_enabled(), max_mb=current_app.config["ATTACH_MAX_BYTES"] // (1024 * 1024),
                           listing_path=f"/marketplace/{t['category']}/{t['slug']}-{t['lid']}/")


# ---------------------------------------------------------------- seller analytics
def record_view(listing_id):
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    db.execute("INSERT INTO listing_views(listing_id, day, views) VALUES (?,?,1) "
               "ON CONFLICT(listing_id, day) DO UPDATE SET views=views+1", (listing_id, day))


@bp.get("/account/analytics/")
@auth.login_required
def seller_analytics():
    uid = g.user["id"]
    today = datetime.datetime.now(datetime.timezone.utc).date()
    since30 = (today - datetime.timedelta(days=29)).isoformat()
    listings = db.query("SELECT * FROM listings WHERE seller_id=? AND status!='removed' ORDER BY updated_at DESC", (uid,))
    rows, totals = [], dict(views=0, views30=0, inquiries=0, saves=0)
    for l in listings:
        v30 = db.query("SELECT COALESCE(SUM(views),0) n FROM listing_views WHERE listing_id=? AND day>=?",
                       (l["id"], since30), one=True)["n"]
        inq = db.query("SELECT COUNT(*) n FROM inquiries WHERE listing_id=?", (l["id"],), one=True)["n"]
        saves = db.query("SELECT COUNT(*) n FROM watchlist WHERE listing_id=?", (l["id"],), one=True)["n"]
        d = dict(l)
        d.update(path=M.listing_path(l), views30=v30, inquiries=inq, saves=saves,
                 rate=(inq / l["view_count"] * 100) if l["view_count"] else None)
        rows.append(d)
        totals["views"] += l["view_count"]
        totals["views30"] += v30
        totals["inquiries"] += inq
        totals["saves"] += saves
    # Views per week for the last 8 weeks (Monday-based), across all the seller's listings.
    weeks = []
    monday = today - datetime.timedelta(days=today.weekday())
    for k in range(7, -1, -1):
        start = monday - datetime.timedelta(weeks=k)
        end = start + datetime.timedelta(days=6)
        n = db.query("SELECT COALESCE(SUM(v.views),0) n FROM listing_views v JOIN listings l ON l.id=v.listing_id "
                     "WHERE l.seller_id=? AND v.day>=? AND v.day<=?", (uid, start.isoformat(), end.isoformat()),
                     one=True)["n"]
        weeks.append(dict(start=start, views=n, current=(k == 0)))
    return render_template("account/analytics.html", rows=rows, totals=totals, weeks=weeks,
                           peak=max([w["views"] for w in weeks] + [1]))


# ---------------------------------------------------------------- verification requests
@bp.post("/account/listings/<int:lid>/verification/")
@auth.login_required
def request_verification(lid):
    from flask import current_app
    l = db.query("SELECT * FROM listings WHERE id=? AND seller_id=? AND status='published'", (lid, g.user["id"]), one=True)
    if not l or not current_app.config["VERIFICATION_REQUESTS_ENABLED"]:
        abort(404)
    kind = request.form.get("type")
    note = (request.form.get("note") or "").strip()
    if kind not in VERIFY_TYPES:
        flash("Choose what you'd like verified.", "error")
    elif len(note) < 20:
        flash("Tell us in a sentence or two what evidence you can share (for example read-only access or statements).", "error")
    elif l["verification_requested_at"]:
        flash("A verification request for this listing is already waiting for review.", "error")
    else:
        db.execute("UPDATE listings SET verification_requested_at=?, verification_request_type=?, "
                   "verification_request_note=? WHERE id=?", (db.now(), kind, note[:1500], lid))
        mailer.admin_verification_request(l["title"], VERIFY_TYPES[kind], g.user["email"], note[:1500])
        from .. import activity
        activity.record("verification_requested", target=f"listing #{lid}", detail=kind)
        analytics.server_event("verification_requested", {"listing": lid})
        flash("Verification requested. A reviewer will email you to arrange the evidence check.", "ok")
    return redirect(url_for("account.listings"))


# ---------------------------------------------------------------- automatic ownership check
@bp.post("/account/listings/<int:lid>/ownership/")
@auth.login_required
def check_ownership(lid):
    l = db.query("SELECT * FROM listings WHERE id=? AND seller_id=?", (lid, g.user["id"]), one=True)
    if not l or l["status"] in ("removed", "suspended"):
        abort(404)
    if auth.rate_limited(f"ownership:{g.user['id']}", 12, 3600):
        abort(429)
    host = ownership.host_of(l["website_url"])
    if not host:
        flash("Add the website address to the listing first (Edit, then Website URL).", "error")
        return redirect(url_for("account.listings"))
    method = ownership.check(l)
    if method:
        db.execute("UPDATE listings SET ownership_verified_at=?, ownership_method=?, ownership_host=? WHERE id=?",
                   (db.now(), method, host, lid))
        activity.record("ownership_verified", target=f"listing #{lid}", detail=f"{host} via {method}")
        analytics.server_event("ownership_verified", {"listing": lid})
        flash(f"Ownership of {host} confirmed. The badge now shows on your listing.", "ok")
    else:
        activity.record("ownership_check_failed", target=f"listing #{lid}", detail=host)
        flash(f"We couldn't find the code on {host} yet. Check it was saved exactly as shown. "
              "A DNS record can take up to an hour to appear; a file or meta tag works straight away.", "error")
    return redirect(url_for("account.listings") + f"#listing-{lid}")
