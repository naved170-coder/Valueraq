"""Render a static, self-contained design preview of every public page.

    python scripts/freeze_preview.py OUT_DIR

Links become relative, CSS is inlined, first-party scripts are removed (no
server in a static preview), and forms show a note instead of submitting.
This is for design review only; the real site is the Flask app.
"""
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.config import TestConfig  # noqa: E402

EXTRA = ["/sell/", "/login/", "/signup/", "/marketplace/", "/blog/"]
BANNER = ('<div class="preview-bar" role="note">Design preview: a static snapshot of VALUERAQ. Calculations, '
          'accounts and the marketplace run on the deployed site; example results are shown instead.</div>')
PREVIEW_CSS = """
.preview-bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:40;background:var(--ink);color:var(--paper);
font:500 .8rem/1.4 var(--f-body);padding:.5rem 16px;text-align:center}
.site-head{top:calc(env(safe-area-inset-top,0px) + 2.1rem)}
.preview-note{display:none;margin-top:.6rem}
form.tried .preview-note{display:block}
"""
FORM_JS = """<script>
document.addEventListener('submit',function(e){e.preventDefault();var f=e.target;f.classList.add('tried');
if(!f.querySelector('.preview-note')){var p=document.createElement('p');p.className='alert preview-note';
p.textContent='This form works on the live site. In this preview the example result above shows what it returns.';
f.appendChild(p);}},true);
</script>"""


def out_file(path):
    return "index.html" if path == "/" else path.strip("/") + "/index.html"


def main(out):
    app = create_app(TestConfig, DATABASE_PATH=os.path.join(tempfile.mkdtemp(), "p.db"))
    c = app.test_client()
    site = app.config["SITE_URL"]
    paths = ["/"]
    idx = c.get("/sitemap.xml").get_data(as_text=True)
    for child in re.findall(r"<loc>([^<]+)</loc>", idx):
        for loc in re.findall(r"<loc>([^<]+)</loc>", c.get(child.replace(site, "")).get_data(as_text=True)):
            p = loc.replace(site, "")
            if p not in paths:
                paths.append(p)
    paths += [p for p in EXTRA if p not in paths]
    frozen = set(paths)
    css = open(os.path.join(app.static_folder, "css", "site.css"), encoding="utf-8").read() + PREVIEW_CSS

    for path in paths:
        html = c.get(path).get_data(as_text=True)
        depth = 0 if path == "/" else path.strip("/").count("/") + 1
        up = "../" * depth

        def rel(m):
            attr, target = m.group(1), m.group(2)
            if target.startswith("/static/"):
                return f'{attr}="{up}{target[1:].split("?")[0]}"'
            clean, _, frag = target.partition("#")
            clean = clean.split("?")[0]
            if clean in frozen:
                return f'{attr}="{up}{out_file(clean)}{("#" + frag) if frag else ""}"'
            return f'{attr}="{up}preview/index.html"'

        html = re.sub(r'(href|action)="(/[^"]*)"', rel, html)
        html = re.sub(r'<link rel="stylesheet" href="[^"]*site\.css[^"]*">', "<style>" + css + "</style>", html)
        html = re.sub(r'<script src="[^"]*"( defer)?></script>', "", html)
        html = html.replace('<a class="skip" href="#main">Skip to content</a>',
                            '<a class="skip" href="#main">Skip to content</a>' + BANNER)
        html = html.replace("</body>", FORM_JS + "</body>")
        if path == "/":
            # The published page is wrapped in its own skeleton: keep head + body contents only.
            head = re.search(r"<head>(.*?)</head>", html, re.S).group(1)
            head = re.sub(r"<meta charset[^>]*>|<meta name=\"viewport\"[^>]*>", "", head)
            head = re.sub(r"<title>.*?</title>", "<title>VALUERAQ Site Preview</title>", head)
            body = re.search(r"<body[^>]*>(.*)</body>", html, re.S).group(1)
            html = head + body
        dest = os.path.join(out, out_file(path))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(html)

    note = c.get("/this-is-a-preview-placeholder/").get_data(as_text=True)
    note = note.replace("This page doesn't exist", "Available on the live site")
    note = re.sub(r'<p class="lede">.*?</p>', '<p class="lede">Accounts, saved reports, search and the admin '
                  'dashboard need the running application, so they aren\'t part of this static preview.</p>', note, flags=re.S)
    note = re.sub(r'(href|action)="/([^"]*)"', lambda m: f'{m.group(1)}="../{out_file("/" + m.group(2)) if m.group(2) and "/" + m.group(2) in frozen else "index.html"}"', note)
    note = re.sub(r'<link rel="stylesheet" href="[^"]*site\.css[^"]*">', "<style>" + css + "</style>", note)
    note = re.sub(r'<script src="[^"]*"( defer)?></script>', "", note)
    os.makedirs(os.path.join(out, "preview"), exist_ok=True)
    with open(os.path.join(out, "preview", "index.html"), "w", encoding="utf-8") as fh:
        fh.write(note)
    for asset in ("brand/favicon.svg",):
        os.makedirs(os.path.join(out, "static", os.path.dirname(asset)), exist_ok=True)
        with open(os.path.join(app.static_folder, asset), "rb") as s, open(os.path.join(out, "static", asset), "wb") as d:
            d.write(s.read())
    print(len(paths) + 1, "pages written to", out)


if __name__ == "__main__":
    main(sys.argv[1])
