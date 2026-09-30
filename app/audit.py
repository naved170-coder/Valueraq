"""SEO QA crawler (§58–61, §69, §80–81).

Renders pages in-process (no network), so it can run in CI, from the admin
dashboard, or from the command line:

    python -m app.audit            # prints a summary, exits 1 on critical issues
"""
import json
import time
from collections import defaultdict
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from flask import current_app

from . import db, redirects, schema
from .views.seo_files import GROUPS, entries

CONTENT_TEMPLATES = {"guide", "glossary", "tool", "calculator", "page", "category", "home", "blog", "hub"}
EXTRA_PROBES = [
    # Must be noindex (or 404) — verifies private/utility handling.
    ("/search/?q=saas", "noindex"), ("/login/", "noindex"), ("/signup/", "noindex"), ("/sell/", "noindex"),
    ("/businesses-for-sale/saas/?sort=price_asc", "noindex"), ("/account/", "redirect"),
    ("/admin/", "redirect"), ("/this-page-does-not-exist/", 404), ("/businesses-for-sale/saas/page/999/", 404),
]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self._in_title = False
        self.description = None
        self.canonical = None
        self.robots = None
        self.h1 = 0
        self.links = []
        self.main_links = []   # contextual links inside <main> (nav/footer excluded)
        self.imgs_no_alt = 0
        self.jsonld = []
        self._in_ld = False
        self._ld_buf = []
        self._skip = 0
        self._in_main = 0
        self.text = []
        self.og = {}
        self.template = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            n = (a.get("name") or "").lower()
            if n == "description":
                self.description = a.get("content")
            elif n == "robots":
                self.robots = a.get("content")
            if (a.get("property") or "").startswith("og:"):
                self.og[a["property"]] = a.get("content")
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical":
            self.canonical = a.get("href")
        elif tag == "h1":
            self.h1 += 1
        elif tag == "a" and a.get("href"):
            self.links.append((a["href"], a.get("rel") or ""))
            if self._in_main > 0:
                self.main_links.append(a["href"])
        elif tag == "img" and not a.get("alt") and a.get("alt") != "":
            self.imgs_no_alt += 1
        elif tag == "script":
            if (a.get("type") or "") == "application/ld+json":
                self._in_ld = True
                self._ld_buf = []
            else:
                self._skip += 1
        elif tag in ("style", "noscript"):
            self._skip += 1
        elif tag == "main":
            self._in_main += 1
        elif tag == "body":
            self.template = a.get("data-template")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            if self._in_ld:
                self.jsonld.append("".join(self._ld_buf))
                self._in_ld = False
            elif self._skip:
                self._skip -= 1
        elif tag in ("style", "noscript") and self._skip:
            self._skip -= 1
        elif tag == "main":
            self._in_main -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data
        elif self._in_ld:
            self._ld_buf.append(data)
        elif not self._skip and self._in_main > 0:
            self.text.append(data)


def _fetch(client, path):
    t = time.perf_counter()
    r = client.get(path, headers={"Accept": "text/html", "X-VQ-Audit": "1"})
    ms = (time.perf_counter() - t) * 1000
    return r, ms


def _internal(href, base_path):
    if href.startswith(("mailto:", "tel:", "#", "javascript:")):
        return None
    site = current_app.config["SITE_URL"]
    if href.startswith(site):
        href = href[len(site):] or "/"
    if href.startswith("http://") or href.startswith("https://") or href.startswith("//"):
        return None
    full = urljoin(base_path, href)
    parts = urlsplit(full)
    return parts.path + (("?" + parts.query) if parts.query else "")


