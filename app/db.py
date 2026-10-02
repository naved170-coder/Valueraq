"""SQLite storage. All SQL lives here or in the domain modules; swap for Postgres later."""
import os
import sqlite3
import time
from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT,
    role TEXT NOT NULL DEFAULT 'user',            -- user | admin
    plan TEXT NOT NULL DEFAULT 'free',            -- free | trial | pro
    trial_started_at INTEGER,
    trial_ends_at INTEGER,
    trial_used INTEGER NOT NULL DEFAULT 0,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    subscription_status TEXT,
    current_period_end INTEGER,
    is_seller INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    last_login_at INTEGER,
    session_version INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    tool TEXT NOT NULL,
    title TEXT,
    inputs_json TEXT NOT NULL,
    result_json TEXT NOT NULL,
    ai_commentary TEXT,
    methodology_version TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reports_user ON reports(user_id, created_at);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL REFERENCES users(id),
    category TEXT NOT NULL,
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    headline TEXT,
    description TEXT NOT NULL,
    business_model TEXT,
    industry TEXT,
    country TEXT,
    asking_price INTEGER,
    currency TEXT NOT NULL DEFAULT 'USD',
    monthly_revenue INTEGER,
    monthly_profit INTEGER,
    age_years REAL,
    monthly_traffic INTEGER,
    growth_note TEXT,
    assets_included TEXT,
    reason_for_sale TEXT,
    website_url TEXT,
    verification TEXT NOT NULL DEFAULT 'unverified',  -- unverified | revenue_verified | traffic_verified | fully_verified
    status TEXT NOT NULL DEFAULT 'draft',  -- draft|pending|published|rejected|suspended|sold|removed
    is_test INTEGER NOT NULL DEFAULT 0,
    is_featured INTEGER NOT NULL DEFAULT 0,
    featured_until INTEGER,
    featured_subscription_id TEXT,
    verification_requested_at INTEGER,
    verification_request_type TEXT,
    verification_request_note TEXT,
    replacement_listing_id INTEGER,
    moderation_note TEXT,
    quality_score INTEGER,
    quality_flags TEXT,
    content_hash TEXT,
    meta_title TEXT,
    meta_description TEXT,
    indexable INTEGER NOT NULL DEFAULT 0,
    sitemap_included INTEGER NOT NULL DEFAULT 0,
    view_count INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    published_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_listings_cat_status ON listings(category, status, is_featured, published_at);
