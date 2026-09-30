"""Admin: SEO dashboard, overrides, redirects, change log, keyword/GSC import, moderation, blog CMS, analytics."""
import csv
import io
import json

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from .. import analytics, audit, auth, catalog, content, db, linkgraph, marketplace as M, redirects
from ..seo import log_change

bp = Blueprint("admin", __name__, url_prefix="/admin")

OVERRIDE_FIELDS = ["meta_title", "meta_description", "h1", "canonical_url", "robots_directive", "og_title",
                   "og_description", "og_image", "schema_extra"]


def _who():
    return f"admin:{g.user['email']}"


@bp.get("/")
@auth.admin_required
def home():
    stats = dict(
        users=db.query("SELECT COUNT(*) n FROM users", one=True)["n"],
        pro=db.query("SELECT COUNT(*) n FROM users WHERE plan IN ('pro','trial')", one=True)["n"],
        reports=db.query("SELECT COUNT(*) n FROM reports", one=True)["n"],
        pending=db.query("SELECT COUNT(*) n FROM listings WHERE status='pending'", one=True)["n"],
        live=db.query("SELECT COUNT(*) n FROM listings WHERE status='published'", one=True)["n"],
        messages=db.query("SELECT COUNT(*) n FROM contact_messages", one=True)["n"],
    )
    run, _ = audit.last_run()
    steps, market = analytics.funnel(30)
    return render_template("admin/home.html", stats=stats, run=run, steps=steps, market=market, section="home")


# ---------------------------------------------------------------- SEO audit
@bp.get("/seo/")
@auth.admin_required
def seo():
    run, pages = audit.last_run()
    code = request.args.get("issue")
    sev = request.args.get("severity")
    if code:
        pages = [p for p in pages if any(i["code"] == code for i in p["issues"])]
    if sev:
        pages = [p for p in pages if any(i["severity"] == sev for i in p["issues"])]
    return render_template("admin/seo.html", run=run, pages=pages, code=code, sev=sev, section="seo")


@bp.post("/seo/run/")
@auth.admin_required
def seo_run():
    summary, _ = audit.run()
    flash(f"Audit finished: {summary['pages']} URLs, {summary['critical']} critical issues, "
          f"{summary['warnings']} warnings.", "ok")
    return redirect(url_for("admin.seo"))


@bp.route("/seo/page/", methods=["GET", "POST"])
@auth.admin_required
def seo_page():
    path = request.values.get("path") or "/"
    if not path.startswith("/"):
        abort(400)
    ov = db.query("SELECT * FROM seo_overrides WHERE path=?", (path,), one=True)
    if request.method == "POST":
        new = {f: (request.form.get(f) or "").strip() or None for f in OVERRIDE_FIELDS}
        if new["schema_extra"]:
            try:
                json.loads(new["schema_extra"])
            except ValueError:
                flash("Extra schema must be valid JSON.", "error")
                return redirect(url_for("admin.seo_page", path=path))
        idx = request.form.get("indexable")
        smp = request.form.get("sitemap_included")
        new["indexable"] = None if idx in (None, "") else int(idx)
        new["sitemap_included"] = None if smp in (None, "") else int(smp)
        if new["meta_title"] and len(new["meta_title"]) > 70:
            flash("Title is longer than 70 characters; search engines will likely truncate it.", "error")
        # Duplicate-title guard against the last audit.
        if new["meta_title"]:
            dup = db.query("SELECT path FROM seo_audit_pages WHERE run_id=(SELECT MAX(id) FROM seo_audit_runs) "
                           "AND title=? AND path!=?", (new["meta_title"], path), one=True)
            if dup:
                flash(f"That title is already used by {dup['path']}. Choose a unique title.", "error")
                return redirect(url_for("admin.seo_page", path=path))
        reason = request.form.get("reason") or None
        for f in OVERRIDE_FIELDS + ["indexable", "sitemap_included"]:
            old = ov[f] if ov else None
            log_change(path, f, None if old is None else str(old), None if new[f] is None else str(new[f]), _who(), reason)
        if all(v is None for v in new.values()):
            db.execute("DELETE FROM seo_overrides WHERE path=?", (path,))
        else:
            cols = OVERRIDE_FIELDS + ["indexable", "sitemap_included"]
            db.execute(f"INSERT INTO seo_overrides(path, {', '.join(cols)}, updated_at, updated_by) VALUES "
                       f"(?, {', '.join('?' for _ in cols)}, ?, ?) ON CONFLICT(path) DO UPDATE SET "
                       + ", ".join(f"{c}=excluded.{c}" for c in cols) + ", updated_at=excluded.updated_at, "
                       "updated_by=excluded.updated_by", (path, *[new[c] for c in cols], db.now(), _who()))
        flash("Saved. Changes are logged and live immediately.", "ok")
        return redirect(url_for("admin.seo_page", path=path))
    log = db.query("SELECT * FROM seo_change_log WHERE path=? ORDER BY changed_at DESC LIMIT 50", (path,))
    audit_row = db.query("SELECT * FROM seo_audit_pages WHERE run_id=(SELECT MAX(id) FROM seo_audit_runs) AND path=?",
                         (path,), one=True)
    issues = json.loads(audit_row["issues_json"]) if audit_row else []
    info = linkgraph.registry().get(path)
    suggestions = []
    if audit_row and audit_row["inbound"] is not None and audit_row["inbound"] < 3 and info:
        # Recommend pages in the same cluster that could link here (§61).
        for p, i in linkgraph.registry().items():
            if p != path and info["cluster"] and i["cluster"] == info["cluster"] and i["kind"] in ("guide", "tool", "category"):
                suggestions.append((i["title"], p))
    keywords = db.query("SELECT * FROM keywords WHERE target_path=?", (path,))
    return render_template("admin/seo_page.html", path=path, ov=ov, log=log, audit_row=audit_row, issues=issues,
                           suggestions=suggestions[:8], keywords=keywords, section="seo")