def run(max_pages=3000, store=True):
    app = current_app._get_current_object()
    cfg = app.config
    site = cfg["SITE_URL"]
    client = app.test_client()
    started = db.now()

    sitemap_paths = set()
    for g in GROUPS:
        for loc, _ in entries(g):
            sitemap_paths.add(loc[len(site):] if loc.startswith(site) else loc)

    queue = ["/"] + sorted(sitemap_paths)
    seen = set()
    pages = {}
    inbound = defaultdict(set)
    broken = defaultdict(set)

    while queue and len(seen) < max_pages:
        path = queue.pop(0)
        if path in seen:
            continue
        seen.add(path)
        r, ms = _fetch(client, path)
        info = dict(path=path, status=r.status_code, render_ms=round(ms, 1), bytes=len(r.data),
                    x_robots=r.headers.get("X-Robots-Tag"), location=r.headers.get("Location"))
        if r.status_code == 200 and r.mimetype == "text/html":
            p = PageParser()
            p.feed(r.get_data(as_text=True))
            info.update(title=(p.title or "").strip(), description=p.description, canonical=p.canonical,
                        robots=p.robots or "", h1=p.h1, imgs_no_alt=p.imgs_no_alt, template=p.template,
                        words=len(" ".join(p.text).split()), jsonld=p.jsonld, og=p.og)
            for href in p.main_links:
                target = _internal(href, path)
                if target:
                    clean = target.split("?")[0]
                    if clean != path:
                        inbound[clean].add(path)
            for href, rel in p.links:
                target = _internal(href, path)
                if not target or target.startswith(("/static/", "/api/")):
                    continue
                clean = target.split("?")[0]
                if clean not in seen and "?" not in target and not any(
                        clean.startswith(pp) for pp in cfg["PRIVATE_PATH_PREFIXES"]):
                    queue.append(clean)
                info.setdefault("out", set()).add(clean)
        pages[path] = info

    # Link targets that failed.
    for path, info in pages.items():
        for target in info.get("out", ()):
            t = pages.get(target)
            if t and t["status"] >= 400:
                broken[path].add(target)
            if t and t["status"] in (301, 302, 307, 308):
                info.setdefault("links_to_redirect", set()).add(target)

    # Probes.
    probe_results = []
    for path, expect in EXTRA_PROBES:
        r, _ = _fetch(client, path)
        ok = True
        if expect == "noindex":
            p = PageParser()
            p.feed(r.get_data(as_text=True))
            ok = r.status_code in (200, 302) and ("noindex" in (p.robots or "") or "noindex" in (r.headers.get("X-Robots-Tag") or ""))
            if r.status_code == 200 and p.canonical and "?" in p.canonical:
                ok = False
        elif expect == "redirect":
            ok = r.status_code in (301, 302, 303) and "noindex" in (r.headers.get("X-Robots-Tag") or "noindex")
        else:
            ok = r.status_code == expect
        probe_results.append(dict(path=path, expect=expect, status=r.status_code, ok=ok))

    # Per-page checks.
    titles, descs = defaultdict(list), defaultdict(list)
    results = []
    for path, info in pages.items():
        issues = []
        indexable = info["status"] == 200 and "noindex" not in (info.get("robots") or "") and \
            "noindex" not in (info.get("x_robots") or "")

        def add(sev, code, msg):
            issues.append(dict(severity=sev, code=code, message=msg))

        if info["status"] >= 400:
            add("critical" if path in sitemap_paths else "warning", "status", f"Returns HTTP {info['status']}.")
        if info["status"] in (301, 302, 307, 308) and path in sitemap_paths:
            add("critical", "sitemap_redirect", "Sitemap URL redirects.")
        if info["status"] == 200 and info.get("title") is not None:
            if path in sitemap_paths and not indexable:
                add("critical", "sitemap_noindex", "Sitemap contains a noindex URL.")
            if indexable:
                titles[info["title"]].append(path)
                if info.get("description"):
                    descs[info["description"]].append(path)
                if not info["title"]:
                    add("critical", "title_missing", "Missing <title>.")
                elif len(info["title"]) > 70:
                    add("warning", "title_long", f"Title is {len(info['title'])} characters; may be truncated.")
                if not info.get("description"):
                    add("critical", "desc_missing", "Missing meta description.")
                elif not (cfg["DESCRIPTION_MIN"] <= len(info["description"]) <= cfg["DESCRIPTION_MAX"] + 10):
                    add("warning", "desc_length", f"Meta description is {len(info['description'])} characters.")
                expected = site + path
                if not info.get("canonical"):
                    add("critical", "canonical_missing", "Missing canonical.")
                elif info["canonical"] != expected:
                    add("warning", "canonical_other", f"Canonical points to {info['canonical']}.")
                if info["h1"] == 0:
                    add("critical", "h1_missing", "No H1.")
                elif info["h1"] > 1:
                    add("warning", "h1_multiple", f"{info['h1']} H1 elements.")
                if path not in sitemap_paths:
                    add("warning", "not_in_sitemap", "Indexable page is missing from the sitemaps.")
                if info.get("template") in CONTENT_TEMPLATES and info["words"] < cfg["THIN_WORDS"] and path != "/":
                    add("warning", "thin", f"Only {info['words']} words of main content.")
                if not info.get("og", {}).get("og:title") or not info.get("og", {}).get("og:image"):
                    add("warning", "og_missing", "Open Graph title or image missing.")
                n_in = len(inbound.get(path, ()))
                if n_in == 0 and path != "/":
                    add("critical", "orphan", "No links from any page's main content point here (menus and footers aren't counted).")
                elif n_in < 3 and path != "/":
                    add("info", "weak_links", f"Only {n_in} page{'' if n_in == 1 else 's'} link{'s' if n_in == 1 else ''} here.")
            # Structured data.
            types = []
            for raw in info.get("jsonld", []):
                try:
                    doc = json.loads(raw)
                except ValueError:
                    add("critical", "schema_parse", "JSON-LD does not parse.")
                    continue
                t, errs = schema.validate(doc)
                types += t
                for e in errs:
                    add("critical", "schema_invalid", e)
            info["schema_types"] = types
            if indexable and not types:
                add("warning", "schema_missing", "No structured data.")
            if info.get("imgs_no_alt"):
                add("warning", "img_alt", f"{info['imgs_no_alt']} images without alt text.")
            if info["render_ms"] > 800:
                add("warning", "slow", f"Server render took {info['render_ms']:.0f} ms.")
            if info["bytes"] > 250_000:
                add("warning", "heavy", f"HTML is {info['bytes'] // 1024} KB.")
        for target in sorted(broken.get(path, ())):
            add("critical", "broken_link", f"Links to {target}, which returns an error.")
        for target in sorted(info.get("links_to_redirect", ())):
            add("info", "link_to_redirect", f"Links to {target}, which redirects. Update the link.")
        info["issues"] = issues
        info["indexable"] = indexable
        info["inbound"] = len(inbound.get(path, ()))
        info["score"] = score(info, issues) if indexable else None
        results.append(info)

    for t, paths in titles.items():
        if len(paths) > 1:
            for pth in paths:
                pages[pth]["issues"].append(dict(severity="critical", code="title_duplicate",
                                                 message=f"Title shared with {len(paths) - 1} other page(s)."))
    for d, paths in descs.items():
        if len(paths) > 1:
            for pth in paths:
                pages[pth]["issues"].append(dict(severity="warning", code="desc_duplicate",
                                                 message=f"Meta description shared with {len(paths) - 1} other page(s)."))

    chain_rows = redirects.chains()
    site_issues = []
    for c in chain_rows:
        site_issues.append(dict(severity="critical", code="redirect_chain",
                                message=f"{c['from_path']} → {c['to_path']} → {c['final']}"))
    for p in probe_results:
        if not p["ok"]:
            site_issues.append(dict(severity="critical", code="probe",
                                    message=f"{p['path']} expected {p['expect']}, got HTTP {p['status']}."))
    robots_txt = client.get("/robots.txt").get_data(as_text=True)
    for must_allow in ("/tools/", "/guides/", "/businesses-for-sale/", "/marketplace/", "/static/"):
        for line in robots_txt.splitlines():
            if line.strip().lower() == f"disallow: {must_allow}":
                site_issues.append(dict(severity="critical", code="robots_block", message=f"robots.txt blocks {must_allow}"))
    if "Disallow: /\n" in robots_txt.split("User-agent: *", 1)[-1].split("User-agent:", 1)[0] + "\n":
        site_issues.append(dict(severity="critical", code="robots_block_all", message="robots.txt blocks the whole site."))

    all_issues = [i for r in results for i in r["issues"]] + site_issues
    summary = dict(
        pages=len(results),
        indexable=sum(1 for r in results if r["indexable"]),
        noindex=sum(1 for r in results if r["status"] == 200 and not r["indexable"]),
        sitemap_urls=len(sitemap_paths),
        critical=sum(1 for i in all_issues if i["severity"] == "critical"),
        warnings=sum(1 for i in all_issues if i["severity"] == "warning"),
        info=sum(1 for i in all_issues if i["severity"] == "info"),
        by_code=_count_codes(all_issues),
        site_issues=site_issues,
        probes=probe_results,
        avg_score=round(sum(r["score"] for r in results if r["score"] is not None) /
                        max(1, sum(1 for r in results if r["score"] is not None)), 1),
    )
    changes = []
    if store:
        prev = db.query("SELECT id FROM seo_audit_runs WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1", one=True)
        rid = db.execute("INSERT INTO seo_audit_runs(started_at) VALUES (?)", (started,))
        conn = db.get_db()
        conn.executemany(
            "INSERT INTO seo_audit_pages(run_id, path, status, title, description, canonical, robots, h1_count, words,"
            " inbound, score, issues_json, schema_types, render_ms, bytes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [(rid, r["path"], r["status"], r.get("title"), r.get("description"), r.get("canonical"),
              r.get("robots") or r.get("x_robots"), r.get("h1"), r.get("words"), r["inbound"], r["score"],
              json.dumps(r["issues"]), ",".join(sorted(set(r.get("schema_types", [])))), r["render_ms"], r["bytes"])
             for r in results])
        conn.commit()
        if prev:
            changes = diff_runs(prev["id"], rid)
        summary["changes"] = len(changes)
        db.execute("UPDATE seo_audit_runs SET finished_at=?, pages=?, critical=?, warnings=?, summary_json=? WHERE id=?",
                   (db.now(), summary["pages"], summary["critical"], summary["warnings"],
                    json.dumps(dict(summary, change_list=changes[:200])), rid))
        summary["run_id"] = rid
    summary["change_list"] = changes
    return summary, sorted(results, key=lambda r: (-(sum(i["severity"] == "critical" for i in r["issues"])), r["path"]))


