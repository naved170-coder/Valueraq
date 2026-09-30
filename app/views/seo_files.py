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