@bp.route("/seo/redirects/", methods=["GET", "POST"])
@auth.admin_required
def seo_redirects():
    if request.method == "POST":
        action = request.form.get("action")
        src = (request.form.get("from_path") or "").strip()
        if action == "add":
            dst = (request.form.get("to_path") or "").strip()
            if not (src.startswith("/") and dst.startswith("/")) or src == dst:
                flash("Both paths must start with / and differ.", "error")
            elif dst == "/" and not request.form.get("confirm_home"):
                flash("Redirecting to the homepage is usually a soft 404. Tick the box if it really is the replacement.",
                      "error")
            else:
                redirects.add_redirect(src, dst, _who(), request.form.get("reason"))
                flash(f"Redirect {src} → {dst} saved (any chain collapsed).", "ok")
        elif action == "gone":
            if src.startswith("/"):
                redirects.mark_gone(src, _who(), request.form.get("reason"))
                flash(f"{src} now returns 410 Gone.", "ok")
        elif action == "delete":
            redirects.remove_redirect(src, _who())
        elif action == "ungone":
            db.execute("DELETE FROM gone_urls WHERE path=?", (src,))
            redirects._invalidate()
        return redirect(url_for("admin.seo_redirects"))
    return render_template("admin/redirects.html", rows=db.query("SELECT * FROM redirects ORDER BY created_at DESC"),
                           gone=db.query("SELECT * FROM gone_urls ORDER BY created_at DESC"),
                           chains=redirects.chains(), section="redirects")


@bp.get("/seo/log/")
@auth.admin_required
def seo_log():
    rows = db.query("SELECT * FROM seo_change_log ORDER BY changed_at DESC LIMIT 500")
    return render_template("admin/log.html", rows=rows, section="log")


# ---------------------------------------------------------------- keyword + search performance imports
@bp.route("/seo/keywords/", methods=["GET", "POST"])
@auth.admin_required
def keywords():
    if request.method == "POST":
        f = request.files.get("file")
        source = (request.form.get("source") or "").strip()
        if not f or not source:
            flash("Choose a CSV file and name its source (for example 'Google Keyword Planner, Sept 2026').", "error")
        else:
            n = 0
            reader = csv.DictReader(io.StringIO(f.read().decode("utf-8-sig", errors="replace")))
            for row in reader:
                row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
                kw = row.get("keyword") or row.get("query") or row.get("keyphrase")
                if not kw:
                    continue

                def num(*names):
                    for nm in names:
                        v = row.get(nm)
                        if v not in (None, ""):
                            try:
                                return float(v.replace(",", "").replace("$", "").replace("%", ""))
                            except ValueError:
                                return None
                    return None
                db.execute("INSERT INTO keywords(keyword, intent, target_path, search_volume, difficulty, cpc, source, "
                           "source_date, imported_at) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(keyword, source) DO UPDATE "
                           "SET intent=excluded.intent, target_path=excluded.target_path, search_volume=excluded.search_volume, "
                           "difficulty=excluded.difficulty, cpc=excluded.cpc, source_date=excluded.source_date",
                           (kw.lower(), row.get("intent") or None, row.get("target_path") or row.get("url") or None,
                            num("search_volume", "volume", "avg. monthly searches"), num("difficulty", "kd", "keyword difficulty"),
                            num("cpc", "cpc (usd)"), source, request.form.get("source_date") or None, db.now()))
                n += 1
            flash(f"Imported {n} keywords from {source}. Values are shown exactly as imported.", "ok")
        return redirect(url_for("admin.keywords"))
    rows = db.query("SELECT * FROM keywords ORDER BY COALESCE(search_volume, -1) DESC, keyword LIMIT 1000")
    targeted = {r["target_path"] for r in rows if r["target_path"]}
    untargeted = [p for p, i in linkgraph.registry().items() if p not in targeted and i["kind"] in
                  ("tool", "calculator", "guide", "category")]
    return render_template("admin/keywords.html", rows=rows, untargeted=untargeted, section="keywords")


