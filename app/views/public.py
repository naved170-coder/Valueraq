"""Public, indexable pages: home, tools, calculators, guides, glossary, trust pages, blog, search."""
import json
import re

from flask import (Blueprint, abort, flash, g, jsonify, redirect, render_template, request,
                   session)

from .. import analytics, auth, catalog, content, db, linkgraph, schema, valuation as V
from ..seo import PageMeta, abs_url, iso
from . import render_page

bp = Blueprint("public", __name__)


# ---------------------------------------------------------------- home
@bp.get("/")
def home():
    ex_tool = "website"
    ex_inputs = V.parse_inputs(ex_tool, {k: str(v) for k, v in V.EXAMPLES[ex_tool].items()})
    example = V.value_business(ex_tool, ex_inputs)
    counts = {r["category"]: r["n"] for r in db.query(
        "SELECT category, COUNT(*) n FROM listings WHERE status='published' AND is_test=0 GROUP BY category")}
    guides = content.list_docs("guides")[:6]
    meta = PageMeta(
        path="/",
        title="Digital Business Valuation & Marketplace",
        meta_title="VALUERAQ – Value, Buy and Sell Digital Businesses",
        description="All valuation features, at much lower fees than the leading marketplaces. Free tools for "
                    "websites, SaaS, AI, apps, newsletters and ecommerce.",
        h1="What is your digital business worth?",
        template="home",
    )
    meta.schema.append(schema.web_page("/", meta.title, meta.description))
    return render_page("home.html", meta, example=example, ex_inputs=ex_inputs, counts=counts, guides=guides)


# ---------------------------------------------------------------- tools
@bp.get("/tools/")
def tools_hub():
    meta = PageMeta(
        path="/tools/", title="Digital Business Valuation Tools",
        meta_title="Digital Business Valuation Tools – Free Online Business Valuation",
        description="Six free valuation tools for websites, SaaS, AI businesses, apps, newsletters and ecommerce "
                    "stores. Each one shows its inputs, multiples, adjustments and limitations.",
        breadcrumbs=[("Valuation tools", "/tools/")], template="hub")
    meta.schema.append(schema.collection_page("/tools/", meta.title, meta.description,
                                              [(t["name"], t["path"]) for t in catalog.TOOLS]))
    doc = content.load("hubs", "tools")
    return render_page("hub_tools.html", meta, doc=doc, tools=catalog.TOOLS, calcs=catalog.CALCULATORS,
                       base=V.BASE, type_label=V.TYPE_LABEL)


@bp.get("/tools/<slug>/")
def tool(slug):
    t = catalog.TOOLS_BY_SLUG.get(slug)
    if not t:
        abort(404)
    doc = content.load("tools", slug)
    key = t["key"]
    ex_inputs = V.parse_inputs(key, {k: str(v) for k, v in V.EXAMPLES[key].items()})
    example = V.value_business(key, ex_inputs)
    meta = PageMeta(path=t["path"], title=t["name"], meta_title=t["meta_title"], description=t["description"],
                    h1=doc.h1 if doc and doc.h1 else t["name"], breadcrumbs=[("Valuation tools", "/tools/"), (t["name"], t["path"])],
                    updated=doc.updated if doc else None, template="tool")
    meta.schema.append(schema.web_application(t["path"], t["name"], t["description"]))
    meta.schema.append(schema.web_page(t["path"], t["name"], t["description"], updated=meta.updated))
    cat = catalog.CAT_BY_TOOL[key]
    rel = linkgraph.related_for(t["path"], explicit=[t["guide"], t["calculator"], cat["path"]] +
                                [f"/glossary/{s}/" for s in t["glossary"]] + (doc.related or [] if doc else []),
                                cluster=linkgraph.TOOL_CLUSTER[key])
    body = linkgraph.autolink_glossary(_example_tokens(doc.html, example)) if doc else ""
    fields = [(k, V.F[k]) for k in V.TOOL_INPUTS[key]]
    base = V.BASE[key]
    return render_page("tool.html", meta, t=t, doc=doc, body=body, fields=fields, values=V.EXAMPLES[key],
                       monetization_options=V.F["monetization"]["options"],
                       example=example, related=rel, cat=cat, base=base, key=key,
                       guide_title=linkgraph.title_for(t["guide"]), calc_title=linkgraph.title_for(t["calculator"]))