def score(info, issues):
    """Internal QA score (0–100). NOT a ranking prediction (§60)."""
    s = dict(technical=30, content=25, linking=20, schema=10, performance=15)
    for i in issues:
        c = i["code"]
        if c in ("title_missing", "desc_missing", "canonical_missing", "h1_missing", "status", "sitemap_noindex",
                 "title_duplicate"):
            s["technical"] -= 10
        elif c in ("title_long", "desc_length", "canonical_other", "h1_multiple", "not_in_sitemap", "og_missing",
                   "desc_duplicate"):
            s["technical"] -= 3
        elif c == "thin":
            s["content"] -= 15
        elif c == "orphan":
            s["linking"] -= 20
        elif c == "weak_links":
            s["linking"] -= 6
        elif c in ("broken_link",):
            s["linking"] -= 8
        elif c.startswith("schema"):
            s["schema"] -= 5 if c == "schema_missing" else 10
        elif c in ("slow", "heavy"):
            s["performance"] -= 7
        elif c == "img_alt":
            s["content"] -= 3
    return max(0, sum(max(0, v) for v in s.values()))


def _count_codes(issues):
    out = defaultdict(int)
    for i in issues:
        out[i["code"]] += 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def diff_runs(old_id, new_id):
    """Monitor unusual changes (§69): titles, descriptions, canonicals, robots, schema, disappearance."""
    old = {r["path"]: r for r in db.query("SELECT * FROM seo_audit_pages WHERE run_id=?", (old_id,))}
    new = {r["path"]: r for r in db.query("SELECT * FROM seo_audit_pages WHERE run_id=?", (new_id,))}
    changes = []
    for path, n in new.items():
        o = old.get(path)
        if not o:
            changes.append(dict(path=path, field="page", old=None, new="new page"))
            continue
        for f in ("status", "title", "description", "canonical", "robots", "schema_types"):
            if (o[f] or "") != (n[f] or ""):
                changes.append(dict(path=path, field=f, old=o[f], new=n[f]))
    for path in old:
        if path not in new:
            changes.append(dict(path=path, field="page", old="present", new="no longer crawled"))
    return changes


