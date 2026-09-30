"""Page metadata system (§10–13, §34, §70).

Every public view builds a PageMeta. `finalize()` applies path rules,
query-parameter rules and admin overrides, so the template, the sitemap and the
audit all read the same decision.
"""
from dataclasses import dataclass, field
from typing import Optional
import json

from flask import current_app, request

from . import db


@dataclass
class PageMeta:
    path: str
    title: str                         # human title (used for H1 fallback and og)
    description: str
    h1: Optional[str] = None
    meta_title: Optional[str] = None   # explicit <title>; otherwise built from title
    canonical: Optional[str] = None    # absolute URL; default self
    robots: str = "index, follow"
    og_type: str = "website"
    og_image: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    schema: list = field(default_factory=list)
    breadcrumbs: list = field(default_factory=list)  # [(name, path)], home excluded
    published: Optional[str] = None    # ISO date
    updated: Optional[str] = None      # ISO date
    template: str = "page"             # template family for analytics / vitals
    sitemap: bool = True
    noindex_reason: Optional[str] = None

    @property
    def indexable(self):
        return "noindex" not in self.robots


def abs_url(path):
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return current_app.config["SITE_URL"] + path


def build_title(meta: PageMeta):
    if meta.meta_title:
        return meta.meta_title
    brand = current_app.config["BRAND"]
    candidate = f"{meta.title} | {brand}"
    if len(candidate) <= current_app.config["TITLE_MAX"] + 10:
        return candidate
    return meta.title


def path_is_private(path):
    return any(path.startswith(p) for p in current_app.config["PRIVATE_PATH_PREFIXES"])


def path_is_noindex(path):
    return any(path.startswith(p) for p in current_app.config["NOINDEX_PATH_PREFIXES"])


def get_override(path):
    try:
        return db.query("SELECT * FROM seo_overrides WHERE path = ?", (path,), one=True)
    except Exception:
        return None


def finalize(meta: PageMeta, allow_params=()):
    """Resolve canonical + robots + overrides. Call once per rendered page."""
    # 1. Canonical defaults to the clean self URL (no query string).
    if not meta.canonical:
        meta.canonical = abs_url(meta.path)

    # 2. Path rules (private and utility areas never index).
    if path_is_noindex(meta.path):
        meta.robots = "noindex, nofollow" if path_is_private(meta.path) else "noindex, follow"
        meta.sitemap = False
        meta.noindex_reason = meta.noindex_reason or "utility or private path"

    # 3. Any unexpected query parameter (filters, sort, tracking) → noindex, follow;
    #    canonical stays on the clean URL (§21, §34, §36).
    params = [k for k in request.args.keys() if k not in allow_params]
    if params:
        meta.robots = "noindex, follow"
        meta.sitemap = False
        meta.noindex_reason = meta.noindex_reason or "parameterised URL"

    # 4. Admin overrides (§11, §70).
    ov = get_override(meta.path)
    if ov is not None:
        for attr in ("meta_title", "h1", "og_title", "og_description", "og_image"):
            if ov[attr]:
                setattr(meta, attr, ov[attr])
        if ov["meta_description"]:
            meta.description = ov["meta_description"]
        if ov["canonical_url"]:
            meta.canonical = abs_url(ov["canonical_url"])
        if ov["robots_directive"] and not params:
            meta.robots = ov["robots_directive"]
        if ov["indexable"] is not None and not params:
            if not ov["indexable"]:
                meta.robots = "noindex, follow"
                meta.noindex_reason = "admin override"
        if ov["sitemap_included"] is not None:
            meta.sitemap = bool(ov["sitemap_included"])
        if ov["schema_extra"]:
            try:
                meta.schema.append(json.loads(ov["schema_extra"]))
            except ValueError:
                pass

    if not meta.indexable:
        meta.sitemap = False
    # A canonical that points elsewhere means this URL is not the sitemap URL.
    if meta.canonical != abs_url(meta.path):
        meta.sitemap = False
    if not meta.h1:
        meta.h1 = meta.title
    return meta


def override_sitemap_state(path, default=True):
    """Used by sitemap builders so admin overrides affect inclusion."""
    ov = get_override(path)
    if ov is None:
        return default
    if ov["indexable"] is not None and not ov["indexable"]:
        return False
    if ov["robots_directive"] and "noindex" in ov["robots_directive"]:
        return False
    if ov["canonical_url"] and abs_url(ov["canonical_url"]) != abs_url(path):
        return False
    if ov["sitemap_included"] is not None:
        return bool(ov["sitemap_included"])
    return default


def log_change(path, field_name, old, new, by, reason=None):
    if (old or "") == (new or ""):
        return
    db.execute(
        "INSERT INTO seo_change_log(path, field, old_value, new_value, changed_by, reason, changed_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (path, field_name, old, new, by, reason, db.now()),
    )


def iso(ts_or_date):
    """Accept epoch seconds or a YYYY-MM-DD string; return YYYY-MM-DD."""
    if ts_or_date is None:
        return None
    if isinstance(ts_or_date, (int, float)):
        import datetime
        return datetime.datetime.fromtimestamp(ts_or_date, datetime.timezone.utc).strftime("%Y-%m-%d")
    return str(ts_or_date)[:10]