def _example_tokens(html, r):
    """Replace [[ex:...]] tokens in tool copy with the live example calculation, so
    worked examples never drift from the engine."""
    from ..filters import money, mult, effect
    tokens = {
        "low": money(r["value"]["low"]), "mid": money(r["value"]["mid"]), "high": money(r["value"]["high"]),
        "metric": money(r["metric"]["value"]), "base_low": mult(r["base_multiple"]["low"]),
        "base_mid": mult(r["base_multiple"]["mid"]), "base_high": mult(r["base_multiple"]["high"]),
        "mlow": mult(r["multiple"]["low"]), "mmid": mult(r["multiple"]["mid"]), "mhigh": mult(r["multiple"]["high"]),
        "factor": f"{r['adjustment_factor']:.2f}", "confidence": r["confidence"],
    }
    if r.get("value_including_extras"):
        tokens["incl_low"] = money(r["value_including_extras"]["low"])
        tokens["incl_high"] = money(r["value_including_extras"]["high"])
    if r.get("cross_check"):
        tokens["implied"] = f"{r['cross_check']['value']}×"
    adj_rows = "".join(f"<tr><td>{a['factor']}</td><td>{a['value']}</td><td class=\"r num\">{effect(a['effect'])}</td></tr>"
                       for a in r["adjustments"])
    tokens["adjustments"] = ('<div class="table-wrap"><table><thead><tr><th>Factor</th><th>Example input</th>'
                             f'<th class="r">Effect</th></tr></thead><tbody>{adj_rows}</tbody></table></div>')

    def sub(m):
        return tokens.get(m.group(1), m.group(0))
    html = re.sub(r"<p>\[\[ex:adjustments\]\]</p>", lambda m: tokens["adjustments"], html)
    return re.sub(r"\[\[ex:([a-z_]+)\]\]", sub, html)


@bp.post("/tools/result/<key>/")
def tool_result(key):
    """Calculation endpoint. JSON for the enhanced form; a noindex HTML page otherwise."""
    if key not in V.TOOL_INPUTS:
        abort(404)
    wants_json = "application/json" in request.headers.get("Accept", "")
    if auth.rate_limited("calc", 60, 60):
        msg = "Too many calculations in a short time. Wait a minute and try again."
        return (jsonify(ok=False, error=msg), 429) if wants_json else (msg, 429)
    t = catalog.TOOLS_BY_KEY[key]
    try:
        x = V.parse_inputs(key, request.form)
        r = V.value_business(key, x)
    except V.ValuationError as e:
        fields = getattr(e, "fields", {})
        if wants_json:
            return jsonify(ok=False, error=str(e), fields=fields), 422
        return render_template("result_page.html", t=t, error=str(e), fields=fields, values=request.form,
                               field_specs=[(k, V.F[k]) for k in V.TOOL_INPUTS[key]]), 422
    session["last_valuation"] = {"tool": key, "inputs": x}
    analytics.server_event("valuation_generated", {"tool": key, "confidence": r["confidence"]})
    html = render_template("partials/result.html", r=r, t=t)
    if wants_json:
        return jsonify(ok=True, html=html, value=r["value"])
    return render_template("result_page.html", t=t, r=r, html=html)


@bp.get("/tools/result/<key>/")
def tool_result_get(key):
    t = catalog.TOOLS_BY_KEY.get(key)
    return redirect(t["path"] if t else "/tools/", 301)


# ---------------------------------------------------------------- calculators
@bp.get("/calculators/")
def calcs_hub():
    meta = PageMeta(path="/calculators/", title="Business Valuation Calculators",
                    meta_title="Business Valuation Calculators – Website, SaaS & Multiples",
                    description="Quick calculators for website worth, SaaS value from ARR, and the revenue and profit "
                                "multiples implied by any asking price.",
                    breadcrumbs=[("Calculators", "/calculators/")], template="hub")
    meta.schema.append(schema.collection_page("/calculators/", meta.title, meta.description,
                                              [(c["name"], c["path"]) for c in catalog.CALCULATORS]))
    doc = content.load("hubs", "calculators")
    return render_page("hub_calcs.html", meta, doc=doc, calcs=catalog.CALCULATORS, tools=catalog.TOOLS)


def _calc_compute(key, form):
    if key == "website_worth":
        return V.website_worth(form.get("monthly_profit"), form.get("months") or 36)
    if key == "saas_quick":
        return V.saas_quick(form.get("mrr"), form.get("growth_pct"), form.get("monthly_churn"))
    if key == "business_multiple":
        return V.business_multiple(form.get("asking_price"), form.get("annual_revenue"),
                                   form.get("annual_profit"), form.get("category") or None)
    raise V.ValuationError("Unknown calculator")