def last_run():
    r = db.query("SELECT * FROM seo_audit_runs WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1", one=True)
    if not r:
        return None, []
    rows = db.query("SELECT * FROM seo_audit_pages WHERE run_id=? ORDER BY path", (r["id"],))
    pages = []
    for p in rows:
        d = dict(p)
        d["issues"] = json.loads(p["issues_json"] or "[]")
        pages.append(d)
    return dict(r, summary=json.loads(r["summary_json"] or "{}")), pages


def prepublish_check(html, path, existing_titles=(), existing_descs=()):
    """Gate for blog posts / overrides (§59). Returns (ok, issues)."""
    p = PageParser()
    p.feed(html)
    issues = []
    site = current_app.config["SITE_URL"]
    if not p.title or not p.title.strip():
        issues.append(("critical", "Missing title."))
    elif p.title.strip() in existing_titles:
        issues.append(("critical", "Another page already uses this title."))
    if not p.description:
        issues.append(("critical", "Missing meta description."))
    elif p.description in existing_descs:
        issues.append(("critical", "Another page already uses this meta description."))
    if p.canonical != site + path:
        issues.append(("critical", f"Canonical should be {site + path}."))
    if p.h1 != 1:
        issues.append(("critical", f"Page must have exactly one H1 (found {p.h1})."))
    if "noindex" in (p.robots or ""):
        issues.append(("warning", "Page is set to noindex."))
    words = len(" ".join(p.text).split())
    if words < current_app.config["THIN_WORDS"]:
        issues.append(("critical", f"Only {words} words; publish at least {current_app.config['THIN_WORDS']}."))
    internal = [h for h, _ in p.links if _internal(h, path)]
    if len(internal) < 3:
        issues.append(("warning", "Few internal links."))
    if p.imgs_no_alt:
        issues.append(("critical", f"{p.imgs_no_alt} images are missing alt text."))
    for raw in p.jsonld:
        try:
            _t, errs = schema.validate(json.loads(raw))
            issues += [("critical", e) for e in errs]
        except ValueError:
            issues.append(("critical", "Structured data doesn't parse."))
    return not any(s == "critical" for s, _ in issues), issues


if __name__ == "__main__":
    import sys
    from . import create_app
    application = create_app()
    with application.app_context():
        summ, res = run(store=False)
        print(json.dumps({k: v for k, v in summ.items() if k not in ("change_list",)}, indent=2, default=str))
        for r in res:
            crit = [i for i in r["issues"] if i["severity"] == "critical"]
            if crit:
                print(r["path"], [i["message"] for i in crit])
        sys.exit(1 if summ["critical"] else 0)
