"""Jinja filters and context processors."""
import datetime

from flask import current_app, g, request, url_for

from . import auth, catalog


def money(v, currency="USD", compact=False):
    if v is None or v == "":
        return "—"
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    sym = {"USD": "$", "GBP": "£", "EUR": "€", "CAD": "CA$", "AUD": "A$"}.get(currency or "USD", "")
    neg = v < 0
    v = abs(v)
    if compact and v >= 1_000_000:
        s = f"{sym}{v / 1_000_000:.2f}M".replace(".00M", "M")
    elif compact and v >= 10_000:
        s = f"{sym}{v / 1000:.0f}K"
    else:
        s = f"{sym}{v:,.0f}"
    return ("−" if neg else "") + s


def num(v, digits=0):
    if v is None or v == "":
        return "—"
    try:
        return f"{float(v):,.{digits}f}"
    except (TypeError, ValueError):
        return str(v)


def pct(v, digits=0, signed=False):
    if v is None or v == "":
        return "—"
    v = float(v)
    s = f"{v:+.{digits}f}%" if signed else f"{v:.{digits}f}%"
    return s.replace("-", "−")


def effect(v):
    """+0.08 → '+8%'"""
    if not v:
        return "0%"
    return f"{v * 100:+.0f}%".replace("-", "−")


def human_date(v):
    if not v:
        return ""
    if isinstance(v, (int, float)):
        d = datetime.datetime.fromtimestamp(v, datetime.timezone.utc).date()
    else:
        d = datetime.date.fromisoformat(str(v)[:10])
    return d.strftime("%B %-d, %Y")


def mult(v):
    if v is None:
        return "—"
    return f"{float(v):.1f}×"


def register(app):
    import json as _json
    app.jinja_env.filters['fromjson'] = _json.loads
    app.jinja_env.filters.update(money=money, num=num, pct=pct, effect=effect, human_date=human_date, mult=mult)

    @app.context_processor
    def _ctx():
        cfg = current_app.config

        def static(path):
            return url_for("static", filename=path) + "?v=" + cfg["STATIC_VERSION"]

        return dict(
            BRAND=cfg["BRAND"],
            SITE_URL=cfg["SITE_URL"],
            cfg=cfg,
            user=g.get("user"),
            premium=auth.is_premium(),
            csrf_token=auth.csrf_token,
            static=static,
            nav_tools=catalog.TOOLS,
            nav_calcs=catalog.CALCULATORS,
            nav_cats=catalog.CATEGORIES,
            current_path=request.path,
            year=datetime.date.today().year,
            form_t0=int(__import__('time').time()),
        )
