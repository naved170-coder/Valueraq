"""Marketplace: category landing pages, pagination, facets, listings, selling and inquiries."""
import math

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from .. import analytics, auth, catalog, content, db, linkgraph, mailer, marketplace as M, schema
from ..seo import PageMeta, abs_url, iso
from . import render_page

bp = Blueprint("marketplace", __name__)

FILTER_PARAMS = ("sort", "price_min", "price_max", "profit_min", "age_min", "model", "verified")


def _decorate(rows):
    out = []
    for r in rows:
        d = dict(r)
        d["path"] = M.listing_path(r)
        d["category_name"] = catalog.CATS_BY_SLUG.get(r["category"], {}).get("name", r["category"]).replace(" for Sale", "")
        out.append(d)
    return out


def _filtered_query(category=None):
    where = ["status='published'", "is_test=0"]
    args = []
    if category:
        where.append("category=?")
        args.append(category)
    a = request.args

    def num(k):
        try:
            return float(a.get(k)) if a.get(k) not in (None, "") else None
        except ValueError:
            return None
    if num("price_min") is not None:
        where.append("asking_price>=?"); args.append(num("price_min"))
    if num("price_max") is not None:
        where.append("asking_price<=?"); args.append(num("price_max"))
    if num("profit_min") is not None:
        where.append("monthly_profit>=?"); args.append(num("profit_min"))
    if num("age_min") is not None:
        where.append("age_years>=?"); args.append(num("age_min"))
    if a.get("model"):
        where.append("business_model=?"); args.append(a.get("model"))
    if a.get("verified") == "1":
        where.append("verification!='unverified'")
    sort = catalog.SORTS.get(a.get("sort") or "newest", catalog.SORTS["newest"])[1]
    return " AND ".join(where), args, f"is_featured DESC, {sort}, id DESC"


def _page(where, args, order, page):
    per = current_app.config["LISTINGS_PER_PAGE"]
    total = db.query(f"SELECT COUNT(*) n FROM listings WHERE {where}", args, one=True)["n"]
    pages = max(1, math.ceil(total / per))
    if page > pages:
        abort(404)  # no soft-404 / infinite crawl trap
    rows = db.query(f"SELECT * FROM listings WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?",
                    (*args, per, (page - 1) * per))
    return _decorate(rows), total, pages


# ---------------------------------------------------------------- hub
@bp.get("/businesses-for-sale/")
def hub():
    counts = {r["category"]: r["n"] for r in db.query(
        "SELECT category, COUNT(*) n FROM listings WHERE status='published' AND is_test=0 GROUP BY category")}
    recent = _decorate(db.query("SELECT * FROM listings WHERE status='published' AND is_test=0 "
                                "ORDER BY published_at DESC LIMIT 6"))
    # §8: recently sold. 'sold' is a public status (marketplace.PUBLIC_STATUSES), so these
    # pages already exist; this surfaces them. The section hides itself when empty, so it
    # costs nothing while the marketplace is still filling.
    sold = _decorate(db.query("SELECT * FROM listings WHERE status='sold' AND is_test=0 "
                              "ORDER BY updated_at DESC LIMIT 3"))
    doc = content.load("hubs", "businesses-for-sale")
    meta = PageMeta(path="/businesses-for-sale/", title="Digital Businesses for Sale",
                    meta_title="Digital Businesses for Sale – Websites, SaaS, Apps & More",
                    description="Browse websites, SaaS, AI businesses, apps, newsletters and ecommerce stores for sale. "
                                "Every listing shows asking price, revenue, profit and age.",
                    breadcrumbs=[("Businesses for sale", "/businesses-for-sale/")], template="hub")
    meta.schema.append(schema.collection_page(meta.path, meta.title, meta.description,
                                              [(c["name"], c["path"]) for c in catalog.CATEGORIES]))
    return render_page("bfs_hub.html", meta, cats=catalog.CATEGORIES, counts=counts, recent=recent,
                       sold=sold, doc=doc)


# ---------------------------------------------------------------- category pages
@bp.get("/businesses-for-sale/<cat>/")
def category(cat):
    return _category(cat, 1)


@bp.get("/businesses-for-sale/<cat>/page/<int:page>/")
def category_page(cat, page):
    if page == 1:
        return redirect(url_for("marketplace.category", cat=cat), 301)
    if page < 1:
        abort(404)
    return _category(cat, page)