CALC_EXAMPLES = {
    "website_worth": {"monthly_profit": "4500", "months": "36"},
    "saas_quick": {"mrr": "20000", "growth_pct": "30", "monthly_churn": "3"},
    "business_multiple": {"asking_price": "300000", "annual_revenue": "120000", "annual_profit": "90000",
                          "category": "website"},
}


@bp.get("/calculators/<slug>/")
def calculator(slug):
    c = catalog.CALCS_BY_SLUG.get(slug)
    if not c:
        abort(404)
    doc = content.load("calculators", slug)
    example = _calc_compute(c["key"], CALC_EXAMPLES[c["key"]])
    meta = PageMeta(path=c["path"], title=c["name"], meta_title=c["meta_title"], description=c["description"],
                    breadcrumbs=[("Calculators", "/calculators/"), (c["name"], c["path"])],
                    updated=doc.updated if doc else None, template="calculator")
    meta.schema.append(schema.web_application(c["path"], c["name"], c["description"]))
    meta.schema.append(schema.web_page(c["path"], c["name"], c["description"], updated=meta.updated))
    rel = linkgraph.related_for(c["path"], explicit=[c["tool"]] + (doc.related or [] if doc else []),
                                cluster=c["cluster"])
    body = linkgraph.autolink_glossary(doc.html) if doc else ""
    return render_page("calculator.html", meta, c=c, doc=doc, body=body, example=example,
                       values=CALC_EXAMPLES[c["key"]], related=rel, type_label=V.TYPE_LABEL)


@bp.post("/calculators/result/<key>/")
def calculator_result(key):
    c = next((x for x in catalog.CALCULATORS if x["key"] == key), None)
    if not c:
        abort(404)
    wants_json = "application/json" in request.headers.get("Accept", "")
    try:
        r = _calc_compute(key, request.form)
    except V.ValuationError as e:
        if wants_json:
            return jsonify(ok=False, error=str(e)), 422
        return render_template("calc_result_page.html", c=c, error=str(e)), 422
    if key == "saas_quick":
        session["last_valuation"] = {"tool": "saas", "inputs": {k: r["inputs"].get(k) for k in r["inputs"]}}
    analytics.server_event("tool_completed", {"calculator": key})
    html = render_template("partials/calc_result.html", c=c, r=r, type_label=V.TYPE_LABEL)
    if wants_json:
        return jsonify(ok=True, html=html)
    return render_template("calc_result_page.html", c=c, html=html)


# ---------------------------------------------------------------- guides & glossary
@bp.get("/guides/")
def guides_index():
    docs = content.list_docs("guides")
    meta = PageMeta(path="/guides/", title="Digital Business Guides",
                    meta_title="Guides to Valuing, Buying and Selling Digital Businesses",
                    description="Plain-English guides to valuing websites, SaaS and AI businesses, and to buying, "
                                "selling and doing due diligence on online businesses.",
                    breadcrumbs=[("Guides", "/guides/")], template="hub")
    meta.schema.append(schema.collection_page("/guides/", meta.title, meta.description,
                                              [(d.title, f"/guides/{d.slug}/") for d in docs]))
    groups = {}
    for d in docs:
        groups.setdefault(d.section or "Valuation", []).append(d)
    return render_page("guides_index.html", meta, groups=groups)


@bp.get("/guides/<slug>/")
def guide(slug):
    doc = content.load("guides", slug)
    if not doc or doc.meta.get("status", "published") != "published":
        abort(404)
    path = f"/guides/{slug}/"
    meta = PageMeta(path=path, title=doc.title, meta_title=doc.meta_title, description=doc.meta_description,
                    h1=doc.h1 or doc.title, og_type="article", published=doc.published, updated=doc.updated,
                    breadcrumbs=[("Guides", "/guides/"), (doc.title, path)], template="guide")
    meta.schema.append(schema.article(path, doc.h1 or doc.title, doc.meta_description, doc.author,
                                      doc.published, doc.updated, doc.section))
    rel = linkgraph.related_for(path, explicit=doc.related, cluster=doc.cluster)
    body = linkgraph.autolink_glossary(doc.html)
    cta = _cta_for(doc)
    return render_page("guide.html", meta, doc=doc, body=body, related=rel, cta=cta)


def _cta_for(doc):
    if doc.cta:
        path = doc.cta
        title = linkgraph.title_for(path) or "the tool"
        return dict(path=path, title=title, text=doc.cta_text or f"Try the free {title}.")
    return None


