"""Central configuration. Everything brand-, domain- or policy-specific lives here.

Values can be overridden with environment variables so the same code runs in
development, staging and production.
"""
import os


def _bool(name, default=False):
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


class Config:
    # --- Brand & entity -------------------------------------------------
    BRAND = os.environ.get("BRAND_NAME", "VALUERAQ")
    SLOGAN = "All valuation features, at much lower fees than the leading marketplaces."
    BRAND_DESCRIPTION = (
        "VALUERAQ is a digital business intelligence platform and marketplace. "
        "It provides free valuation tools for websites, SaaS, AI businesses, apps, "
        "newsletters and ecommerce stores, and a marketplace where owners list "
        "digital businesses for sale."
    )
    # One preferred domain. Every other host 301-redirects here.
    SITE_URL = os.environ.get("SITE_URL", "https://www.valueraq.com").rstrip("/")
    # Hosts that are allowed to serve without redirect (dev/test).
    DEV_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "testserver"}
    ENFORCE_CANONICAL_HOST = _bool("ENFORCE_CANONICAL_HOST", True)
    # The host platform's health check reaches the instance on an internal host, so
    # this one path must answer 200 on any host and never 301 to the canonical one.
    HEALTH_CHECK_PATH = os.environ.get("HEALTH_CHECK_PATH", "/robots.txt")

    LANGUAGE = "en-US"
    LOCALE = "en_US"
    DEFAULT_CURRENCY = "USD"
    PRIMARY_MARKET = "US"

    # Legal owner and operator, shown in the Organization schema (the legal pages name it in their own text).
    LEGAL_NAME = os.environ.get("LEGAL_NAME", "Advent Business Consultax LLC")
    LEGAL_ADDRESS = {"streetAddress": "18W100 22nd St, Suite 124", "addressLocality": "Oakbrook Terrace",
                     "addressRegion": "IL", "postalCode": "60181", "addressCountry": "US"}
    CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "hello@valueraq.com")
    REFUND_EMAIL = os.environ.get("REFUND_EMAIL", "refund@valueraq.com")
    CONTACT_PHONE = os.environ.get("CONTACT_PHONE", "+12172909383")           # dialled form
    CONTACT_PHONE_DISPLAY = os.environ.get("CONTACT_PHONE_DISPLAY", "+1 217 290 9383")
    # Official accounts: shown in the footer and listed as sameAs in the Organization schema.
    SOCIAL_LINKS = [
        ("LinkedIn", "https://www.linkedin.com/company/145275373/"),
        ("X", "https://x.com/valueraq"),
        ("Facebook", "https://www.facebook.com/profile.php?id=61594665137424"),
    ]
    SOCIAL_PROFILES = [u.strip() for u in os.environ.get("SOCIAL_PROFILES", "").split(",") if u.strip()] \
        or [url for _, url in SOCIAL_LINKS]
    TWITTER_HANDLE = os.environ.get("TWITTER_HANDLE", "@valueraq")
    DEFAULT_OG_IMAGE = "/static/og/valueraq-default.png"

    # --- Search engine verification --------------------------------------
    # Google Analytics 4. Runs cookie-free until the visitor accepts the cookie notice. Set to "" to switch it off.
    GA_MEASUREMENT_ID = os.environ.get("GA_MEASUREMENT_ID", "G-TR4Q35LERR")
    GOOGLE_SITE_VERIFICATION = os.environ.get("GOOGLE_SITE_VERIFICATION", "")
    BING_SITE_VERIFICATION = os.environ.get("BING_SITE_VERIFICATION", "")

    # --- Crawler policy (§51) --------------------------------------------
    # "allow": no crawler is blocked beyond private areas (default).
    # A comma list in BLOCKED_CRAWLERS adds Disallow: / groups for named user agents.
    BLOCKED_CRAWLERS = [u.strip() for u in os.environ.get("BLOCKED_CRAWLERS", "").split(",") if u.strip()]
    PRIVATE_PATH_PREFIXES = [
        "/admin/", "/dashboard/", "/account/", "/settings/", "/checkout/",
        "/billing/", "/reports/private/", "/api/",
    ]
    NOINDEX_PATH_PREFIXES = PRIVATE_PATH_PREFIXES + [
        "/search/", "/login/", "/signup/", "/logout/", "/sell/", "/tools/result/",
        "/forgot-password/", "/reset-password/",
    ]

    # --- App --------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.getcwd(), "instance", "valueraq.db"))
    ADMIN_EMAILS = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", True)
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 30
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024
    ATTACH_MAX_BYTES = 5 * 1024 * 1024       # one file in a message thread
    ATTACH_PER_THREAD = 20
    ADMIN_2FA = _bool("ADMIN_2FA", True)      # emergency switch: ADMIN_2FA=0 turns two-step login off
    LOGIN_CODE_MINUTES = 10
    TESTING = False

    # --- Plans & billing (placeholders — set real prices before launch) ----
    TRIAL_DAYS = 14
    FREE_SAVED_REPORTS = 3
    PLANS = {
        "pro_monthly": {"name": "Pro", "price_usd": 29, "interval": "month",
                         "stripe_price_id": os.environ.get("STRIPE_PRICE_PRO_MONTHLY", "")},
        "pro_yearly": {"name": "Pro (annual)", "price_usd": 250, "interval": "year",
                        "stripe_price_id": os.environ.get("STRIPE_PRICE_PRO_YEARLY", "")},
    }
    # Featured listing: a subscription per listing, monthly or yearly.
    FEATURED_PLANS = {
        "featured_monthly": {"name": "Featured listing", "price_usd": 39, "interval": "month",
                              "stripe_price_id": os.environ.get("STRIPE_PRICE_FEATURED_MONTHLY", "")},
        "featured_yearly": {"name": "Featured listing (annual)", "price_usd": 350, "interval": "year",
                             "stripe_price_id": os.environ.get("STRIPE_PRICE_FEATURED_YEARLY", "")},
    }
    FEATURED_GRACE_DAYS = 3  # keep featured this long past period end while a renewal is confirmed
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    # --- Email through Resend (optional; the site works without it) --------
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "VALUERAQ <no-reply@valueraq.com>")
    PASSWORD_RESET_MINUTES = 60

    # --- Off-site database backups to Cloudflare R2 (optional) --------------
    R2_ENDPOINT = os.environ.get("R2_ENDPOINT", "")
    R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY", "")
    R2_BUCKET = os.environ.get("R2_BUCKET", "")
    # Sellers can ask for a verification badge; a reviewer (a person) checks the evidence.
    # Set VERIFICATION_REQUESTS=0 to hide the request form while nobody is available to review.
    VERIFICATION_REQUESTS_ENABLED = _bool("VERIFICATION_REQUESTS", True)
    BACKUP_EVERY_HOURS = 24
    BACKUP_KEEP = 30

    # --- SEO thresholds ----------------------------------------------------
    TITLE_MAX = 60
    DESCRIPTION_MIN = 70
    DESCRIPTION_MAX = 160
    THIN_WORDS = 250               # editorial pages under this word count are flagged
    LISTING_MIN_WORDS = 120        # listing descriptions below this are not indexable
    LISTING_MIN_QUALITY = 60
    LISTINGS_PER_PAGE = 24
    DUPLICATE_THRESHOLD = 0.8      # shingle Jaccard similarity
    INDEXABLE_COLLECTION_MIN_LISTINGS = 6
    METHODOLOGY_VERSION = "1.0"

    # --- Performance ---------------------------------------------------------
    PUBLIC_CACHE_SECONDS = 300
    CDN_CACHE_SECONDS = 300        # short, so edits and deploys show within minutes
    STATIC_VERSION = os.environ.get("STATIC_VERSION", "16")


class TestConfig(Config):
    TESTING = True
    GA_MEASUREMENT_ID = "G-TEST123"
    SECRET_KEY = "test"
    SESSION_COOKIE_SECURE = False
    ENFORCE_CANONICAL_HOST = False
    ADMIN_EMAILS = ["admin@example.com"]