def _category(cat, page):
    c = catalog.CATS_BY_SLUG.get(cat)
    if not c:
        abort(404)
    where, args, order = _filtered_query(cat)
    listings, total, pages = _page(where, args, order, page)
    base = c["path"]
    path = base if page == 1 else f"{base}page/{page}/"
    doc = content.load("categories", cat)
    title = c["name"] if page == 1 else f"{c['name']} – Page {page}"
    meta = PageMeta(path=path, title=title,
                    meta_title=c["meta_title"] if page == 1 else f"{c['name']} – Page {page} | VALUERAQ",
                    description=c["description"] if page == 1 else f"Page {page} of {c['name'].lower()} on VALUERAQ. "
                    f"{total} listings with asking price, revenue, profit and age.",
                    h1=c["name"], updated=doc.updated if doc else None,
                    breadcrumbs=[("Businesses for sale", "/businesses-for-sale/"), (c["name"], base)] +
                                ([(f"Page {page}", path)] if page > 1 else []),
                    template="category")
    meta.schema.append(schema.collection_page(path, title, meta.description,
                                              [(l["title"], l["path"]) for l in listings]))
    tool = catalog.TOOLS_BY_KEY[c["tool"]]
    rel = linkgraph.related_for(base, explicit=[tool["path"], tool["guide"], "/guides/buying-digital-businesses/",
                                                "/guides/digital-business-due-diligence/"] + (doc.related or [] if doc else []),
                                cluster=linkgraph.CAT_CLUSTER[cat])
    body = linkgraph.autolink_glossary(doc.html) if (doc and page == 1) else ""
    filtered = any(request.args.get(k) for k in FILTER_PARAMS)
    return render_page("category.html", meta, c=c, listings=listings, total=total, page=page, pages=pages,
                       base=base, doc=doc if page == 1 else None, body=body, related=rel, tool=tool,
                       models=catalog.BUSINESS_MODELS.get(cat, []), sorts=catalog.SORTS, filtered=filtered,
                       args=request.args)


# ---------------------------------------------------------------- all listings
@bp.get("/marketplace/")
def all_listings():
    return _all(1)


@bp.get("/marketplace/page/<int:page>/")
def all_listings_page(page):
    if page == 1:
        return redirect("/marketplace/", 301)
    return _all(page)


def _all(page):
    where, args, order = _filtered_query(None)
    listings, total, pages = _page(where, args, order, page)
    path = "/marketplace/" if page == 1 else f"/marketplace/page/{page}/"
    meta = PageMeta(path=path, title="Marketplace" if page == 1 else f"Marketplace – Page {page}",
                    meta_title="Marketplace – All Digital Businesses for Sale" if page == 1 else
                    f"Marketplace – Page {page} | VALUERAQ",
                    description="Every live listing on the VALUERAQ marketplace, newest first, across websites, SaaS, "
                                "AI businesses, apps, newsletters and ecommerce." if page == 1 else
                    f"Page {page} of all live listings on the VALUERAQ marketplace.",
                    h1="All businesses for sale",
                    breadcrumbs=[("Marketplace", "/marketplace/")] + ([(f"Page {page}", path)] if page > 1 else []),
                    template="category")
    if total == 0:
        # An empty "all listings" page adds nothing the category pages don't; keep it out of the index.
        meta.robots = "noindex, follow"
        meta.noindex_reason = "no live listings"
    meta.schema.append(schema.collection_page(path, meta.title, meta.description,
                                              [(l["title"], l["path"]) for l in listings]))
    return render_page("marketplace_all.html", meta, listings=listings, total=total, page=page, pages=pages,
                       base="/marketplace/", cats=catalog.CATEGORIES, sorts=catalog.SORTS, args=request.args)