@bp.get("/glossary/")
def glossary_index():
    docs = content.list_docs("glossary")
    terms = [dict(term=d.term or d.title, path=f"/glossary/{d.slug}/", definition=d.definition) for d in docs]
    terms.sort(key=lambda t: t["term"].lower())
    meta = PageMeta(path="/glossary/", title="Digital Business Glossary",
                    meta_title="Digital Business Glossary – ARR, SDE, Multiples & More",
                    description="Definitions of the terms used to value, buy and sell digital businesses, from ARR "
                                "and SDE to churn, LTV and customer concentration, with formulas and examples.",
                    breadcrumbs=[("Glossary", "/glossary/")], template="hub")
    meta.schema.append(schema.web_page("/glossary/", meta.title, meta.description, "CollectionPage"))
    meta.schema.append(schema.defined_term_set("/glossary/", terms))
    return render_page("glossary_index.html", meta, terms=terms)


@bp.get("/glossary/<slug>/")
def glossary_term(slug):
    doc = content.load("glossary", slug)
    if not doc:
        abort(404)
    path = f"/glossary/{slug}/"
    term = doc.term or doc.title
    meta = PageMeta(path=path, title=doc.title, meta_title=doc.meta_title, description=doc.meta_description,
                    h1=doc.h1 or doc.title, updated=doc.updated,
                    breadcrumbs=[("Glossary", "/glossary/"), (term, path)], template="glossary")
    meta.schema.append(schema.defined_term(path, term, doc.definition))
    meta.schema.append(schema.web_page(path, doc.title, doc.meta_description, updated=doc.updated))
    rel = linkgraph.related_for(path, explicit=doc.related, cluster=doc.cluster)
    body = linkgraph.autolink_glossary(doc.html, self_slug=slug)
    return render_page("glossary_term.html", meta, doc=doc, body=body, related=rel, term=term)


# ---------------------------------------------------------------- trust & company pages
LEGAL_PAGES = ("privacy", "terms", "refund-policy", "cookie-policy", "disclaimer")  # no automatic glossary links
PAGE_TYPES = {"about": "AboutPage", "contact": "ContactPage", "faq": "FAQPage"}


def _static_page(slug, template="page.html", **extra):
    doc = content.load("pages", slug)
    if not doc:
        abort(404)
    path = f"/{slug}/"
    meta = PageMeta(path=path, title=doc.title, meta_title=doc.meta_title, description=doc.meta_description,
                    h1=doc.h1 or doc.title, updated=doc.updated, breadcrumbs=[(doc.title, path)],
                    template="contact" if slug == "contact" else "page")
    ptype = PAGE_TYPES.get(slug, "WebPage")
    if ptype == "FAQPage":
        meta.schema.append(schema.web_page(path, doc.title, doc.meta_description, updated=doc.updated))
        meta.schema.append(schema.faq_page(path, doc.faqs()))
    else:
        meta.schema.append(schema.web_page(path, doc.title, doc.meta_description, ptype, updated=doc.updated))
    rel = linkgraph.related_for(path, explicit=doc.related)
    body = linkgraph.autolink_glossary(doc.html) if slug not in LEGAL_PAGES else doc.html
    return render_page(template, meta, doc=doc, body=body, related=rel, **extra)


for _slug in ("about", "data-sources", "editorial-policy", "verification", "marketplace-rules", "privacy", "terms",
              "refund-policy", "cookie-policy", "disclaimer", "buyer-safety", "how-it-works", "fees", "report-a-listing"):
    bp.add_url_rule(f"/{_slug}/", f"page_{_slug.replace('-', '_')}", (lambda s=_slug: _static_page(s)))


@bp.get("/faq/")
def faq():
    return _static_page("faq", "faq.html")


@bp.get("/methodology/")
def methodology():
    rows = []
    for key in ("website", "saas", "ai", "app", "newsletter", "ecommerce"):
        b = V.BASE[key]
        rows.append(dict(type=V.TYPE_LABEL[key], basis="Annual profit (SDE)" if b["method"] == "profit" else "ARR",
                         low=b["low"], mid=b["mid"], high=b["high"],
                         tool=catalog.TOOLS_BY_KEY[key]["path"]))
    return _static_page("methodology", "methodology.html", base_rows=rows, rules=V.rules_table(),
                        version=V.METHODOLOGY_VERSION,
                        version_date=V.METHODOLOGY_DATE, floor=V.ADJ_FLOOR, ceil=V.ADJ_CEIL)


@bp.get("/pricing/")
def pricing():
    return _static_page("pricing", "pricing.html")


