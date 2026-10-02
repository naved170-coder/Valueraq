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

    CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "hello@valueraq.com")
    SOCIAL_PROFILES = [u for u in os.environ.get("SOCIAL_PROFILES", "").split(",") if u]
    TWITTER_HANDLE = os.environ.get("TWITTER_HANDLE", "")  # e.g. "@valueraq"
    DEFAULT_OG_IMAGE = "/static/og/valueraq-default.png"

    # --- Search engine verification --------------------------------------
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
    ]

    # --- App --------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.getcwd(), "instance", "valueraq.db"))
    ADMIN_EMAILS = [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", True)
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 30
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    TESTING = False

    # --- Plans & billing (placeholders — set real prices before launch) ----
    TRIAL_DAYS = 14
    FREE_SAVED_REPORTS = 3
    PLANS = {
        "pro_monthly": {"name": "Pro", "price_usd": 29, "interval": "month",
                         "stripe_price_id": os.environ.get("STRIPE_PRICE_PRO_MONTHLY", "")},
        "pro_yearly": {"name": "Pro (annual)", "price_usd": 290, "interval": "year",
                        "stripe_price_id": os.environ.get("STRIPE_PRICE_PRO_YEARLY", "")},
    }
    # Featured listing: a subscription per listing, monthly or yearly.
    FEATURED_PLANS = {
        "featured_monthly": {"name": "Featured listing", "price_usd": 39, "interval": "month",
                              "stripe_price_id": os.environ.get("STRIPE_PRICE_FEATURED_MONTHLY", "")},
        "featured_yearly": {"name": "Featured listing (annual)", "price_usd": 390, "interval": "year",
                             "stripe_price_id": os.environ.get("STRIPE_PRICE_FEATURED_YEARLY", "")},
    }
    FEATURED_GRACE_DAYS = 3  # keep featured this long past period end while a renewal is confirmed
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    # --- Optional AI commentary (premium) ----------------------------------
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

    # --- Email (optional; in-app notifications work without it) ----------
    SMTP_URL = os.environ.get("SMTP_URL", "")  # smtp://user:pass@host:587

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
    CDN_CACHE_SECONDS = 3600
    STATIC_VERSION = os.environ.get("STATIC_VERSION", "5")


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test"
    SESSION_COOKIE_SECURE = False
    ENFORCE_CANONICAL_HOST = False
    ADMIN_EMAILS = ["admin@example.com"]
