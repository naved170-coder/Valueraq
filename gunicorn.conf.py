"""Read automatically by gunicorn. Checks (and if needed repairs) the database once, in the master
process, before any worker starts, so a slow repair can't be cut off by the worker start-up timeout."""
import os


def on_starting(server):
    from flask import Flask
    from app.config import Config
    from app import db
    app = Flask("valueraq-dbcheck")
    app.config.from_object(Config)
    result = db.repair(app)
    if result:
        server.log.error("database repair result: %s", {k: v for k, v in result.items() if k != "tables"})
    os.environ["VQ_DB_CHECKED"] = "1"     # workers inherit this and skip the check