@bp.route("/contact/", methods=["GET", "POST"])
def contact():
    sent = False
    if request.method == "POST":
        if auth.honeypot_tripped() or auth.rate_limited("contact", 5, 3600):
            abort(429)
        msg = (request.form.get("message") or "").strip()
        email = (request.form.get("email") or "").strip()
        if len(msg) < 10 or "@" not in email:
            flash("Add your email address and a message of at least a sentence.", "error")
        else:
            db.execute("INSERT INTO contact_messages(name, email, topic, message, created_at) VALUES (?,?,?,?,?)",
                       (request.form.get("name"), email, request.form.get("topic"), msg[:5000], db.now()))
            from .. import mailer
            mailer.admin_contact_message((request.form.get("name") or "")[:80], email[:200],
                                         (request.form.get("topic") or "")[:80], msg[:5000])
            sent = True
    html, status = _static_page("contact", "contact.html", sent=sent)
    return html, status


# ---------------------------------------------------------------- blog
@bp.get("/blog/")
def blog_index():
    posts = db.query("SELECT * FROM blog_posts WHERE status='published' ORDER BY published_at DESC")
    meta = PageMeta(path="/blog/", title="Blog", meta_title="VALUERAQ Blog – Digital Business Analysis",
                    description="Analysis and commentary on valuing, buying and selling digital businesses from the "
                                "VALUERAQ editorial team.", breadcrumbs=[("Blog", "/blog/")], template="hub")
    if not posts:
        # No thin, empty hub in the index (§73): noindex until the first post exists.
        meta.robots = "noindex, follow"
        meta.sitemap = False
        meta.noindex_reason = "no published posts"
    else:
        meta.schema.append(schema.collection_page("/blog/", meta.title, meta.description,
                                                  [(p["title"], f"/blog/{p['slug']}/") for p in posts]))
    return render_page("blog_index.html", meta, posts=posts)


@bp.get("/blog/<slug>/")
def blog_post(slug):
    p = db.query("SELECT * FROM blog_posts WHERE slug=?", (slug,), one=True)
    if not p or p["status"] != "published":
        abort(404)
    path = f"/blog/{slug}/"
    html, toc = content.render_md(p["body_md"])
    html = linkgraph.autolink_glossary(html)
    author = content.AUTHORS.get(p["author_key"], content.AUTHORS["editorial"])
    meta = PageMeta(path=path, title=p["title"], meta_title=p["meta_title"],
                    description=p["meta_description"] or p["summary"] or "", h1=p["h1"] or p["title"],
                    og_type="article", og_image=p["og_image"], published=iso(p["published_at"]),
                    updated=iso(p["updated_at"]), canonical=abs_url(p["canonical_url"]) if p["canonical_url"] else None,
                    breadcrumbs=[("Blog", "/blog/"), (p["title"], path)], template="blog")
    if p["robots_directive"]:
        meta.robots = p["robots_directive"]
    if not p["indexable"]:
        meta.robots = "noindex, follow"
    meta.schema.append(schema.article(path, meta.h1, meta.description, author, meta.published, meta.updated))
    rel = linkgraph.related_for(path, cluster=p["cluster"])
    return render_page("blog_post.html", meta, p=p, body=html, author=author, related=rel)


# ---------------------------------------------------------------- search (noindex)
@bp.get("/search/")
def search():
    q = (request.args.get("q") or "").strip()[:100]
    results = []
    if len(q) >= 2:
        terms = [t for t in re.findall(r"\w+", q.lower()) if len(t) > 1]
        for path, info in linkgraph.registry().items():
            doc = info.get("doc")
            hay = (info["title"] + " " + ((doc.meta_description or doc.definition or "") if doc else "")).lower()
            score = sum(3 if t in info["title"].lower() else 1 for t in terms if t in hay)
            if score:
                results.append((score, info["title"], path, (doc.meta_description or doc.definition) if doc else ""))
        like = f"%{q}%"
        for l in db.query("SELECT id, slug, category, title, headline FROM listings WHERE status='published' "
                          "AND is_test=0 AND (title LIKE ? OR headline LIKE ? OR description LIKE ?) LIMIT 20",
                          (like, like, like)):
            results.append((2, l["title"], f"/marketplace/{l['category']}/{l['slug']}-{l['id']}/", l["headline"] or ""))
        results.sort(key=lambda r: -r[0])
        analytics.server_event("marketplace_search", {"q": q, "n": len(results)})
    meta = PageMeta(path="/search/", title="Search", description="Search VALUERAQ tools, guides and listings.",
                    robots="noindex, follow", template="search")
    return render_page("search.html", meta, allow_params=("q",), q=q, results=results[:40])
