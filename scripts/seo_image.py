"""Branded images for articles, made in code (no AI image service, no stock photos).

  Featured image (1200x630 PNG, also used when the page is shared):
      python scripts/seo_image.py feature --slug saas-valuation-multiples \
          --title "SaaS Valuation Multiples Explained" --label "Guide · SaaS"

  Bar chart (SVG, sharp at any size, a few KB):
      python scripts/seo_image.py bar --slug saas-valuation-multiples --name default-ranges \
          --title "Default ARR multiple ranges" --unit "x" --data "Low=2.5,Midpoint=4,High=6"

Files are written to app/static/img/articles/. Each command prints the front
matter or markdown line to paste into the article. Charts must only show
figures that appear in the article and come from the published methodology.
"""
import argparse
import html
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "app", "static", "img", "articles")
WEB = "/static/img/articles/"
FONT = "'Liberation Sans', Arial, Helvetica, sans-serif"
C = dict(bg="#f2f5f3", surface="#ffffff", rule="#d3dbd7", ink="#0f1c19", muted="#53625d", green="#0d6a54",
         gold="#d99a14", soft="#d8ebe4")
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _mark(w):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="2 5 28 23" width="{w}" style="flex:none">'
            f'<rect x="4" y="14" width="24" height="5" rx="2.5" fill="{C["green"]}"/>'
            f'<rect x="14.25" y="7" width="3.5" height="19" rx="1.75" fill="{C["gold"]}"/></svg>')


def _motif(seed):
    """A quiet row of bars on the right; heights vary with the title so pages don't all look identical."""
    hs = [(seed * (i + 3) * 37) % 60 + 30 for i in range(7)]
    bars = "".join(f'<rect x="{i * 46}" y="{300 - h * 3}" width="30" height="{h * 3}" rx="6" '
                   f'fill="{C["gold"] if i == seed % 7 else C["soft"]}"/>' for i, h in enumerate(hs))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="310" height="300" viewBox="0 0 310 300">{bars}</svg>'


def feature_html(title, label):
    size = 68 if len(title) <= 38 else 58 if len(title) <= 60 else 48
    seed = sum(ord(ch) for ch in title)
    return f'''<html><body style="margin:0;width:1200px;height:630px;background:{C["bg"]};font-family:{FONT};overflow:hidden">
<div style="box-sizing:border-box;width:1200px;height:630px;padding:56px 64px;display:flex;flex-direction:column;justify-content:space-between;border-top:14px solid {C["green"]}">
  <div style="display:flex;align-items:center;gap:16px">{_mark(54)}<span style="font-weight:700;font-size:36px;letter-spacing:.08em;color:{C["ink"]}">VALUERAQ</span></div>
  <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:40px">
    <div style="max-width:760px">
      <div style="font-size:24px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:{C["green"]};margin-bottom:18px">{html.escape(label)}</div>
      <div style="font-size:{size}px;font-weight:700;line-height:1.12;color:{C["ink"]}">{html.escape(title)}</div>
    </div>
    {_motif(seed)}
  </div>
  <div style="display:flex;justify-content:space-between;font-size:24px;color:{C["muted"]}"><span>Free valuation tools for digital businesses</span><span style="font-weight:700;color:{C["green"]}">www.valueraq.com</span></div>
</div></body></html>'''


def feature(slug, title, label):
    from PIL import Image
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        pg.set_content(feature_html(title, label))
        raw = pg.screenshot()
        b.close()
    img = Image.open(io.BytesIO(raw)).convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT,
                                                              dither=Image.Dither.NONE)
    path = os.path.join(OUT, slug + ".png")
    img.save(path, optimize=True)
    return path


def bar_svg(title, pairs, unit=""):
    """Horizontal bar chart. pairs = [(label, number)]."""
    w, row, left, top = 720, 46, 210, 64
    h = top + row * len(pairs) + 24
    mx = max(v for _, v in pairs) or 1
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
           f'font-family="Arial, Helvetica, sans-serif"><title>{html.escape(title)}</title>'
           f'<rect width="{w}" height="{h}" fill="{C["surface"]}"/>'
           f'<text x="24" y="38" font-size="20" font-weight="700" fill="{C["ink"]}">{html.escape(title)}</text>']
    for i, (label, v) in enumerate(pairs):
        y = top + i * row
        bw = max(4, (w - left - 110) * v / mx)
        num = f"{v:g}{unit}" if unit not in ("$",) else f"${v:,.0f}"
        out.append(f'<text x="{left - 14}" y="{y + 23}" font-size="15" text-anchor="end" fill="{C["ink"]}">{html.escape(label)}</text>'
                   f'<rect x="{left}" y="{y + 4}" width="{bw:.1f}" height="28" rx="5" fill="{C["green"] if i % 2 == 0 else C["gold"]}"/>'
                   f'<text x="{left + bw + 10:.1f}" y="{y + 23}" font-size="15" font-weight="700" fill="{C["ink"]}">{html.escape(num)}</text>')
    out.append(f'<text x="{w - 24}" y="{h - 8}" font-size="11" text-anchor="end" fill="{C["muted"]}">valueraq.com</text></svg>')
    return "".join(out)


def bar(slug, name, title, pairs, unit=""):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{slug}-{name}.svg")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(bar_svg(title, pairs, unit))
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("feature")
    f.add_argument("--slug", required=True); f.add_argument("--title", required=True); f.add_argument("--label", default="Guide")
    b = sub.add_parser("bar")
    b.add_argument("--slug", required=True); b.add_argument("--name", required=True); b.add_argument("--title", required=True)
    b.add_argument("--data", required=True, help='"Label=number,Label=number"'); b.add_argument("--unit", default="")
    a = ap.parse_args(argv)
    if not _SLUG.match(a.slug) or (a.cmd == "bar" and not _SLUG.match(a.name)):
        sys.exit("slug and name must be lower-case words joined by hyphens")
    if a.cmd == "feature":
        path = feature(a.slug, a.title, a.label)
        print(f"{os.path.getsize(path) // 1024} KB  {path}")
        print(f"image: {WEB}{a.slug}.png\nimage_alt: {a.title} (VALUERAQ {a.label.split('·')[0].strip().lower()})")
    else:
        pairs = [(k.strip(), float(v)) for k, v in (x.split("=", 1) for x in a.data.split(",") if "=" in x)]
        if not 2 <= len(pairs) <= 10:
            sys.exit("give between 2 and 10 bars")
        if any(v < 0 for _, v in pairs):
            sys.exit("bar charts cannot show negative numbers; use a table instead")
        path = bar(a.slug, a.name, a.title, pairs, a.unit)
        desc = ", ".join(f"{k} {v:g}{a.unit}" for k, v in pairs)
        print(f"{os.path.getsize(path)} bytes  {path}")
        print(f'![{a.title}: {desc}]({WEB}{a.slug}-{a.name}.svg){{: width="720" height="{64 + 46 * len(pairs) + 24}" loading="lazy" }}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
