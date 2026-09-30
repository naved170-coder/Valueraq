"""Listing lifecycle, quality checks, duplicate detection and indexation rules (§20–25, §36, §69)."""
import hashlib
import re
import unicodedata

from flask import current_app

from . import catalog, db, redirects
from .seo import log_change

STATUSES = ("draft", "pending", "published", "rejected", "suspended", "sold", "removed")
PUBLIC_STATUSES = ("published", "sold")

SPAM_PHRASES = [
    "guaranteed income", "get rich", "passive income guaranteed", "100% guaranteed", "risk free",
    "whatsapp me", "telegram me", "crypto doubling", "click here", "buy now!!!", "limited time only",
    "casino", "viagra", "payday loan",
]
URL_RE = re.compile(r"(https?://|www\.)\S+", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{8,}\d")


def slugify(text, maxlen=60):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    text = text[:maxlen].rstrip("-")
    return text or "listing"


def listing_path(l):
    return f"/marketplace/{l['category']}/{l['slug']}-{l['id']}/"


def words(text):
    return re.findall(r"[a-zA-Z0-9']+", text or "")


def shingles(text, k=5):
    w = [x.lower() for x in words(text)]
    return {" ".join(w[i:i + k]) for i in range(max(0, len(w) - k + 1))}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def content_hash(text):
    norm = " ".join(x.lower() for x in words(text))
    return hashlib.sha256(norm.encode()).hexdigest()


def quality(l, others=None):
    """Return (score 0–100, flags list[(severity, message)])."""
    cfg = current_app.config
    flags = []
    desc = l["description"] or ""
    wc = len(words(desc))
    score = 100

    required = {"asking_price": "asking price", "monthly_revenue": "monthly revenue",
                "monthly_profit": "monthly profit", "age_years": "business age",
                "business_model": "business model"}
    for k, label in required.items():
        if l[k] in (None, ""):
            flags.append(("critical", f"Missing {label}."))
            score -= 12
    if wc < cfg["LISTING_MIN_WORDS"]:
        flags.append(("critical", f"Description has {wc} words; at least {cfg['LISTING_MIN_WORDS']} are needed to be indexed."))
        score -= 25
    if len((l["title"] or "")) < 12:
        flags.append(("warning", "Title is very short."))
        score -= 5
    if l["monthly_profit"] and l["monthly_revenue"] and l["monthly_profit"] > l["monthly_revenue"]:
        flags.append(("critical", "Monthly profit is higher than monthly revenue."))
        score -= 20
    if l["asking_price"] and l["monthly_profit"] and l["monthly_profit"] > 0:
        mult = l["asking_price"] / (l["monthly_profit"] * 12)
        if mult > 15:
            flags.append(("warning", f"Asking price is {mult:.1f}× annual profit; buyers will ask for justification."))
            score -= 5
    lower = desc.lower()
    hits = [p for p in SPAM_PHRASES if p in lower]
    if hits:
        flags.append(("critical", "Contains spam phrases: " + ", ".join(hits) + "."))
        score -= 30
    links = URL_RE.findall(desc)
    if len(links) > 2:
        flags.append(("critical", "More than two links in the description."))
        score -= 20
    if EMAIL_RE.search(desc) or PHONE_RE.search(desc):
        flags.append(("warning", "Contact details belong in inquiries, not the description; they will be hidden."))
        score -= 5
    letters = [c for c in desc if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.35:
        flags.append(("warning", "Too much text in capitals."))
        score -= 10
    w = [x.lower() for x in words(desc) if len(x) > 3]
    if len(w) > 40:
        top = max(set(w), key=w.count)
        density = w.count(top) / len(w)
        if density > 0.06:
            flags.append(("warning", f"The word '{top}' is repeated heavily ({density:.0%}); this reads as keyword stuffing."))
            score -= 10
        uniq = len(set(w)) / len(w)
        if uniq < 0.35:
            flags.append(("warning", "The description repeats itself a lot."))
            score -= 10
    # Near-duplicate detection against other live listings.
    if others is None:
        others = db.query("SELECT id, description FROM listings WHERE status IN ('published','pending') AND id != ?",
                          (l["id"] or 0,))
    mine = shingles(desc)
    for o in others:
        sim = jaccard(mine, shingles(o["description"]))
        if sim >= cfg["DUPLICATE_THRESHOLD"]:
            flags.append(("critical", f"Description is {sim:.0%} similar to listing #{o['id']}."))
            score -= 40
            break
    return max(0, min(100, score)), flags


def indexable(l, score=None, flags=None):
    cfg = current_app.config
    if l["status"] != "published" or l["is_test"]:
        return False
    if score is None:
        score = l["quality_score"] or 0
    if flags is None:
        flags = decode_flags(l["quality_flags"])
    if any(sev == "critical" for sev, _ in flags):
        return False
    return score >= cfg["LISTING_MIN_QUALITY"]


def encode_flags(flags):
    return "\n".join(f"{s}|{m}" for s, m in flags)


def decode_flags(s):
    out = []
    for line in (s or "").splitlines():
        if "|" in line:
            sev, msg = line.split("|", 1)
            out.append((sev, msg))
    return out


def refresh(listing_id):
    """Recompute quality + indexation flags after any change."""
    l = db.query("SELECT * FROM listings WHERE id=?", (listing_id,), one=True)
    if not l:
        return None
    score, flags = quality(l)
    idx = indexable(l, score, flags)
    db.execute("UPDATE listings SET quality_score=?, quality_flags=?, content_hash=?, indexable=?, sitemap_included=? "
               "WHERE id=?", (score, encode_flags(flags), content_hash(l["description"]), int(idx), int(idx), listing_id))
    return db.query("SELECT * FROM listings WHERE id=?", (listing_id,), one=True)


def set_status(listing_id, status, by="admin", note=None, replacement_id=None):
    assert status in STATUSES
    l = db.query("SELECT * FROM listings WHERE id=?", (listing_id,), one=True)
    if not l:
        return None
    path = listing_path(l)
    fields = {"status": status, "updated_at": db.now()}
    if note is not None:
        fields["moderation_note"] = note
    if status == "published" and not l["published_at"]:
        fields["published_at"] = db.now()
    if replacement_id:
        fields["replacement_listing_id"] = replacement_id
    sets = ", ".join(f"{k}=?" for k in fields)
    db.execute(f"UPDATE listings SET {sets} WHERE id=?", (*fields.values(), listing_id))
    log_change(path, "listing_status", l["status"], status, by, note)

    was_public = l["status"] in PUBLIC_STATUSES
    if status == "removed" and was_public:
        rep = db.query("SELECT * FROM listings WHERE id=? AND status='published'", (replacement_id,), one=True) \
            if replacement_id else None
        if rep:
            redirects.add_redirect(path, listing_path(rep), by, f"listing {listing_id} replaced by {rep['id']}")
        else:
            redirects.mark_gone(path, by, f"listing {listing_id} removed")
    if status == "suspended" and was_public:
        redirects.mark_gone(path, by, f"listing {listing_id} suspended")
    if status in PUBLIC_STATUSES:
        db.execute("DELETE FROM gone_urls WHERE path=?", (path,))
        from . import invalidate_redirect_cache
        invalidate_redirect_cache()
    return refresh(listing_id)


def change_slug(listing_id, new_title, by="seller"):
    l = db.query("SELECT * FROM listings WHERE id=?", (listing_id,), one=True)
    new_slug = slugify(new_title)
    if new_slug == l["slug"]:
        return
    old_path = listing_path(l)
    db.execute("UPDATE listings SET slug=? WHERE id=?", (new_slug, listing_id))
    l2 = db.query("SELECT * FROM listings WHERE id=?", (listing_id,), one=True)
    if l["status"] in PUBLIC_STATUSES or l["published_at"]:
        redirects.add_redirect(old_path, listing_path(l2), by, "listing title changed")


def public_text(desc):
    """Strip contact details and turn URLs into plain text (UGC safety)."""
    desc = EMAIL_RE.sub("[contact via inquiry]", desc)
    desc = PHONE_RE.sub("[contact via inquiry]", desc)
    return desc


def facts(l):
    cat = catalog.CATS_BY_SLUG.get(l["category"], {})
    cur = l["currency"] or "USD"
    from .filters import money, num
    return {
        "Business type": catalog.ucfirst(cat.get("singular", l["category"])) if cat else l["category"],
        "Business model": l["business_model"] or "—",
        "Industry": l["industry"] or "—",
        "Asking price": money(l["asking_price"], cur),
        "Monthly revenue": money(l["monthly_revenue"], cur),
        "Monthly profit": money(l["monthly_profit"], cur),
        "Business age": (num(l["age_years"], 1) + " years") if l["age_years"] else "—",
        "Monthly traffic": (num(l["monthly_traffic"]) + " visits") if l["monthly_traffic"] else "—",
        "Seller location": l["country"] or "—",
        "Verification": (l["verification"] or "unverified").replace("_", " ").capitalize(),
    }


def implied_multiples(l):
    out = {}
    if l["asking_price"] and l["monthly_profit"] and l["monthly_profit"] > 0:
        out["profit"] = round(l["asking_price"] / (l["monthly_profit"] * 12), 2)
        out["months"] = round(l["asking_price"] / l["monthly_profit"], 1)
    if l["asking_price"] and l["monthly_revenue"]:
        out["revenue"] = round(l["asking_price"] / (l["monthly_revenue"] * 12), 2)
    return out
