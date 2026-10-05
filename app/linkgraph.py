"""Page registry + internal linking engine (§30, §61, §62).

`registry()` lists every code/content-defined public page. Sitemaps, related
links, orphan detection and search all read from it.
"""
import re
from functools import lru_cache

from . import catalog, content

STATIC_PAGES = [
    # slug, sitemap group
    ("about", "pages"), ("methodology", "pages"), ("data-sources", "pages"), ("pricing", "pages"),
    ("faq", "pages"), ("contact", "pages"), ("editorial-policy", "pages"), ("verification", "pages"),
    ("marketplace-rules", "pages"), ("privacy", "pages"), ("terms", "pages"), ("refund-policy", "pages"),
    ("cookie-policy", "pages"), ("disclaimer", "pages"), ("buyer-safety", "pages"), ("how-it-works", "pages"),
    ("fees", "pages"), ("report-a-listing", "pages"),
]

TOOL_CLUSTER = {"website": "website", "saas": "saas", "ai": "ai", "app": "app",
                "newsletter": "newsletter", "ecommerce": "ecommerce"}
CAT_CLUSTER = {c["slug"]: TOOL_CLUSTER[c["tool"]] for c in catalog.CATEGORIES}


def registry():
    return _registry(content.epoch())


@lru_cache(maxsize=2)
def _registry(_epoch):
    pages = {}

    def add(path, title, kind, group, cluster=None, updated=None, doc=None):
        pages[path] = dict(path=path, title=title, kind=kind, group=group, cluster=cluster,
                           updated=updated, doc=doc)

    add("/", "Home", "home", "pages")
    add("/tools/", "Valuation Tools", "hub", "tools")
    add("/calculators/", "Business Calculators", "hub", "tools")
    add("/businesses-for-sale/", "Businesses for Sale", "hub", "categories")
    add("/marketplace/", "Marketplace", "hub", "categories")
    add("/guides/", "Guides", "hub", "guides")
    add("/glossary/", "Glossary", "hub", "guides")

    for t in catalog.TOOLS:
        d = content.load("tools", t["slug"])
        add(t["path"], t["name"], "tool", "tools", TOOL_CLUSTER[t["key"]], d.updated if d else None, d)
    for c in catalog.CALCULATORS:
        d = content.load("calculators", c["slug"])
        add(c["path"], c["name"], "calculator", "tools", c["cluster"], d.updated if d else None, d)
    for c in catalog.CATEGORIES:
        d = content.load("categories", c["slug"])
        add(c["path"], c["name"], "category", "categories", CAT_CLUSTER[c["slug"]], d.updated if d else None, d)
    for g in content.list_docs("guides"):
        add(f"/guides/{g.slug}/", g.title, "guide", "guides", g.cluster, g.updated, g)
    for g in content.list_docs("glossary"):
        add(f"/glossary/{g.slug}/", g.term or g.title, "glossary", "guides", g.cluster, g.updated, g)
    for slug, group in STATIC_PAGES:
        d = content.load("pages", slug)
        if d:
            add(f"/{slug}/", d.title, "page", group, None, d.updated, d)
    return pages


def title_for(path):
    p = registry().get(path)
    return p["title"] if p else None


def related_for(path, explicit=None, cluster=None, limit_per_group=4):
    """Return [(group_label, [(title, path)])] of contextual links.

    Explicit links from front matter come first; the cluster fills the rest.
    """
    reg = registry()
    groups = {"Tools": [], "Guides": [], "Marketplace": [], "Glossary": []}
    seen = {path}

    def put(p):
        if p in seen or p not in reg:
            return
        kind = reg[p]["kind"]
        label = {"tool": "Tools", "calculator": "Tools", "guide": "Guides", "category": "Marketplace",
                 "glossary": "Glossary", "page": "Guides", "hub": "Guides"}.get(kind)
        if not label or len(groups[label]) >= limit_per_group:
            return
        seen.add(p)
        groups[label].append((reg[p]["title"], p))

    for p in (explicit or []):
        put(p)
    if cluster:
        for p, info in reg.items():
            if info["cluster"] == cluster and info["kind"] in ("tool", "calculator", "category", "guide"):
                put(p)
    # Every page should reach the methodology page (trust hub).
    if len(groups["Guides"]) < limit_per_group:
        put("/methodology/")
    return [(k, v) for k, v in groups.items() if v]


# --------------------------------------------------------------------------
# Glossary auto-linking: first mention only, max 3 per page, never in headings
# or existing links.
# --------------------------------------------------------------------------
def _glossary_patterns():
    return _glossary_patterns_at(content.epoch())


@lru_cache(maxsize=2)
def _glossary_patterns_at(_epoch):
    pats = []
    for g in content.list_docs("glossary"):
        names = [g.term or g.title] + (g.aliases or [])
        for n in names:
            pats.append((re.compile(r"(?<![\w/-])(" + re.escape(n) + r")(?![\w-])"), g.slug))
    pats.sort(key=lambda x: -len(x[0].pattern))
    return pats


def autolink_glossary(html, self_slug=None, limit=3):
    used = set()
    count = 0
    # Split into protected (headings, links, code, tables headers) and free text.
    parts = re.split(r"(<h[1-6][^>]*>.*?</h[1-6]>|<a\b[^>]*>.*?</a>|<code>.*?</code>|<th\b[^>]*>.*?</th>|<[^>]+>)",
                     html, flags=re.S)
    for i, part in enumerate(parts):
        if count >= limit:
            break
        if not part or part.startswith("<"):
            continue
        for pat, slug in _glossary_patterns():
            if slug in used or slug == self_slug or count >= limit:
                continue
            m = pat.search(part)
            if m:
                link = f'<a href="/glossary/{slug}/" class="gloss">{m.group(1)}</a>'
                part = part[:m.start()] + link + part[m.end():]
                used.add(slug)
                count += 1
                # Re-split not needed: later patterns may match inside the new link text,
                # so stop processing this fragment after one insertion.
                break
        parts[i] = part
    return "".join(parts)


def suggest_links(text, limit=8):
    """Suggest related pages for a draft (blog CMS §62). Scored by term overlap."""
    words = set(re.findall(r"[a-z]{3,}", text.lower()))
    scored = []
    for path, info in registry().items():
        if info["kind"] in ("hub",) or path == "/":
            continue
        title_words = set(re.findall(r"[a-z]{3,}", info["title"].lower())) - {"for", "the", "and", "sale", "tool", "how"}
        if not title_words:
            continue
        overlap = len(words & title_words) / len(title_words)
        if overlap >= 0.5:
            scored.append((overlap, info["kind"], info["title"], path))
    scored.sort(reverse=True)
    return [dict(title=t, path=p, kind=k, score=round(s, 2)) for s, k, t, p in scored[:limit]]
