"""Daily off-site database backups to Cloudflare R2.

  * A consistent snapshot is taken with SQLite's online backup API (safe while
    the site is serving requests), gzip-compressed and uploaded to the private
    bucket under backups/.
  * A small scheduler thread in each web worker checks every 30 minutes whether
    a successful backup exists from the last 24 hours. Workers coordinate through
    the backup_claims table so only one of them runs it.
  * The newest BACKUP_KEEP backups are kept; older ones are deleted.
  * Restore: `python manage.py restore-backup <key>` (see README).
"""
import datetime
import gzip
import os
import sqlite3
import tempfile
import threading
import time

from flask import current_app

from . import db
from .storage import R2, StorageError

PREFIX = "backups/"


def configured():
    c = current_app.config
    return bool(c.get("R2_ENDPOINT") and c.get("R2_ACCESS_KEY_ID") and c.get("R2_SECRET_ACCESS_KEY") and c.get("R2_BUCKET"))


def client():
    c = current_app.config
    return R2(c["R2_ENDPOINT"], c["R2_ACCESS_KEY_ID"], c["R2_SECRET_ACCESS_KEY"], c["R2_BUCKET"])


def snapshot_bytes(db_path):
    """Return a gzip-compressed, consistent copy of the SQLite database."""
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        src = sqlite3.connect(db_path, timeout=30)
        dst = sqlite3.connect(tmp)
        with dst:
            src.backup(dst)
        ok = dst.execute("PRAGMA integrity_check").fetchone()[0]
        dst.close()
        src.close()
        if ok != "ok":
            raise RuntimeError(f"snapshot failed its integrity check: {ok}")
        with open(tmp, "rb") as fh:
            raw = fh.read()
        return gzip.compress(raw, 6), len(raw)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def run(kind="scheduled", store=None):
    """Take one backup now. Returns the backups row (as a dict). Never raises."""
    c = current_app.config
    started = db.now()
    key = PREFIX + f"valueraq-{datetime.datetime.now(datetime.timezone.utc):%Y%m%d-%H%M%S}.db.gz"
    row = dict(object_key=key, kind=kind, status="failed", bytes=0, db_bytes=0, error=None, created_at=started)
    try:
        if store is None:
            if not configured():
                raise StorageError("File storage isn't configured (R2_* settings missing).")
            store = client()
        data, raw_len = snapshot_bytes(c["DATABASE_PATH"])
        store.put(key, data, "application/gzip")
        listed = {k: size for k, size, _ in store.list(key)}
        if listed.get(key) != len(data):
            raise StorageError("Uploaded backup could not be confirmed in storage.")
        row.update(status="ok", bytes=len(data), db_bytes=raw_len)
        prune(store)
    except Exception as e:  # report every failure on the admin page instead of crashing a worker
        row["error"] = str(e)[:300]
        current_app.logger.error("backup failed: %s", e)
    db.execute("INSERT INTO backups(object_key, kind, status, bytes, db_bytes, error, created_at, finished_at) "
               "VALUES (?,?,?,?,?,?,?,?)", (row["object_key"], row["kind"], row["status"], row["bytes"],
                                           row["db_bytes"], row["error"], row["created_at"], db.now()))
    if row["status"] == "ok":
        current_app.logger.info("backup ok: %s (%d bytes)", key, row["bytes"])
    return row


def prune(store):
    keep = current_app.config["BACKUP_KEEP"]
    keys = sorted(k for k, _, _ in store.list(PREFIX) if k.endswith(".db.gz"))
    for old in keys[:-keep] if len(keys) > keep else []:
        store.delete(old)
        db.execute("UPDATE backups SET status='pruned' WHERE object_key=? AND status='ok'", (old,))


def last_ok():
    return db.query("SELECT * FROM backups WHERE status='ok' ORDER BY created_at DESC LIMIT 1", one=True)


def due():
    last = last_ok()
    return not last or last["created_at"] < db.now() - current_app.config["BACKUP_EVERY_HOURS"] * 3600


def _claim(slot):
    """Only one worker gets True for a given slot (an hour bucket)."""
    conn = db.get_db()
    cur = conn.execute("INSERT OR IGNORE INTO backup_claims(slot, claimed_at) VALUES (?,?)", (slot, db.now()))
    conn.commit()
    return cur.rowcount == 1


def tick():
    """One scheduler check. Returns the backup row if this worker ran a backup."""
    if not configured() or not due():
        return None
    if not _claim(datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H")):
        return None
    return run("scheduled")


def start_scheduler(app):
    """Background thread per worker; safe with several workers thanks to _claim()."""
    if app.config.get("TESTING") or app.extensions.get("backup_scheduler"):
        return
    with app.app_context():
        if not configured():
            app.logger.info("backups: storage not configured, scheduler not started")
            return

    def loop():
        time.sleep(45)  # let the worker finish booting
        while True:
            try:
                with app.app_context():
                    tick()
            except Exception as e:
                app.logger.error("backup scheduler error: %s", e)
            time.sleep(1800)

    t = threading.Thread(target=loop, name="backup-scheduler", daemon=True)
    app.extensions["backup_scheduler"] = t
    t.start()


def fetch(key, store=None):
    """Download and decompress one backup; returns the raw SQLite file bytes."""
    if not key.startswith(PREFIX) or ".." in key:
        raise StorageError("Not a backup file.")
    return gzip.decompress((store or client()).get(key))
