"""Markdown content loader (guides, glossary, tool/category/calculator copy, trust pages).

Front matter format (between --- lines), one `key: value` per line. Lists are
comma separated. Example:

    ---
    title: How to Value a Website
    meta_description: ...
    related: /tools/website-valuation/, /guides/saas-valuation/
    ---
"""
import calendar
import os
import re
import time
from functools import lru_cache

import markdown
from markupsafe import Markup

CONTENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content")
LIST_KEYS = {"related", "glossary", "aliases", "tags", "keywords"}
KIND_PREFIX = {"guides": "/guides/", "glossary": "/glossary/"}

AUTHORS = {
    # Do not add qualifications that are not true. Add real people here with
    # their real, verifiable experience (§42).
    "editorial": dict(key="editorial", type="Organization", name="VALUERAQ Editorial Team",
                      bio="The VALUERAQ editorial team writes and maintains the platform's guides, "
                          "methodology and glossary. Every guide is reviewed against the published "
                          "methodology before publication and when the methodology changes.",
                      url="/editorial-policy/"),
}


def parse_front_matter(text):
    meta = {}
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[3:end].strip("\n")
            body = text[end + 4:].lstrip("\n")
            for line in block.splitlines():
                if not line.strip() or line.strip().startswith("#") or ":" not in line:
                    continue
                k, v = line.split(":", 1)
                k, v = k.strip(), v.strip()
                if k in LIST_KEYS:
                    meta[k] = [s.strip() for s in v.split(",") if s.strip()]
                else:
                    meta[k] = v
    return meta, body


_md_exts = ["tables", "toc", "attr_list", "sane_lists", "def_list", "abbr"]


def render_md(body):
    body = body.replace("{{BRAND}}", os.environ.get("BRAND_NAME", "VALUERAQ"))
    md = markdown.Markdown(extensions=_md_exts, extension_configs={
        "toc": {"permalink": False, "toc_depth": "2-3"}})
    html = md.convert(body)
    html = _external_links(html)
    html = _wrap_tables(html)
    return html, md.toc_tokens


def _external_links(html):
    def repl(m):
        tag = m.group(0)
        href = m.group(1)
        if href.startswith("http") and "valueraq.com" not in href and "rel=" not in tag:
            tag = tag[:-1] + ' rel="noopener" target="_blank">'
        return tag
    return re.sub(r'<a href="([^"]+)"[^>]*>', repl, html)


def _wrap_tables(html):
    return html.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")


def word_count(html):
    text = re.sub(r"<[^>]+>", " ", html)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", text))


class Doc:
    def __init__(self, kind, slug, meta, body_md):
        self.kind = kind
        self.slug = slug
        self.meta = meta
        self.body_md = body_md
        self.html, self.toc = render_md(body_md)
        self.words = word_count(self.html)

    def __getattr__(self, item):
        if item in ("kind", "slug", "meta", "body_md", "html", "toc", "words"):
            raise AttributeError(item)
        return self.meta.get(item)

    @property
    def path(self):
        pre = KIND_PREFIX.get(self.kind)
        return f"{pre}{self.slug}/" if pre else f"/{self.slug}/"

    @property
    def publish_ts(self):
        """Unix time this page goes public (from `publish_at`), or None if it has no timer."""
        return parse_when(self.meta.get("publish_at"))

    @property
    def held(self):
        return str(self.meta.get("hold", "")).strip().lower() in ("yes", "true", "1")

    @property
    def author(self):
        return AUTHORS.get(self.meta.get("author", "editorial"), AUTHORS["editorial"])

    def faqs(self):
        """Extract Q&A pairs from a '## Frequently asked questions' section (### headings)."""
        m = re.search(r"^## Frequently asked questions\s*$(.*?)(?=^## |\Z)", self.body_md, re.M | re.S)
        if not m:
            return []
        pairs = re.findall(r"^### (.+?)\s*$\n(.*?)(?=^### |\Z)", m.group(1), re.M | re.S)
        out = []
        for q, a in pairs:
            a = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", a.strip())
            a = re.sub(r"[*_`]", "", a)
            out.append((q.strip(), " ".join(a.split())))
        return out


