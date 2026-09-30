import os, sys, tempfile, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, audit
from app.config import TestConfig
d = tempfile.mkdtemp()
app = create_app(TestConfig, DATABASE_PATH=os.path.join(d, 't.db'))
with app.app_context():
    s, res = audit.run(store=False)
    print(json.dumps({k: v for k, v in s.items() if k not in ('change_list', 'probes')}, indent=1, default=str))
    for r in res:
        iss = [i for i in r['issues'] if i['severity'] in ('critical', 'warning')]
        if iss:
            print(r['path'], r.get('words'), [i['code'] + ': ' + i['message'] for i in iss])
