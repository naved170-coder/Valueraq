"""Build the VALUERAQ audit package data (crawl, SEO audit, HTML snapshots, schema, headers).

    python scripts/build_audit_package.py OUT_DIR

Runs the real application against a fresh local database seeded with a few
clearly marked SAMPLE listings, a demo admin and a demo report, so every page
type (including marketplace and account pages) can be inspected. Nothing here
reads or changes the live site's database.
"""
import csv
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import audit, create_app, db, marketplace as M, schema  # noqa: E402
from app.config import Config  # noqa: E402

SAMPLE_DESC = (
    "SAMPLE LISTING FOR AUDIT PURPOSES. {what} The business has run for {age} years with steady demand and "
    "documented processes. Revenue comes from {model}. The owner spends about ten hours a week on content "
    "planning, supplier contact and customer email, and has written procedures for each task so a new owner "
    "can take over quickly. Traffic and sales history are available to serious buyers after a short call. "
    "Assets include the domain, the site or app, social accounts, the email list, supplier contacts and all "
    "content. The seller will provide thirty days of handover support and answer questions about operations, "
    "costs and growth ideas. Growth opportunities include new product lines, paid acquisition, partnerships "
    "and improving conversion on the main landing pages. The reason for sale is a change of focus to other projects."
)
SAMPLES = [
    ("websites", "Sample recipe website with affiliate income", "Affiliate content site", "a recipe and kitchen-gear content site.",
     "affiliate commissions and display ads", 4, 180000, 6000, 4500),
    ("saas", "Sample scheduling SaaS for dental clinics", "B2B SaaS", "a scheduling product for dental clinics.",
     "monthly subscriptions", 3, 480000, 20000, 9000),
    ("ecommerce", "Sample ecommerce store for eco cleaning products", "Ecommerce (own brand)",
     "an online store selling eco-friendly cleaning products.", "direct product sales", 5, 260000, 40000, 7000),
]

LOGGED_OUT_PAGES = ["/login/", "/signup/", "/sell/", "/search/?q=saas"]
PRIVATE_PAGES = ["/account/", "/account/reports/", "/account/listings/", "/account/inquiries/", "/account/billing/",
                 "/account/settings/", "/admin/", "/admin/seo/", "/admin/seo/redirects/", "/admin/seo/log/",
                 "/admin/seo/keywords/", "/admin/seo/search-performance/", "/admin/listings/", "/admin/blog/",
                 "/admin/blog/new/", "/admin/analytics/", "/admin/users/", "/admin/messages/"]

TECH_CHECKS = [
    ("Uppercase URL is redirected to lowercase", "/Tools/Website-Valuation/"),
    ("Missing trailing slash is redirected", "/tools/website-valuation"),
    ("URL with tracking parameter", "/tools/website-valuation/?utm_source=test"),
    ("Filtered marketplace URL (noindex expected)", "/businesses-for-sale/saas/?sort=price_asc"),
    ("Unknown page returns 404", "/this-page-does-not-exist/"),
    ("robots.txt", "/robots.txt"),
    ("XML sitemap index", "/sitemap.xml"),
    ("Admin hidden from non-admins (404 expected when logged out)", "/admin/"),
    ("Account requires login (redirect expected)", "/account/"),
]


def slug(path):
    s = path.strip("/").replace("/", "__") or "home"
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", s)


def write(path, text, mode="w"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode, encoding=None if "b" in mode else "utf-8") as fh:
        fh.write(text)