@bp.route("/seo/search-performance/", methods=["GET", "POST"])
@auth.admin_required
def search_performance():
    if request.method == "POST":
        f = request.files.get("file")
        engine = request.form.get("engine") or "google"
        if not f:
            flash("Choose a CSV exported from Search Console (Pages or Queries tab) or Bing Webmaster Tools.", "error")
            return redirect(url_for("admin.search_performance"))
        reader = csv.DictReader(io.StringIO(f.read().decode("utf-8-sig", errors="replace")))
        n = 0
        site = current_app.config["SITE_URL"]
        for row in reader:
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            page = row.get("top pages") or row.get("page") or row.get("url")
            query = row.get("top queries") or row.get("query") or row.get("keyword")
            if page and page.startswith(site):
                page = page[len(site):] or "/"

            def num(k):
                v = row.get(k)
                try:
                    return float(v.replace(",", "").replace("%", "")) if v else None
                except ValueError:
                    return None
            ctr = num("ctr")
            db.execute("INSERT INTO search_performance(engine, path, query, clicks, impressions, ctr, position, "
                       "period_start, period_end, imported_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                       (engine, page, query, num("clicks"), num("impressions"), ctr, num("position") or num("avg. position"),
                        request.form.get("period_start") or None, request.form.get("period_end") or None, db.now()))
            n += 1
        flash(f"Imported {n} rows.", "ok")
        return redirect(url_for("admin.search_performance"))
    pages = db.query("SELECT engine, path, SUM(clicks) clicks, SUM(impressions) impressions, AVG(position) position, "
                     "MAX(period_end) period_end FROM search_performance WHERE path IS NOT NULL GROUP BY engine, path "
                     "ORDER BY clicks DESC LIMIT 200")
    queries = db.query("SELECT engine, query, SUM(clicks) clicks, SUM(impressions) impressions, AVG(position) position "
                       "FROM search_performance WHERE query IS NOT NULL GROUP BY engine, query ORDER BY clicks DESC LIMIT 200")
    return render_template("admin/search_performance.html", pages=pages, queries=queries, section="search")


# ---------------------------------------------------------------- listing moderation
@bp.get("/listings/")
@auth.admin_required
def listings():
    status = request.args.get("status", "pending")
    rows = db.query("SELECT l.*, u.email seller_email FROM listings l JOIN users u ON u.id=l.seller_id WHERE status=? "
                    "ORDER BY updated_at DESC LIMIT 200", (status,))
    out = []
    for r in rows:
        d = dict(r)
        d["path"] = M.listing_path(r)
        d["flags"] = M.decode_flags(r["quality_flags"])
        out.append(d)
    counts = {r["status"]: r["n"] for r in db.query("SELECT status, COUNT(*) n FROM listings GROUP BY status")}
    return render_template("admin/listings.html", rows=out, status=status, counts=counts, statuses=M.STATUSES,
                           section="listings")


@bp.post("/listings/<int:lid>/")
@auth.admin_required
def listing_action(lid):
    action = request.form.get("action")
    note = request.form.get("note") or None
    if action in ("published", "rejected", "suspended", "removed", "pending"):
        rep = request.form.get("replacement_id")
        M.set_status(lid, action, by=_who(), note=note, replacement_id=int(rep) if rep and rep.isdigit() else None)
    elif action == "verify":
        v = request.form.get("verification")
        if v in ("unverified", "revenue_verified", "traffic_verified", "fully_verified"):
            db.execute("UPDATE listings SET verification=?, updated_at=? WHERE id=?", (v, db.now(), lid))
            M.refresh(lid)
    elif action == "test":
        db.execute("UPDATE listings SET is_test=1-is_test WHERE id=?", (lid,))
        M.refresh(lid)
    flash(f"Listing #{lid} updated.", "ok")
    return redirect(request.referrer or url_for("admin.listings"))


