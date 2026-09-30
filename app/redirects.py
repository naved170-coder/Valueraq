"""URL change system (§38, §72): 301s without chains, 410s, logging."""
from . import db
from .seo import log_change


def add_redirect(from_path, to_path, by="system", reason=None, status=301):
    if from_path == to_path:
        return
    # 1. Anything that pointed at from_path now points straight at to_path (no chains).
    for r in db.query("SELECT from_path FROM redirects WHERE to_path = ?", (from_path,)):
        db.execute("UPDATE redirects SET to_path=? WHERE from_path=?", (to_path, r["from_path"]))
        log_change(r["from_path"], "redirect", from_path, to_path, by, "chain collapsed")
    # 2. If the target itself redirects, follow it to the end.
    seen = {from_path}
    target = to_path
    while True:
        nxt = db.query("SELECT to_path FROM redirects WHERE from_path=?", (target,), one=True)
        if not nxt or nxt["to_path"] in seen:
            break
        seen.add(target)
        target = nxt["to_path"]
    # 3. The destination must not itself be gone.
    db.execute("DELETE FROM gone_urls WHERE path=?", (from_path,))
    # A path that now redirects can't also be a redirect target loop.
    db.execute("DELETE FROM redirects WHERE from_path=? AND to_path=?", (target, from_path))
    old = db.query("SELECT to_path FROM redirects WHERE from_path=?", (from_path,), one=True)
    db.execute("INSERT INTO redirects(from_path, to_path, status, reason, created_at) VALUES (?,?,?,?,?) "
               "ON CONFLICT(from_path) DO UPDATE SET to_path=excluded.to_path, status=excluded.status, "
               "reason=excluded.reason", (from_path, target, status, reason, db.now()))
    log_change(from_path, "redirect", old["to_path"] if old else None, target, by, reason)
    _invalidate()


def mark_gone(path, by="system", reason=None):
    db.execute("DELETE FROM redirects WHERE from_path=?", (path,))
    db.execute("INSERT OR REPLACE INTO gone_urls(path, reason, created_at) VALUES (?,?,?)", (path, reason, db.now()))
    log_change(path, "status", "200", "410", by, reason)
    _invalidate()


def remove_redirect(from_path, by="admin"):
    old = db.query("SELECT to_path FROM redirects WHERE from_path=?", (from_path,), one=True)
    db.execute("DELETE FROM redirects WHERE from_path=?", (from_path,))
    if old:
        log_change(from_path, "redirect", old["to_path"], None, by, "removed")
    _invalidate()


def chains():
    """Return redirects whose target is itself redirected (should be empty)."""
    return db.query("SELECT a.from_path, a.to_path, b.to_path AS final FROM redirects a "
                    "JOIN redirects b ON a.to_path = b.from_path")


def _invalidate():
    from . import invalidate_redirect_cache
    invalidate_redirect_cache()