def seed(app):
    from app import auth
    with app.app_context():
        uid = auth.create_user("demo-admin@example.com", "demo-admin-password-1", name="Demo Admin")
        db.execute("UPDATE users SET role='admin' WHERE id=?", (uid,))
        seller = auth.create_user("demo-seller@example.com", "demo-seller-password-1", name="Demo Seller")
        for cat, title, model, what, money, age, price, rev, profit in SAMPLES:
            t = db.now()
            lid = db.execute(
                "INSERT INTO listings(seller_id, category, slug, title, headline, description, business_model, industry, "
                "country, asking_price, monthly_revenue, monthly_profit, age_years, status, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (seller, cat, M.slugify(title), title, f"{model}, {age} years trading", SAMPLE_DESC.format(
                    what=what.capitalize(), age=age, model=money), model, "Sample", "United States", price, rev,
                 profit, age, "pending", t, t))
            M.refresh(lid)
            M.set_status(lid, "published", by="audit-package")
    return uid


def main(out):
    tmp = tempfile.mkdtemp()
    app = create_app(Config, DATABASE_PATH=os.path.join(tmp, "audit.db"), ENFORCE_CANONICAL_HOST=False,
                     SESSION_COOKIE_SECURE=False)
    seed(app)
    c = app.test_client()
    site = app.config["SITE_URL"]

    # ---------------------------------------------------------- built-in SEO audit (crawls every public page)
    with app.app_context():
        summary, results = audit.run(store=True)
    summary.pop("change_list", None)
    write(f"{out}/03-seo-audit/seo_audit_summary.json", json.dumps(summary, indent=2, default=str))
    with open(f"{out}/03-seo-audit/seo_audit_pages.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "http_status", "quality_score_0_100", "title", "title_length", "meta_description",
                    "description_length", "canonical", "robots", "h1_count", "words_in_main", "inbound_internal_links",
                    "schema_types", "server_render_ms", "html_bytes", "issue_count", "issues"])
        for r in sorted(results, key=lambda r: r["path"]):
            w.writerow([r["path"], r["status"], r["score"], r.get("title"), len(r.get("title") or ""),
                        r.get("description"), len(r.get("description") or ""), r.get("canonical"),
                        r.get("robots") or r.get("x_robots"), r.get("h1"), r.get("words"), r["inbound"],
                        ",".join(sorted(set(r.get("schema_types", [])))), round(r["render_ms"], 1), r["bytes"],
                        len(r["issues"]), " | ".join(f"{i['severity']}:{i['code']}" for i in r["issues"])])
    with open(f"{out}/03-seo-audit/seo_issues.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "severity", "code", "message"])
        for r in results:
            for i in r["issues"]:
                w.writerow([r["path"], i["severity"], i["code"], i.get("message") or i.get("msg") or ""])

    # ---------------------------------------------------------- page snapshots, headers, JSON-LD, links
    paths = sorted(r["path"] for r in results)
    headers_out, schema_rows, edges = {}, [], []
    for p in paths:
        r = c.get(p)
        html = r.get_data(as_text=True)
        write(f"{out}/02-pages/public-html/{slug(p)}.html", html)
        headers_out[p] = {"status": r.status_code, **{k: v for k, v in r.headers.items() if k.lower() != "set-cookie"}}
        parser = audit.PageParser()
        parser.feed(html)
        for href in sorted(set(parser.main_links)):
            edges.append((p, href))
        for i, block in enumerate(parser.jsonld):
            try:
                doc = json.loads(block)
            except ValueError as e:
                schema_rows.append([p, "INVALID JSON", str(e)])
                continue
            write(f"{out}/04-structured-data/json-ld/{slug(p)}{'' if i == 0 else '-' + str(i)}.json",
                  json.dumps(doc, indent=2))
            types, problems = schema.validate(doc)
            types = sorted({t if isinstance(t, str) else ",".join(t) for t in types})
            schema_rows.append([p, ";".join(types), "; ".join(problems) if problems else "OK"])
    write(f"{out}/02-pages/response_headers.json", json.dumps(headers_out, indent=2))
    with open(f"{out}/04-structured-data/schema_validation.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "schema_types", "validation_result"])
        w.writerows(schema_rows)
    with open(f"{out}/03-seo-audit/internal_links.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["from_page", "to_href (links inside <main>, nav/footer excluded)"])
        w.writerows(edges)

    # ---------------------------------------------------------- robots.txt and sitemaps
    write(f"{out}/05-seo-files/robots.txt", c.get("/robots.txt").get_data(as_text=True))
    idx = c.get("/sitemap.xml").get_data(as_text=True)
    write(f"{out}/05-seo-files/sitemap.xml", idx)
    for loc in re.findall(r"<loc>([^<]+)</loc>", idx):
        name = loc.rsplit("/", 1)[-1]
        write(f"{out}/05-seo-files/{name}", c.get(loc.replace(site, "")).get_data(as_text=True))

    # ---------------------------------------------------------- technical behaviour checks
    with open(f"{out}/03-seo-audit/technical_checks.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["check", "request", "status", "location_header", "x_robots_tag", "meta_robots", "canonical"])
        fresh = app.test_client()
        for label, p in TECH_CHECKS:
            r = fresh.get(p)
            body = r.get_data(as_text=True)
            mr = re.search(r'<meta name="robots" content="([^"]+)"', body)
            cn = re.search(r'<link rel="canonical" href="([^"]+)"', body)
            w.writerow([label, p, r.status_code, r.headers.get("Location", ""), r.headers.get("X-Robots-Tag", ""),
                        mr.group(1) if mr else "", cn.group(1) if cn else ""])

    # ---------------------------------------------------------- tool and calculator results
    from app import valuation as V
    for key, ex in V.EXAMPLES.items():
        r = c.post(f"/tools/result/{key}/", data={k: str(v) for k, v in ex.items()}, headers={"Accept": "application/json"})
        write(f"{out}/02-pages/tool-results/{key}-example-result.html", r.json.get("html", json.dumps(r.json)))
    os.makedirs(f"{out}/06-valuation-engine", exist_ok=True)
    with open(f"{out}/06-valuation-engine/example_valuations.json", "w", encoding="utf-8") as fh:
        json.dump({k: {"inputs": ex, "result": V.value_business(k, V.parse_inputs(k, {a: str(b) for a, b in ex.items()}))}
                   for k, ex in V.EXAMPLES.items()}, fh, indent=2, default=str)
    write(f"{out}/06-valuation-engine/base_multiples_and_rules.json", json.dumps({
        "methodology_version": V.METHODOLOGY_VERSION,
        "base_multiples": V.BASE,
        "required_inputs": V.REQUIRED,
        "tool_inputs": V.TOOL_INPUTS,
        "adjustment_rules": [{k: (v if k != "bands" else [b[0] + f" -> {b[2]:+.0%}: {b[3]}" for b in v])
                              for k, v in r.items() if k != "mapping"} | (
                                 {"mapping": {o: f"{e:+.0%}: {why}" for o, (e, why) in r["mapping"].items()}}
                                 if "mapping" in r else {}) for r in V.RULES],
    }, indent=2, default=str))

    # ---------------------------------------------------------- noindex utility pages (logged out)
    for p in LOGGED_OUT_PAGES:
        write(f"{out}/02-pages/noindex-html/{slug(p)}.html", app.test_client().get(p).get_data(as_text=True))

    # ---------------------------------------------------------- private pages (as a demo admin)
    with c.session_transaction() as s:
        s["csrf"] = "audit"
    c.post("/login/", data={"email": "demo-admin@example.com", "password": "demo-admin-password-1", "csrf": "audit"})
    c.post("/tools/result/website/", data={k: str(v) for k, v in V.EXAMPLES["website"].items()})
    c.get("/account/reports/new/")
    for p in PRIVATE_PAGES:
        r = c.get(p)
        write(f"{out}/02-pages/private-html/{slug(p)}.html", r.get_data(as_text=True))
    print(f"{len(paths)} public pages, {len(PRIVATE_PAGES)} private pages, "
          f"{summary.get('critical')} critical / {summary.get('warnings')} warnings")
    return os.path.join(tmp, "audit.db")


if __name__ == "__main__":
    print(main(sys.argv[1]))