@lru_cache(maxsize=None)
def load(kind, slug):
    path = os.path.join(CONTENT_DIR, kind, slug + ".md")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        meta, body = parse_front_matter(fh.read())
    return Doc(kind, slug, meta, body)


@lru_cache(maxsize=None)
def all_docs(kind):
    """Every published-status document of a kind, including ones still waiting for their time or an approval."""
    d = os.path.join(CONTENT_DIR, kind)
    if not os.path.isdir(d):
        return []
    docs = [load(kind, f[:-3]) for f in sorted(os.listdir(d)) if f.endswith(".md")]
    docs = [x for x in docs if x and x.meta.get("status", "published") == "published"]
    docs.sort(key=lambda x: (int(x.meta.get("order", 100)), x.meta.get("title", "")))
    return docs


def list_docs(kind):
    """Documents the public can see right now."""
    return _live_docs(kind, epoch())


@lru_cache(maxsize=16)
def _live_docs(kind, _epoch):
    return [d for d in all_docs(kind) if is_live(d)]


# --------------------------------------------------------------------------
# Timed publishing and approvals.
#
#   publish_at: 2026-10-07T19:00Z   the page stays hidden (404, out of sitemaps,
#                                   menus and internal links) until this moment
#   hold: yes                       the page also needs a click on Admin > Approvals
#
# Files live in the repository; the approve / reject decision lives in the database.
# --------------------------------------------------------------------------
_now = time.time
_decisions_cache = {"at": 0.0, "data": {}}
DECISION_TTL = 20


def parse_when(value):
    """'2026-10-07T19:00Z' or '2026-10-07 19:00' (always UTC) -> unix time, or None."""
    m = re.match(r"^\s*(\d{4})-(\d\d)-(\d\d)(?:[T ](\d\d):(\d\d))?", str(value or ""))
    if not m:
        return None
    y, mo, d, h, mi = (int(x) if x else 0 for x in m.groups())
    try:
        return calendar.timegm((y, mo, d, h, mi, 0))
    except (ValueError, OverflowError):
        return None


def decisions(fresh=False):
    """{path: 'approved' | 'rejected'} from the database, cached briefly per worker."""
    c = _decisions_cache
    if fresh or _now() - c["at"] > DECISION_TTL:
        data = {}
        try:
            from . import db
            data = {r["path"]: r["decision"] for r in db.query("SELECT path, decision FROM content_approvals")}
        except Exception:
            data = dict(c["data"]) if not fresh else {}
        c["data"], c["at"] = data, _now()
    return c["data"]


def is_live(doc):
    if not doc or doc.meta.get("status", "published") != "published":
        return False
    ts = doc.publish_ts
    if doc.meta.get("publish_at") and ts is None:
        return False  # unreadable timer: stay hidden rather than publish by accident
    if ts is not None and ts > _now():
        return False
    if doc.held and decisions().get(doc.path) != "approved":
        return False
    return True


@lru_cache(maxsize=1)
def _timers():
    out = []
    for kind in KIND_PREFIX:
        out += [d.publish_ts for d in all_docs(kind) if d.publish_ts is not None]
    return sorted(out)


def epoch():
    """A value that changes whenever the set of public pages changes; used as a cache key."""
    now = _now()
    due = sum(1 for t in _timers() if t <= now)
    dec = decisions()
    return (due, len(dec), hash(frozenset(dec.items())))


def reset_caches():
    for f in (load, all_docs, _live_docs, _timers):
        f.cache_clear()
    _decisions_cache["at"] = 0.0


def md_inline(text):
    """Render a short user or admin string as safe inline markdown."""
    return Markup(markdown.markdown(text or "", extensions=["sane_lists"]))
