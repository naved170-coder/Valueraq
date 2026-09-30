"""JSON-LD builders (§14) and a validator used by tests and the admin audit.

Schema is only emitted for content that is visible on the page. No Review or
AggregateRating types are produced anywhere.
"""
from flask import current_app

from .seo import abs_url


def org_id():
    return current_app.config["SITE_URL"] + "/#organization"


def site_id():
    return current_app.config["SITE_URL"] + "/#website"


def organization():
    cfg = current_app.config
    node = {
        "@type": "Organization",
        "@id": org_id(),
        "name": cfg["BRAND"],
        "url": cfg["SITE_URL"] + "/",
        "logo": abs_url("/static/brand/valueraq-logo.png"),
        "description": cfg["BRAND_DESCRIPTION"],
        "email": cfg["CONTACT_EMAIL"],
    }
    if cfg["SOCIAL_PROFILES"]:
        node["sameAs"] = cfg["SOCIAL_PROFILES"]
    return node


def website():
    cfg = current_app.config
    return {
        "@type": "WebSite",
        "@id": site_id(),
        "url": cfg["SITE_URL"] + "/",
        "name": cfg["BRAND"],
        "inLanguage": cfg["LANGUAGE"],
        "publisher": {"@id": org_id()},
    }


def breadcrumb_list(crumbs):
    """crumbs: [(name, path)] including Home first."""
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": abs_url(path)}
            for i, (name, path) in enumerate(crumbs)
        ],
    }


def web_page(path, name, description, page_type="WebPage", updated=None):
    node = {
        "@type": page_type,
        "@id": abs_url(path) + "#webpage",
        "url": abs_url(path),
        "name": name,
        "description": description,
        "isPartOf": {"@id": site_id()},
        "inLanguage": current_app.config["LANGUAGE"],
    }
    if updated:
        node["dateModified"] = updated
    return node


def web_application(path, name, description, category="BusinessApplication"):
    return {
        "@type": "WebApplication",
        "@id": abs_url(path) + "#app",
        "name": name,
        "url": abs_url(path),
        "description": description,
        "applicationCategory": category,
        "operatingSystem": "Any (web browser)",
        "isAccessibleForFree": True,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "provider": {"@id": org_id()},
    }


def article(path, headline, description, author, published, updated, section=None):
    node = {
        "@type": "Article",
        "@id": abs_url(path) + "#article",
        "headline": headline[:110],
        "description": description,
        "url": abs_url(path),
        "mainEntityOfPage": abs_url(path),
        "datePublished": published,
        "dateModified": updated or published,
        "author": author_node(author),
        "publisher": {"@id": org_id()},
        "inLanguage": current_app.config["LANGUAGE"],
    }
    if section:
        node["articleSection"] = section
    return node


def author_node(author):
    if author.get("type") == "Person":
        node = {"@type": "Person", "name": author["name"]}
        if author.get("url"):
            node["url"] = abs_url(author["url"])
        if author.get("job_title"):
            node["jobTitle"] = author["job_title"]
        return node
    return {"@type": "Organization", "name": author["name"], "url": abs_url(author.get("url") or "/about/")}


def defined_term(path, term, definition, set_path="/glossary/"):
    return {
        "@type": "DefinedTerm",
        "@id": abs_url(path) + "#term",
        "name": term,
        "description": definition,
        "url": abs_url(path),
        "inDefinedTermSet": {
            "@type": "DefinedTermSet",
            "@id": abs_url(set_path) + "#set",
            "name": current_app.config["BRAND"] + " Glossary",
            "url": abs_url(set_path),
        },
    }


def defined_term_set(path, terms):
    return {
        "@type": "DefinedTermSet",
        "@id": abs_url(path) + "#set",
        "name": current_app.config["BRAND"] + " Glossary",
        "url": abs_url(path),
        "hasDefinedTerm": [
            {"@type": "DefinedTerm", "name": t["term"], "description": t["definition"], "url": abs_url(t["path"])}
            for t in terms
        ],
    }


def item_list(items):
    """items: [(name, path)] in visible order."""
    return {
        "@type": "ItemList",
        "numberOfItems": len(items),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "url": abs_url(p)}
            for i, (n, p) in enumerate(items)
        ],
    }


def collection_page(path, name, description, items):
    node = web_page(path, name, description, "CollectionPage")
    if items:
        node["mainEntity"] = item_list(items)
    return node


def faq_page(path, faqs):
    return {
        "@type": "FAQPage",
        "@id": abs_url(path) + "#faq",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faqs
        ],
    }


def listing_product(listing, path, facts):
    """Product + Offer built only from fields shown on the listing page."""
    node = {
        "@type": "Product",
        "@id": abs_url(path) + "#listing",
        "name": listing["title"],
        "description": (listing["headline"] or listing["description"][:300]),
        "url": abs_url(path),
        "category": facts.get("Business type"),
        "additionalProperty": [
            {"@type": "PropertyValue", "name": k, "value": v}
            for k, v in facts.items() if v not in (None, "", "—")
        ],
    }
    if listing["asking_price"]:
        node["offers"] = {
            "@type": "Offer",
            "price": str(listing["asking_price"]),
            "priceCurrency": listing["currency"] or "USD",
            "availability": "https://schema.org/InStock" if listing["status"] == "published"
            else "https://schema.org/SoldOut",
            "url": abs_url(path),
        }
    return node


def graph(nodes):
    return {"@context": "https://schema.org", "@graph": [n for n in nodes if n]}


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
REQUIRED = {
    "Organization": ["name", "url"],
    "WebSite": ["name", "url"],
    "WebPage": ["name", "url"],
    "AboutPage": ["name", "url"],
    "ContactPage": ["name", "url"],
    "CollectionPage": ["name", "url"],
    "BreadcrumbList": ["itemListElement"],
    "WebApplication": ["name", "url", "applicationCategory", "offers"],
    "Article": ["headline", "datePublished", "author", "publisher"],
    "DefinedTerm": ["name", "description"],
    "DefinedTermSet": ["name"],
    "FAQPage": ["mainEntity"],
    "ItemList": ["itemListElement"],
    "Product": ["name"],
    "Offer": ["price", "priceCurrency"],
}
FORBIDDEN = {"Review", "AggregateRating"}


def _walk(node, found):
    if isinstance(node, dict):
        t = node.get("@type")
        if t:
            found.append(node)
        for v in node.values():
            _walk(v, found)
    elif isinstance(node, list):
        for v in node:
            _walk(v, found)


def validate(doc):
    """Return (types, errors) for a parsed JSON-LD document."""
    errors, nodes = [], []
    if not isinstance(doc, dict) or doc.get("@context") != "https://schema.org":
        errors.append("missing @context https://schema.org")
    _walk(doc, nodes)
    types = []
    for n in nodes:
        t = n["@type"]
        types.append(t)
        if t in FORBIDDEN:
            errors.append(f"{t} is not allowed (no genuine review system)")
        for prop in REQUIRED.get(t, []):
            if prop not in n or n[prop] in (None, "", []):
                # nested references like {"@id": ...} are acceptable for publisher
                errors.append(f"{t} missing required property '{prop}'")
        if t == "BreadcrumbList":
            for i, item in enumerate(n.get("itemListElement", [])):
                if item.get("position") != i + 1 or not item.get("item"):
                    errors.append("BreadcrumbList item malformed")
        if t == "Product" and "aggregateRating" in n:
            errors.append("Product must not carry aggregateRating")
    return types, errors