# ---------------------------------------------------------------- listing detail
@bp.get("/marketplace/<cat>/<slug_id>/")
def listing(cat, slug_id):
    slug, _, lid = slug_id.rpartition("-")
    if not lid.isdigit():
        abort(404)
    l = db.query("SELECT * FROM listings WHERE id=?", (int(lid),), one=True)
    if not l:
        abort(404)
    canonical_path = M.listing_path(l)
    u = g.get("user")
    is_owner = u is not None and (u["id"] == l["seller_id"] or u["role"] == "admin")

    if l["status"] in ("removed", "suspended"):
        if l["replacement_listing_id"]:
            rep = db.query("SELECT * FROM listings WHERE id=? AND status='published'", (l["replacement_listing_id"],), one=True)
            if rep:
                return redirect(M.listing_path(rep), 301)
        abort(410)
    if l["status"] not in M.PUBLIC_STATUSES and not is_owner:
        abort(404)
    if request.path != canonical_path:
        return redirect(canonical_path, 301)

    c = catalog.CATS_BY_SLUG.get(l["category"])
    facts = M.facts(l)
    desc_public = M.public_text(l["description"])
    meta_desc = l["meta_description"] or _listing_description(l, c)
    meta = PageMeta(path=canonical_path, title=l["title"], meta_title=l["meta_title"] or f"{l['title']} – {catalog.ucfirst(c['singular'])} for Sale",
                    description=meta_desc, og_type="product", updated=iso(l["updated_at"]),
                    breadcrumbs=[("Businesses for sale", "/businesses-for-sale/"), (c["name"], c["path"]),
                                 (l["title"], canonical_path)], template="listing")
    if not (l["indexable"] and l["status"] == "published"):
        meta.robots = "noindex, follow"
        meta.noindex_reason = "sold" if l["status"] == "sold" else "below listing quality threshold or not published"
    meta.schema.append(schema.listing_product(l, canonical_path, {k: v for k, v in facts.items() if k != "Verification"}))
    if not is_owner and not request.headers.get("X-VQ-Audit"):
        db.execute("UPDATE listings SET view_count=view_count+1 WHERE id=?", (l["id"],))
        from .market_account import record_view
        record_view(l["id"])
        analytics.server_event("listing_viewed", {"listing": l["id"], "category": l["category"]})
    tool = catalog.TOOLS_BY_KEY[c["tool"]]
    rel = linkgraph.related_for(canonical_path, explicit=[c["path"], tool["path"], "/guides/digital-business-due-diligence/",
                                                          "/verification/"], cluster=linkgraph.CAT_CLUSTER[l["category"]])
    similar = _decorate(db.query("SELECT * FROM listings WHERE category=? AND status='published' AND is_test=0 AND id!=? "
                                 "ORDER BY published_at DESC LIMIT 3", (l["category"], l["id"])))
    return render_page("listing.html", meta, l=l, c=c, facts=facts, desc=desc_public, tool=tool, related=rel,
                       similar=similar, is_owner=is_owner, mult=M.implied_multiples(l),
                       saved=_is_saved(u, l["id"]))


def _is_saved(user, listing_id):
    from .market_account import is_saved
    return is_saved(user, listing_id)


def _listing_description(l, c):
    """Derived from actual listing data only (§12, §23)."""
    from ..filters import money
    parts = [f"{catalog.ucfirst(c['singular'])} for sale"]
    if l["business_model"]:
        parts[0] += f" ({l['business_model'].lower()})"
    bits = []
    if l["asking_price"]:
        bits.append(f"asking {money(l['asking_price'], l['currency'])}")
    if l["monthly_profit"]:
        bits.append(f"{money(l['monthly_profit'], l['currency'])}/mo profit")
    if l["age_years"]:
        bits.append(f"{l['age_years']:g} years old")
    s = parts[0] + (": " + ", ".join(bits) if bits else "") + ". "
    head = (l["headline"] or l["description"])[:160 - len(s)].rsplit(" ", 1)[0]
    return (s + head).strip()[:160]


@bp.post("/marketplace/<cat>/<slug_id>/inquire/")
@auth.login_required
def inquire(cat, slug_id):
    lid = slug_id.rpartition("-")[2]
    l = db.query("SELECT * FROM listings WHERE id=? AND status='published'", (int(lid) if lid.isdigit() else 0,), one=True)
    if not l:
        abort(404)
    if auth.honeypot_tripped() or auth.rate_limited("inquiry", 10, 3600):
        abort(429)
    msg = (request.form.get("message") or "").strip()
    if l["seller_id"] == g.user["id"]:
        flash("You can't send an inquiry about your own listing.", "error")
    elif len(msg) < 20:
        flash("Write at least a couple of sentences so the seller knows what you'd like to learn.", "error")
    else:
        db.execute("INSERT INTO inquiries(listing_id, buyer_id, message, created_at) VALUES (?,?,?,?)",
                   (l["id"], g.user["id"], msg[:4000], db.now()))
        analytics.server_event("listing_inquiry", {"listing": l["id"]})
        seller = db.query("SELECT email FROM users WHERE id=?", (l["seller_id"],), one=True)
        if seller:
            mailer.inquiry_to_seller(seller["email"], l["title"], g.user["email"], msg[:4000])
        flash("Inquiry sent. The seller will see it in their account.", "ok")
    return redirect(M.listing_path(l))


