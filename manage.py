"""Small admin CLI.

  python manage.py run                   # development server on :5000
  python manage.py create-admin EMAIL    # create or promote an admin (prompts for password)
  python manage.py audit                 # run the SEO acceptance audit; exit 1 on critical issues
  python manage.py expire-featured       # clear featured flags past their end date (run daily)
"""
import getpass
import os
import sys

from app import create_app, db


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    cmd = argv[0]
    if cmd == "run":
        os.environ.setdefault("ENFORCE_CANONICAL_HOST", "0")
        os.environ.setdefault("SESSION_COOKIE_SECURE", "0")
        from app.config import Config
        app = create_app(Config, ENFORCE_CANONICAL_HOST=False, SESSION_COOKIE_SECURE=False)
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=bool(os.environ.get("DEBUG")))
        return 0
    app = create_app()
    with app.app_context():
        if cmd == "create-admin":
            email = argv[1].strip().lower()
            from app import auth
            u = db.query("SELECT * FROM users WHERE email=?", (email,), one=True)
            if u:
                db.execute("UPDATE users SET role='admin' WHERE id=?", (u["id"],))
                print(f"{email} is now an admin.")
            else:
                pw = os.environ.get("ADMIN_PASSWORD") or getpass.getpass("Password (10+ characters): ")
                if len(pw) < 10:
                    print("Password too short.")
                    return 1
                uid = auth.create_user(email, pw)
                db.execute("UPDATE users SET role='admin' WHERE id=?", (uid,))
                print(f"Admin {email} created.")
            return 0
        if cmd == "audit":
            from app import audit
            summary, results = audit.run(store=True)
            print(f"{summary['pages']} URLs · {summary['indexable']} indexable · {summary['sitemap_urls']} in sitemaps · "
                  f"{summary['critical']} critical · {summary['warnings']} warnings")
            for r in results:
                for i in r["issues"]:
                    if i["severity"] != "info":
                        print(f"  [{i['severity']}] {r['path']}: {i['message']}")
            for i in summary["site_issues"]:
                print(f"  [{i['severity']}] site: {i['message']}")
            return 1 if summary["critical"] else 0
        if cmd == "backup":
            from app import backup
            row = backup.run("manual")
            print(row["status"], row["object_key"], row.get("error") or f'{row["bytes"]} bytes')
            return 0 if row["status"] == "ok" else 1
        if cmd == "restore-backup":
            # python manage.py restore-backup backups/valueraq-YYYYMMDD-HHMMSS.db.gz [--apply]
            import shutil
            import sqlite3
            from app import backup
            raw = backup.fetch(argv[1])
            target = app.config["DATABASE_PATH"]
            staged = target + ".restore"
            with open(staged, "wb") as fh:
                fh.write(raw)
            ok = sqlite3.connect(staged).execute("PRAGMA integrity_check").fetchone()[0]
            if ok != "ok":
                print("Downloaded backup failed its integrity check:", ok)
                return 1
            print(f"Backup downloaded and verified: {staged} ({len(raw)} bytes)")
            if "--apply" not in argv:
                print("Nothing was changed. Re-run with --apply to replace the live database with it.")
                return 0
            shutil.copy2(target, target + ".before-restore")
            for ext in ("-wal", "-shm"):
                if os.path.exists(target + ext):
                    os.remove(target + ext)
            os.replace(staged, target)
            print("Live database replaced. The previous one is saved as", target + ".before-restore",
                  "- restart the web service now.")
            return 0
        if cmd == "expire-featured":
            from app import billing
            billing.expire_featured()
            print("Done.")
            return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
