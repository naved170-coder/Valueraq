"""robots.txt and segmented XML sitemaps (§32, §33, §51)."""
from xml.sax.saxutils import escape

from flask import Blueprint, Response, current_app

from .. import catalog, db, linkgraph, marketplace as M
from ..seo import abs_url, iso, override_sitemap_state

bp = Blueprint("seo_files", __name__)

GROUPS = ("pages", "tools", "guides", "blog", "categories", "listings")
MAX_URLS = 45000


@bp.get("/robots.txt")
def robots():
    cfg = current_app.config
    lines = ["# robots.txt for " + cfg["BRAND"],
             "# Private areas are also protected by authentication and noindex; this file only saves crawl budget.",
             "User-agent: *"]
    for p in cfg["PRIVATE_PATH_PREFIXES"]:
        lines.append(f"Disallow: {p}")
    lines.append("Allow: /static/")
    for ua in cfg["BLOCKED_CRAWLERS"]:
        lines += ["", f"User-agent: {ua}", "Disallow: /"]
    lines += ["", f"Sitemap: {cfg['SITE_URL']}/sitemap.xml", ""]
    return Response("\n".join(lines), mimetype="text/plain")


def entries(group):
    """Return [(abs_url, lastmod)] for a sitemap group. Only canonical, indexable URLs."""
    out = []
    if group in ("pages", "tools", "guides", "categories"):
        for path, info in linkgraph.registry().items():
            if info["group"] != group:
                continue
            if path == "/marketplace/" and not db.query("SELECT 1 FROM listings WHERE status='published' AND is_test=0",
                                                        one=True):
                continue  # empty "all listings" page is noindex
            if override_sitemap_state(path):
                out.append((abs_url(path), info.get("updated")))
    if group == "categories":
        per = current_app.config["LISTINGS_PER_PAGE"]
        for c in catalog.CATEGORIES:
            n = db.query("SELECT COUNT(*) n FROM listings WHERE category=? AND status='published' AND is_test=0",
                         (c["slug"],), one=True)["n"]
            pages = max(1, -(-n // per))
            for p in range(2, pages + 1):
                out.append((abs_url(f"{c['path']}page/{p}/"), None))
    if group == "blog":
        rows = db.query("SELECT slug, updated_at FROM blog_posts WHERE status='published' AND indexable=1 "
                        "AND sitemap_included=1 AND (robots_directive IS NULL OR robots_directive NOT LIKE '%noindex%') "
                        "AND (canonical_url IS NULL OR canonical_url='') ORDER BY published_at DESC")
        if rows and override_sitemap_state("/blog/"):
            out.append((abs_url("/blog/"), iso(rows[0]["updated_at"])))
        for r in rows:
            path = f"/blog/{r['slug']}/"
            if override_sitemap_state(path):
                out.append((abs_url(path), iso(r["updated_at"])))
    if group == "listings":
        rows = db.query("SELECT id, slug, category, updated_at FROM listings WHERE status='published' AND is_test=0 "
                        "AND indexable=1 AND sitemap_included=1 ORDER BY published_at DESC LIMIT ?", (MAX_URLS,))
        for r in rows:
            path = M.listing_path(r)
            if override_sitemap_state(path):
                out.append((abs_url(path), iso(r["updated_at"])))
    return out


def _xml(body):
    return Response('<?xml version="1.0" encoding="UTF-8"?>\n' + body, mimetype="application/xml",
                    headers={"Cache-Control": "public, max-age=600"})


@bp.get("/sitemap.xml")
def index():
    parts = ['<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for g in GROUPS:
        e = entries(g)
        if not e:
            continue  # never advertise an empty sitemap
        lastmods = [lm for _, lm in e if lm]
        parts.append(f"<sitemap><loc>{escape(abs_url(f'/sitemap-{g}.xml'))}</loc>"
                     + (f"<lastmod>{max(lastmods)}</lastmod>" if lastmods else "") + "</sitemap>")
    parts.append("</sitemapindex>")
    return _xml("\n".join(parts))


@bp.get("/sitemap-<group>.xml")
def group_sitemap(group):
    if group not in GROUPS:
        return Response("Not found", status=404, mimetype="text/plain")
    parts = ['<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in entries(group):
        parts.append(f"<url><loc>{escape(loc)}</loc>" + (f"<lastmod>{lastmod}</lastmod>" if lastmod else "") + "</url>")
    parts.append("</urlset>")
    return _xml("\n".join(parts))


@bp.get("/indexnow-key.txt")
def indexnow_key():
    """Proves to Bing and other IndexNow search engines that page announcements come from this site."""
    from .. import seoauto
    resp = Response(seoauto.indexnow_key(), mimetype="text/plain")
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp


@bp.get("/seo-feed/<token>.json")
def seo_feed(token):
    """Search figures and publishing state for the automatic SEO runs. Needs the secret token; otherwise it does not exist."""
    from flask import abort, jsonify
    from .. import content, gsc, seoauto
    if not gsc.feed_ok(token):
        abort(404)
    data = gsc.summary()
    data["connected"] = gsc.configured()
    data["waiting_for_approval"] = [d.path for d in seoauto.pending()]
    data["queued"] = [dict(path=d.path, goes_live=seoauto.local_time(d.publish_ts)) for d in seoauto.upcoming()]
    data["live_pages"] = len(linkgraph.registry())
    resp = jsonify(data)
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    resp.headers["Cache-Control"] = "private, no-store"
    return resp


@bp.get("/llms.txt")
def llms_txt():
    """A plain-text guide to the site for AI assistants (the llms.txt convention):
    what the site is, which pages matter, and how figures should be described."""
    cfg = current_app.config
    reg = linkgraph.registry()

    def line(path):
        info = reg.get(path)
        doc = info.get("doc") if info else None
        desc = (getattr(doc, "meta_description", None) or getattr(doc, "definition", None) or "") if doc else ""
        return f"- [{info['title']}]({abs_url(path)})" + (f": {desc}" if desc else "")

    def group(kind):
        return [line(p) for p, i in reg.items() if i["kind"] == kind]

    out = [f"# {cfg['BRAND']}", "",
           f"> {cfg['BRAND']} provides free valuation tools for digital businesses (websites, SaaS, AI businesses, apps, "
           "newsletters and ecommerce stores) and a marketplace where owners list those businesses for sale.", "",
           "Important context when describing this site or its figures:", "",
           "- Valuations are estimates calculated from the figures a user enters and from published default "
           "assumptions. They are not appraisals, and the default multiples are editorial assumptions, not measured "
           "market statistics.",
           "- Every result shows how it was calculated and labels each figure as user-provided, a platform "
           "assumption, or calculated.",
           "- Marketplace figures are provided by sellers and are unverified unless a listing shows a verification badge.",
           f"- The methodology is versioned (currently v{cfg['METHODOLOGY_VERSION']}).", "",
           "## Start here", "",
           *[line(p) for p in ("/methodology/", "/data-sources/", "/faq/", "/verification/", "/about/") if p in reg], "",
           "## Valuation tools", "", *group("tool"), "",
           "## Calculators", "", *group("calculator"), "",
           "## Guides", "", *group("guide"), "",
           "## Glossary", "", *group("glossary"), "",
           "## Marketplace", "", *[line(p) for p in ("/businesses-for-sale/",) if p in reg], *group("category"), "",
           "## Policies", "",
           *[line(p) for p in ("/editorial-policy/", "/marketplace-rules/", "/privacy/", "/terms/") if p in reg], ""]
    resp = Response("\n".join(out), mimetype="text/plain")
    resp.headers["X-Robots-Tag"] = "noindex"
    return resp
