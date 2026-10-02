"""VALUERAQ application factory."""
import gzip
import time
from urllib.parse import urlsplit

from flask import Flask, g, redirect, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.routing import RequestRedirect

from . import auth, db
from .config import Config

# Trailing-slash normalisation issued by the router should be a 301 (§34).
RequestRedirect.code = 301

_redirect_cache = {"at": 0, "map": {}, "gone": set()}


def _load_redirects(app):
    t = time.time()
    if app.config.get("TESTING") or t - _redirect_cache["at"] > 60:
        rows = db.query("SELECT from_path, to_path, status FROM redirects")
        _redirect_cache["map"] = {r["from_path"]: (r["to_path"], r["status"]) for r in rows}
        _redirect_cache["gone"] = {r["path"] for r in db.query("SELECT path FROM gone_urls")}
        _redirect_cache["at"] = t
    return _redirect_cache


def invalidate_redirect_cache():
    _redirect_cache["at"] = 0


def create_app(config_object=Config, **overrides):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object)
    app.config.update(overrides)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.url_map.strict_slashes = True
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    db.init_db(app)
    app.teardown_appcontext(db.close_db)

    if not app.debug and not app.config.get("TESTING"):
        import logging
        app.logger.setLevel(logging.INFO)  # so "email sent" and "backup ok" lines reach the host's logs

    from . import backup
    backup.start_scheduler(app)

    from . import filters
    filters.register(app)

    from .views import public, marketplace, account, api, admin, seo_files, market_account
    for bp in (public.bp, marketplace.bp, account.bp, api.bp, admin.bp, seo_files.bp, market_account.bp):
        app.register_blueprint(bp)

    preferred = urlsplit(app.config["SITE_URL"])

    @app.before_request
    def _canonical_host_and_redirects():
        g.t0 = time.perf_counter()
        host = (request.host or "").split(":")[0].lower()
        if (app.config["ENFORCE_CANONICAL_HOST"]
                and host not in app.config["DEV_HOSTS"]
                and request.path != app.config["HEALTH_CHECK_PATH"]):
            if host != preferred.hostname or request.scheme != preferred.scheme:
                return redirect(app.config["SITE_URL"] + request.full_path.rstrip("?"), 301)
        path = request.path
        if path.startswith("/static/"):
            return None
        if path != path.lower() and not path.startswith("/api/"):
            qs = ("?" + request.query_string.decode()) if request.query_string else ""
            return redirect(path.lower() + qs, 301)
        cache = _load_redirects(app)
        hit = cache["map"].get(path)
        if hit:
            db.execute("UPDATE redirects SET hits = hits + 1 WHERE from_path = ?", (path,))
            qs = ("?" + request.query_string.decode()) if request.query_string else ""
            return redirect(hit[0] + qs, hit[1])
        if path in cache["gone"]:
            return render_template("errors/410.html"), 410
        return None

    @app.before_request
    def _session_and_csrf():
        if request.path.startswith("/static/"):
            return None
        auth.load_user()
        auth.check_csrf()
        return None

    @app.after_request
    def _headers(resp):
        path = request.path
        cfg = app.config
        # Robots header for private/utility paths and for pages that decided noindex.
        robots = g.get("robots_header")
        if any(path.startswith(p) for p in cfg["PRIVATE_PATH_PREFIXES"]):
            robots = "noindex, nofollow"
        elif robots is None and any(path.startswith(p) for p in cfg["NOINDEX_PATH_PREFIXES"]):
            robots = "noindex, follow"
        if robots:
            resp.headers["X-Robots-Tag"] = robots

        # Security headers.
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self' https://checkout.stripe.com "
            "https://billing.stripe.com; object-src 'none'")
        if not app.config.get("TESTING") and request.scheme == "https":
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

        # Caching.
        if path.startswith("/static/"):
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        elif "Cache-Control" not in resp.headers:
            private = (g.get("user") is not None or any(path.startswith(p) for p in cfg["NOINDEX_PATH_PREFIXES"])
                       or request.method != "GET" or resp.status_code >= 400
                       or any(h.lower() == "set-cookie" for h in resp.headers.keys()))
            if private:
                resp.headers["Cache-Control"] = "private, no-store"
            else:
                resp.headers["Cache-Control"] = (f"public, max-age={cfg['PUBLIC_CACHE_SECONDS']}, "
                                                 f"s-maxage={cfg['CDN_CACHE_SECONDS']}, stale-while-revalidate=300")
                resp.headers["Vary"] = "Accept-Encoding, Cookie"

        if g.get("t0"):
            resp.headers["Server-Timing"] = f"app;dur={(time.perf_counter() - g.t0) * 1000:.1f}"

        # Compression (the CDN/proxy may also compress; skip if already encoded).
        compressible = ((resp.mimetype or "").startswith("text/") or resp.mimetype in
                        ("application/json", "application/xml", "application/javascript", "image/svg+xml"))
        if (compressible and resp.status_code in (200, 404, 410) and not resp.direct_passthrough
                and "Content-Encoding" not in resp.headers
                and "gzip" in request.headers.get("Accept-Encoding", "")):
            data = resp.get_data()
            if len(data) > 1024:
                resp.set_data(gzip.compress(data, 6))
                resp.headers["Content-Encoding"] = "gzip"
                if "Accept-Encoding" not in resp.headers.get("Vary", ""):
                    resp.headers["Vary"] = (resp.headers.get("Vary", "") + ", Accept-Encoding").strip(", ")
        return resp

    @app.errorhandler(404)
    def _404(_e):
        g.robots_header = "noindex, follow"
        return render_template("errors/404.html"), 404

    @app.errorhandler(410)
    def _410(_e):
        g.robots_header = "noindex, follow"
        return render_template("errors/410.html"), 410

    @app.errorhandler(429)
    def _429(_e):
        g.robots_header = "noindex, follow"
        return render_template("errors/429.html"), 429

    @app.errorhandler(400)
    def _400(e):
        return render_template("errors/400.html", message=getattr(e, "description", None)), 400

    @app.errorhandler(500)
    def _500(e):
        from . import activity
        activity.record_error(getattr(e, "original_exception", None) or e)
        return render_template("errors/500.html"), 500

    return app
