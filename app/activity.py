"""Activity log (who did what) and server-error log.

Both are written best-effort: a failure to record must never break the page.
"""
import hashlib
import traceback as _tb

from flask import current_app, g, request

from . import db


def _ip():
    ip = request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For", request.remote_addr or "")
    return ip.split(",")[0].strip()[:60]


def record(action, target=None, detail=None, user=None, email=None):
    """Add one line to the activity log. `user` defaults to the signed-in user."""
    try:
        u = user if user is not None else g.get("user")
        db.execute("INSERT INTO activity_log(at, user_id, user_email, ip, action, target, detail) VALUES (?,?,?,?,?,?,?)",
                   (db.now(), u["id"] if u else None, (u["email"] if u else email or "")[:200] or None, _ip(),
                    action[:60], (str(target)[:200] if target is not None else None),
                    (str(detail)[:500] if detail is not None else None)))
    except Exception as e:  # never let logging break a request
        current_app.logger.error("activity log failed: %s", e)


def record_error(exc):
    """Store an unhandled server error once per distinct problem and email the admins
    the first time it appears (then at most once a day while it keeps happening)."""
    try:
        tb = "".join(_tb.format_exception(type(exc), exc, exc.__traceback__))[-6000:]
        frames = _tb.extract_tb(exc.__traceback__)
        where = f"{frames[-1].filename}:{frames[-1].lineno}" if frames else ""
        fp = hashlib.sha256(f"{type(exc).__name__}|{where}".encode()).hexdigest()[:16]
        now = db.now()
        row = db.query("SELECT * FROM error_log WHERE fingerprint=?", (fp,), one=True)
        if row:
            db.execute("UPDATE error_log SET last_at=?, count=count+1, path=?, method=?, message=?, traceback=? "
                       "WHERE fingerprint=?", (now, request.path[:300], request.method, str(exc)[:500], tb, fp))
        else:
            db.execute("INSERT INTO error_log(fingerprint, first_at, last_at, method, path, error_type, message, traceback) "
                       "VALUES (?,?,?,?,?,?,?,?)", (fp, now, now, request.method, request.path[:300],
                                                    type(exc).__name__, str(exc)[:500], tb))
        current_app.logger.error("server error %s on %s %s: %s", fp, request.method, request.path, exc)
        if not row or not row["notified_at"] or row["notified_at"] < now - 86400:
            from . import mailer
            if mailer.admin_error_alert(type(exc).__name__, str(exc)[:300], request.method, request.path,
                                        (row["count"] + 1) if row else 1):
                db.execute("UPDATE error_log SET notified_at=? WHERE fingerprint=?", (now, fp))
    except Exception as e:
        current_app.logger.error("error log failed: %s", e)