# ---------------------------------------------------------------- blog CMS with publish gate
@bp.get("/blog/")
@auth.admin_required
def blog():
    return render_template("admin/blog.html", posts=db.query("SELECT * FROM blog_posts ORDER BY updated_at DESC"),
                           section="blog")


@bp.route("/blog/new/", methods=["GET", "POST"])
@bp.route("/blog/<int:pid>/", methods=["GET", "POST"])
@auth.admin_required
def blog_edit(pid=None):
    post = db.query("SELECT * FROM blog_posts WHERE id=?", (pid,), one=True) if pid else None
    if pid and not post:
        abort(404)
    issues, suggestions = [], []
    if request.method == "POST":
        f = {k: (request.form.get(k) or "").strip() for k in
             ("slug", "title", "h1", "summary", "body_md", "cluster", "primary_intent", "meta_title", "meta_description",
              "canonical_url", "robots_directive", "og_image", "reviewed_by")}
        f["slug"] = M.slugify(f["slug"] or f["title"])
        f["ai_assisted"] = 1 if request.form.get("ai_assisted") else 0
        want_publish = request.form.get("action") == "publish"
        if not f["title"] or not f["body_md"]:
            flash("Title and body are required.", "error")
            return render_template("admin/blog_edit.html", post=f, issues=[], suggestions=[], section="blog")
        clash = db.query("SELECT id FROM blog_posts WHERE slug=? AND id!=?", (f["slug"], pid or 0), one=True)
        if clash:
            flash("Another post already uses that URL slug.", "error")
            return render_template("admin/blog_edit.html", post=f, issues=[], suggestions=[], section="blog")
        t = db.now()
        if post:
            old_path = f"/blog/{post['slug']}/"
            db.execute("UPDATE blog_posts SET slug=?, title=?, h1=?, summary=?, body_md=?, cluster=?, primary_intent=?, "
                       "meta_title=?, meta_description=?, canonical_url=?, robots_directive=?, og_image=?, reviewed_by=?, "
                       "ai_assisted=?, updated_at=? WHERE id=?",
                       (f["slug"], f["title"], f["h1"] or None, f["summary"], f["body_md"], f["cluster"] or None,
                        f["primary_intent"] or None, f["meta_title"] or None, f["meta_description"] or None,
                        f["canonical_url"] or None, f["robots_directive"] or None, f["og_image"] or None,
                        f["reviewed_by"] or None, f["ai_assisted"], t, pid))
            if post["status"] == "published" and post["slug"] != f["slug"]:
                redirects.add_redirect(old_path, f"/blog/{f['slug']}/", _who(), "blog slug changed")
            for k in ("title", "meta_title", "meta_description", "canonical_url", "robots_directive"):
                if post["status"] == "published":
                    log_change(f"/blog/{f['slug']}/", k, post[k], f[k] or None, _who())
        else:
            pid = db.execute("INSERT INTO blog_posts(slug, title, h1, summary, body_md, cluster, primary_intent, meta_title, "
                             "meta_description, canonical_url, robots_directive, og_image, reviewed_by, ai_assisted, status, "
                             "updated_at, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,'draft',?,?)",
                             (f["slug"], f["title"], f["h1"] or None, f["summary"], f["body_md"], f["cluster"] or None,
                              f["primary_intent"] or None, f["meta_title"] or None, f["meta_description"] or None,
                              f["canonical_url"] or None, f["robots_directive"] or None, f["og_image"] or None,
                              f["reviewed_by"] or None, f["ai_assisted"], t, t))
        post = db.query("SELECT * FROM blog_posts WHERE id=?", (pid,), one=True)
        ok, issues = _gate(post)
        if want_publish:
            if post["ai_assisted"] and not post["reviewed_by"]:
                ok = False
                issues.append(("critical", "AI-assisted posts need a named human reviewer before publishing (§19)."))
            if ok:
                db.execute("UPDATE blog_posts SET status='published', published_at=COALESCE(published_at, ?), "
                           "reviewed_at=? WHERE id=?", (db.now(), db.now() if post["reviewed_by"] else None, pid))
                log_change(f"/blog/{post['slug']}/", "status", post["status"], "published", _who())
                flash("Published. It now appears in the blog, related links and the blog sitemap.", "ok")
                return redirect(url_for("admin.blog_edit", pid=pid))
            flash("Not published: fix the critical items below.", "error")
        else:
            flash("Draft saved.", "ok")
        suggestions = linkgraph.suggest_links(post["title"] + " " + post["body_md"])
        return render_template("admin/blog_edit.html", post=post, issues=issues, suggestions=suggestions, section="blog")
    if post:
        _ok, issues = _gate(post)
        suggestions = linkgraph.suggest_links(post["title"] + " " + post["body_md"])
    return render_template("admin/blog_edit.html", post=post, issues=issues, suggestions=suggestions, section="blog")