CREATE INDEX IF NOT EXISTS idx_listings_seller ON listings(seller_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_listings_slug ON listings(category, slug, id);

CREATE TABLE IF NOT EXISTS inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL REFERENCES listings(id),
    buyer_id INTEGER NOT NULL REFERENCES users(id),
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_inquiries_listing ON inquiries(listing_id);

CREATE TABLE IF NOT EXISTS blog_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    h1 TEXT,
    summary TEXT,
    body_md TEXT NOT NULL,
    author_key TEXT NOT NULL DEFAULT 'editorial',
    cluster TEXT,
    primary_intent TEXT,
    meta_title TEXT,
    meta_description TEXT,
    canonical_url TEXT,
    robots_directive TEXT,
    og_image TEXT,
    status TEXT NOT NULL DEFAULT 'draft',        -- draft | published | archived
    ai_assisted INTEGER NOT NULL DEFAULT 0,
    reviewed_by TEXT,
    reviewed_at INTEGER,
    indexable INTEGER NOT NULL DEFAULT 1,
    sitemap_included INTEGER NOT NULL DEFAULT 1,
    published_at INTEGER,
    updated_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS seo_overrides (
    path TEXT PRIMARY KEY,
    meta_title TEXT,
    meta_description TEXT,
    h1 TEXT,
    canonical_url TEXT,
    robots_directive TEXT,
    og_title TEXT,
    og_description TEXT,
    og_image TEXT,
    schema_extra TEXT,
    indexable INTEGER,
    sitemap_included INTEGER,
    updated_at INTEGER NOT NULL,
    updated_by TEXT
);

CREATE TABLE IF NOT EXISTS seo_change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT,
    reason TEXT,
    changed_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_seo_log_path ON seo_change_log(path, changed_at);

CREATE TABLE IF NOT EXISTS redirects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_path TEXT NOT NULL UNIQUE,
    to_path TEXT NOT NULL,
    status INTEGER NOT NULL DEFAULT 301,
    reason TEXT,
    hits INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS gone_urls (
    path TEXT PRIMARY KEY,
    reason TEXT,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    intent TEXT,
    target_path TEXT,
    search_volume INTEGER,
    difficulty REAL,
    cpc REAL,
    source TEXT NOT NULL,
    source_date TEXT,
    imported_at INTEGER NOT NULL,
    UNIQUE(keyword, source)
);

CREATE TABLE IF NOT EXISTS search_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    engine TEXT NOT NULL,          -- google | bing
    path TEXT,
    query TEXT,
    clicks INTEGER,
    impressions INTEGER,
    ctr REAL,
    position REAL,
    period_start TEXT,
    period_end TEXT,
    imported_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT,
    session_id TEXT,
    user_id INTEGER,
    channel TEXT,                  -- organic | direct | referral | paid | social | email | ai
    landing_path TEXT,
    props TEXT,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_name ON events(name, created_at);

CREATE TABLE IF NOT EXISTS vitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template TEXT,
    path TEXT,
    metric TEXT NOT NULL,          -- LCP | CLS | INP | TTFB
    value REAL NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, email TEXT, topic TEXT, message TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (            -- replies inside an inquiry thread (the inquiry itself is message one)
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inquiry_id INTEGER NOT NULL REFERENCES inquiries(id),
    sender_id INTEGER NOT NULL REFERENCES users(id),
    body TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    read_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_messages_inquiry ON messages(inquiry_id, created_at);

CREATE TABLE IF NOT EXISTS watchlist (
    user_id INTEGER NOT NULL REFERENCES users(id),
    listing_id INTEGER NOT NULL REFERENCES listings(id),
    created_at INTEGER NOT NULL,
    last_price INTEGER,                      -- asking price the buyer last saw or was told about
    PRIMARY KEY (user_id, listing_id)
);
CREATE INDEX IF NOT EXISTS idx_watchlist_listing ON watchlist(listing_id);

CREATE TABLE IF NOT EXISTS listing_views (       -- one row per listing per UTC day, for seller analytics
    listing_id INTEGER NOT NULL REFERENCES listings(id),
    day TEXT NOT NULL,                       -- YYYY-MM-DD
    views INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (listing_id, day)
);

CREATE TABLE IF NOT EXISTS saved_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    category TEXT,                           -- NULL = every category
    price_max INTEGER,
    profit_min INTEGER,
    age_min REAL,
    model TEXT,
    verified INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_saved_searches_user ON saved_searches(user_id);

CREATE TABLE IF NOT EXISTS activity_log (        -- who did what: sign-ins, password changes, admin actions
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at INTEGER NOT NULL,
    user_id INTEGER,
    user_email TEXT,
    ip TEXT,
    action TEXT NOT NULL,
    target TEXT,
    detail TEXT
);
CREATE INDEX IF NOT EXISTS idx_activity_at ON activity_log(at);

CREATE TABLE IF NOT EXISTS error_log (           -- one row per distinct server error, with a counter
    fingerprint TEXT PRIMARY KEY,
    first_at INTEGER NOT NULL,
    last_at INTEGER NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    method TEXT,
    path TEXT,
    error_type TEXT,
    message TEXT,
    traceback TEXT,
    notified_at INTEGER
);

CREATE TABLE IF NOT EXISTS password_resets (
    token_hash TEXT PRIMARY KEY,           -- SHA-256 of the emailed token; the token itself is never stored
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    used_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_password_resets_user ON password_resets(user_id, created_at);

CREATE TABLE IF NOT EXISTS backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_key TEXT NOT NULL,
    kind TEXT NOT NULL,                     -- scheduled | manual
    status TEXT NOT NULL,                   -- ok | failed | pruned
    bytes INTEGER NOT NULL DEFAULT 0,
    db_bytes INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_at INTEGER NOT NULL,
    finished_at INTEGER
);
CREATE INDEX IF NOT EXISTS idx_backups_created ON backups(created_at);
CREATE TABLE IF NOT EXISTS backup_claims (slot TEXT PRIMARY KEY, claimed_at INTEGER NOT NULL);

CREATE TABLE IF NOT EXISTS seo_audit_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at INTEGER NOT NULL,
    finished_at INTEGER,
    pages INTEGER,
    critical INTEGER,
    warnings INTEGER,
    summary_json TEXT
);
CREATE TABLE IF NOT EXISTS seo_audit_pages (
    run_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    status INTEGER,
    title TEXT,
    description TEXT,
    canonical TEXT,
    robots TEXT,
    h1_count INTEGER,
    words INTEGER,
    inbound INTEGER,
    score INTEGER,
    issues_json TEXT,
    schema_types TEXT,
    render_ms REAL,
    bytes INTEGER,
    PRIMARY KEY (run_id, path)
);

CREATE TABLE IF NOT EXISTS stripe_events (
    id TEXT PRIMARY KEY,
    type TEXT,
    received_at INTEGER NOT NULL
);
"""


def now():
    return int(time.time())


def get_db():
    if "db" not in g:
        path = current_app.config["DATABASE_PATH"]
        if path != ":memory:":
            os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(app):
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        _migrate(db)
        db.commit()


# Columns added after launch: (table, column, definition). Applied once, in order.
MIGRATIONS = [
    ("listings", "featured_subscription_id", "TEXT"),
    ("users", "session_version", "INTEGER NOT NULL DEFAULT 0"),
    ("listings", "verification_requested_at", "INTEGER"),
    ("listings", "verification_request_type", "TEXT"),
    ("listings", "verification_request_note", "TEXT"),
]


def _migrate(db):
    for table, col, decl in MIGRATIONS:
        have = {r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()}
        if col not in have:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid
