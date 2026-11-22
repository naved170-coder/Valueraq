"""Self-repair for a damaged SQLite database ("database disk image is malformed").

Runs once when the website starts, before anything else opens the database:

  1. A quick check. If the file is healthy, nothing happens.
  2. The damaged file (with its -wal/-shm companions) is copied, untouched, to <data dir>/damaged-<time>/.
  3. First try: rebuild every index on a copy (the usual cause). If the copy then passes, it replaces the file.
  4. Otherwise: a fresh database is created and every row that can still be read is copied into it, table
     by table; a table whose full read fails is read in rowid ranges so only the damaged part is skipped.
  5. Tables that lost rows get them back from the newest good off-site backup, where it has them
     (only rows that are missing; nothing that survived is overwritten).
  6. The new file must pass a full integrity check before it replaces the live one.

Both web workers start at the same time, so a file lock makes sure only one of them repairs.
"""
import fcntl
import json
import logging
import os
import shutil
import sqlite3
import time

log = logging.getLogger("valueraq.dbrepair")

# Tables whose lost rows are worth taking back from the last backup (people's own records).
RESTORE_FROM_BACKUP = {
    "users", "reports", "listings", "inquiries", "messages", "message_files", "watchlist", "saved_searches",
    "blog_posts", "seo_overrides", "seo_change_log", "redirects", "gone_urls", "keywords", "contact_messages",
    "content_approvals", "gsc_daily", "gsc_rows", "rank_reviews", "rank_events", "rank_actions", "stripe_events",
}


def healthy(path):
    try:
        c = sqlite3.connect(path, timeout=30)
        try:
            r = c.execute("PRAGMA quick_check").fetchall()
        finally:
            c.close()
        return len(r) == 1 and r[0][0] == "ok"
    except sqlite3.DatabaseError as e:
        log.error("database check failed: %s", e)
        return False


def _full_ok(path):
    c = sqlite3.connect(path)
    try:
        return c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    except sqlite3.DatabaseError:
        return False
    finally:
        c.close()


def _keep_damaged(path):
    keep = os.path.join(os.path.dirname(path), "damaged-" + time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(keep, exist_ok=True)
    for ext in ("", "-wal", "-shm"):
        if os.path.exists(path + ext):
            shutil.copy2(path + ext, os.path.join(keep, os.path.basename(path) + ext))
    return keep


def _try_reindex(path, work):
    for ext in ("", "-wal", "-shm"):
        if os.path.exists(path + ext):
            shutil.copy2(path + ext, work + ext)
    try:
        c = sqlite3.connect(work)
        c.execute("REINDEX")
        c.commit()
        c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        c.execute("PRAGMA journal_mode = DELETE")
        c.close()
    except sqlite3.DatabaseError as e:
        log.warning("reindex did not work: %s", e)
        return False
    return _full_ok(work)


def _rows(src, table, cols):
    """All readable rows. Falls back to rowid ranges so one bad page only costs the rows on it."""
    sel = ", ".join(f'"{c}"' for c in cols)
    try:
        return src.execute(f'SELECT {sel} FROM "{table}"').fetchall(), False
    except sqlite3.DatabaseError:
        pass
    out, damaged = [], True
    try:
        hi = src.execute(f'SELECT MAX(rowid) FROM "{table}"').fetchone()[0] or 0
    except sqlite3.DatabaseError:
        hi = 5_000_000
    step = 500
    lo = 0
    while lo <= hi:
        try:
            out += src.execute(f'SELECT {sel} FROM "{table}" WHERE rowid BETWEEN ? AND ?',
                               (lo, lo + step - 1)).fetchall()
        except sqlite3.DatabaseError:
            for rid in range(lo, lo + step):   # narrow down inside the bad block
                try:
                    out += src.execute(f'SELECT {sel} FROM "{table}" WHERE rowid=?', (rid,)).fetchall()
                except sqlite3.DatabaseError:
                    pass
        lo += step
    return out, damaged


def _salvage(path, work, build_schema):
    if os.path.exists(work):
        os.remove(work)
    build_schema(work)                       # the app's current tables, empty
    src = sqlite3.connect(path)
    dst = sqlite3.connect(work)
    dst.execute("PRAGMA foreign_keys = OFF")
    report = {}
    tables = [r[0] for r in dst.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
    for t in tables:
        dcols = [r[1] for r in dst.execute(f'PRAGMA table_info("{t}")').fetchall()]
        try:
            scols = [r[1] for r in src.execute(f'PRAGMA table_info("{t}")').fetchall()]
        except sqlite3.DatabaseError:
            scols = []
        cols = [c for c in dcols if c in scols]
        if not cols:
            report[t] = {"copied": 0, "damaged": True}
            continue
        rows, damaged = _rows(src, t, cols)
        ph = ", ".join("?" * len(cols))
        names = ", ".join(f'"{c}"' for c in cols)
        dst.executemany(f'INSERT OR IGNORE INTO "{t}" ({names}) VALUES ({ph})', rows)
        report[t] = {"copied": len(rows), "damaged": damaged}
    dst.commit()
    src.close()
    dst.close()
    return report


def _merge_backup(work, backup_db, report):
    """Put back rows a damaged table lost, from the last good backup. Only missing rows are added."""
    if not backup_db:
        return
    dst = sqlite3.connect(work)
    dst.execute("PRAGMA foreign_keys = OFF")
    b = sqlite3.connect(backup_db)
    for t, info in report.items():
        if not info["damaged"] or t not in RESTORE_FROM_BACKUP:
            continue
        try:
            bcols = [r[1] for r in b.execute(f'PRAGMA table_info("{t}")').fetchall()]
        except sqlite3.DatabaseError:
            continue
        dcols = [r[1] for r in dst.execute(f'PRAGMA table_info("{t}")').fetchall()]
        cols = [c for c in dcols if c in bcols]
        if not cols:
            continue
        names = ", ".join(f'"{c}"' for c in cols)
        before = dst.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        rows = b.execute(f'SELECT {names} FROM "{t}"').fetchall()
        dst.executemany(f'INSERT OR IGNORE INTO "{t}" ({names}) VALUES ({", ".join("?" * len(cols))})', rows)
        info["from_backup"] = dst.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] - before
    dst.commit()
    b.close()
    dst.close()


def _swap(path, work):
    for ext in ("-wal", "-shm"):
        if os.path.exists(path + ext):
            os.remove(path + ext)
    os.replace(work, path)


def repair_if_needed(path, build_schema, fetch_backup=None):
    """Returns None when healthy, else a dict describing the repair. Never raises: the site must still start."""
    if path == ":memory:" or not os.path.exists(path):
        return None
    lock_path = path + ".repair-lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)      # the other worker waits here, then finds a healthy file
        try:
            if healthy(path):
                return None
            log.error("database is damaged; starting repair")
            keep = _keep_damaged(path)
            work = path + ".repair"
            result = {"kept_copy": keep, "at": int(time.time())}
            if _try_reindex(path, work):
                result["method"] = "reindex"
            else:
                for ext in ("-wal", "-shm"):
                    if os.path.exists(work + ext):
                        os.remove(work + ext)
                report = _salvage(path, work, build_schema)
                backup_db = None
                if fetch_backup and any(i["damaged"] for i in report.values()):
                    try:
                        backup_db = fetch_backup()
                    except Exception as e:
                        log.error("could not fetch the last backup: %s", e)
                _merge_backup(work, backup_db, report)
                result["method"] = "salvage"
                result["tables"] = report
                result["backup_used"] = bool(backup_db)
            if not _full_ok(work):
                log.error("repaired copy failed its integrity check; live file left as it was")
                result["swapped"] = False
                return result
            _swap(path, work)
            result["swapped"] = True
            with open(os.path.join(keep, "repair.json"), "w") as fh:
                json.dump(result, fh, indent=1)
            log.error("database repaired (%s); damaged copy kept in %s; details: %s",
                      result["method"], keep, json.dumps(result.get("tables", {}))[:3000])
            return result
        except Exception as e:
            log.exception("database repair failed: %s", e)
            return {"error": str(e)}
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