def _gate(post):
    """Render the draft exactly as it would publish and run the pre-publish checks."""
    from flask import render_template as rt
    from ..seo import PageMeta, abs_url
    from .. import schema as S
    path = f"/blog/{post['slug']}/"
    html_body, _ = content.render_md(post["body_md"])
    meta = PageMeta(path=path, title=post["title"], meta_title=post["meta_title"],
                    description=post["meta_description"] or post["summary"] or "", h1=post["h1"] or post["title"],
                    canonical=abs_url(post["canonical_url"]) if post["canonical_url"] else abs_url(path),
                    robots=post["robots_directive"] or "index, follow", og_type="article",
                    breadcrumbs=[("Blog", "/blog/"), (post["title"], path)], template="blog")
    author = content.AUTHORS.get(post["author_key"], content.AUTHORS["editorial"])
    meta.schema.append(S.article(path, meta.h1, meta.description, author, "2000-01-01", None))
    html = rt("blog_post.html", meta=meta, crumbs=[("Home", "/")] + meta.breadcrumbs, p=post, body=html_body,
              author=author, related=[], jsonld=S.graph([S.organization(), S.website(), S.breadcrumb_list(
                  [("Home", "/")] + meta.breadcrumbs)] + meta.schema))
    titles = {r["title"] for r in db.query("SELECT title FROM seo_audit_pages WHERE run_id=(SELECT MAX(id) FROM "
                                           "seo_audit_runs) AND path!=?", (path,)) if r["title"]}
    descs = {r["description"] for r in db.query("SELECT description FROM seo_audit_pages WHERE run_id=(SELECT MAX(id) "
                                                "FROM seo_audit_runs) AND path!=?", (path,)) if r["description"]}
    # Rendering the preview through base.html consumed the flash queue; reset it so
    # messages flashed after the gate still display.
    from flask.globals import request_ctx
    request_ctx.flashes = None
    return audit.prepublish_check(html, path, titles, descs)


# ---------------------------------------------------------------- analytics
@bp.get("/analytics/")
@auth.admin_required
def analytics_view():
    days = int(request.args.get("days", 30))
    steps_all, market_all = analytics.funnel(days)
    steps_org, market_org = analytics.funnel(days, "organic")
    landings = analytics.landing_pages(days)
    channels = db.query("SELECT channel, COUNT(DISTINCT session_id) n FROM events WHERE name='page_view' AND created_at>=? "
                        "GROUP BY channel ORDER BY n DESC", (db.now() - days * 86400,))
    return render_template("admin/analytics.html", days=days, steps_all=steps_all, steps_org=steps_org,
                           market_all=market_all, market_org=market_org, landings=landings, channels=channels,
                           vitals=analytics.vitals_summary(), section="analytics")


# ---------------------------------------------------------------- users & messages
@bp.route("/users/", methods=["GET", "POST"])
@auth.admin_required
def users():
    if request.method == "POST":
        uid = int(request.form.get("user_id", 0))
        plan = request.form.get("plan")
        if plan in ("free", "pro"):
            db.execute("UPDATE users SET plan=?, subscription_status=? WHERE id=?",
                       (plan, "active" if plan == "pro" else None, uid))
            flash("Plan updated (manual grant; no payment taken).", "ok")
        return redirect(url_for("admin.users"))
    rows = db.query("SELECT * FROM users ORDER BY created_at DESC LIMIT 500")
    return render_template("admin/users.html", rows=rows, section="users")


@bp.get("/messages/")
@auth.admin_required
def messages():
    rows = db.query("SELECT * FROM contact_messages ORDER BY created_at DESC LIMIT 300")
    return render_template("admin/messages.html", rows=rows, section="messages")