# ---------------------------------------------------------------- sell (create/edit)
LISTING_FIELDS = ["category", "title", "headline", "description", "business_model", "industry", "country",
                  "asking_price", "monthly_revenue", "monthly_profit", "age_years", "monthly_traffic",
                  "growth_note", "assets_included", "reason_for_sale", "website_url"]
NUMERIC = {"asking_price", "monthly_revenue", "monthly_profit", "monthly_traffic"}


def _read_listing_form():
    data, errors = {}, {}
    for f in LISTING_FIELDS:
        v = (request.form.get(f) or "").strip()
        if f in NUMERIC or f == "age_years":
            if v:
                try:
                    num = float(v.replace(",", "").replace("$", ""))
                    if num < 0 and f != "monthly_profit":
                        raise ValueError
                    data[f] = num if f == "age_years" else int(num)
                except ValueError:
                    errors[f] = "Enter a number."
            else:
                data[f] = None
        else:
            data[f] = v or None
    if data["category"] not in catalog.CATS_BY_SLUG:
        errors["category"] = "Choose a category."
    if not data["title"] or len(data["title"]) < 12:
        errors["title"] = "Use a descriptive title of at least 12 characters (no URLs)."
    elif M.URL_RE.search(data["title"]):
        errors["title"] = "Titles can't contain links."
    if not data["description"] or len(M.words(data["description"])) < 40:
        errors["description"] = "Describe the business in at least 40 words. Listings need 120+ words to appear in search engines."
    if data["website_url"] and not data["website_url"].startswith(("http://", "https://")):
        errors["website_url"] = "Start the URL with https://"
    for f in ("headline",):
        if data[f] and len(data[f]) > 160:
            errors[f] = "Keep this under 160 characters."
    return data, errors


@bp.route("/sell/", methods=["GET", "POST"])
def sell():
    meta = PageMeta(path="/sell/", title="Sell Your Digital Business",
                    description="List a website, SaaS, AI business, app, newsletter or ecommerce store for sale on VALUERAQ.",
                    robots="noindex, follow", template="form")
    if not g.get("user"):
        return render_page("sell_intro.html", meta)
    data, errors = {}, {}
    if request.method == "POST":
        if auth.honeypot_tripped() or auth.rate_limited("listing", 10, 86400):
            abort(429)
        data, errors = _read_listing_form()
        recent = db.query("SELECT COUNT(*) n FROM listings WHERE seller_id=? AND created_at>?",
                          (g.user["id"], db.now() - 86400), one=True)["n"]
        if recent >= 5:
            errors["title"] = "You've created five listings today. Contact us if you need to list more."
        if not errors:
            t = db.now()
            lid = db.execute(
                "INSERT INTO listings(seller_id, category, slug, title, headline, description, business_model, industry, "
                "country, asking_price, monthly_revenue, monthly_profit, age_years, monthly_traffic, growth_note, "
                "assets_included, reason_for_sale, website_url, status, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (g.user["id"], data["category"], M.slugify(data["title"]), data["title"], data["headline"],
                 data["description"], data["business_model"], data["industry"], data["country"], data["asking_price"],
                 data["monthly_revenue"], data["monthly_profit"], data["age_years"], data["monthly_traffic"],
                 data["growth_note"], data["assets_included"], data["reason_for_sale"], data["website_url"],
                 "pending", t, t))
            if not g.user["is_seller"]:
                db.execute("UPDATE users SET is_seller=1 WHERE id=?", (g.user["id"],))
                analytics.server_event("seller_registration")
            analytics.server_event("listing_created", {"listing": lid, "category": data["category"]})
            l = M.refresh(lid)
            mailer.admin_new_listing(data["title"], data["category"], g.user["email"])
            flash("Listing submitted for review. We check every listing before it goes live, usually within two "
                  "business days.", "ok")
            if l["quality_flags"]:
                flash("Fix the items flagged on your listing to help it pass review and appear in search engines.", "ok")
            return redirect(url_for("account.listings"))
    return render_page("sell.html", meta, data=data, errors=errors, cats=catalog.CATEGORIES,
                       models=catalog.BUSINESS_MODELS, editing=None)
