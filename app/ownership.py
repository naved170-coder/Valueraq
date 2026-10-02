"""Automatic website-ownership check for listings.

The seller proves control of the listing's website by publishing a short code
in one of three places; we look for it and never need a human:

  1. a DNS TXT record on the domain:      valueraq-verify=<code>
  2. a file on the site:                  /valueraq-verify.txt containing the code
  3. a meta tag on the home page:         <meta name="valueraq-verify" content="<code>">

Fetching a URL supplied by a user is risky, so the fetcher only talks to public
internet addresses on the standard web ports, never follows a redirect to a
private address, reads a small capped amount, and the page content is never
shown to anyone: the only output is found / not found.
"""
import hashlib
import hmac
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

from flask import current_app

FILE_PATH = "/valueraq-verify.txt"
META_NAME = "valueraq-verify"
TXT_PREFIX = "valueraq-verify="
MAX_BYTES = 300_000
TIMEOUT = 6
DOH_URL = "https://cloudflare-dns.com/dns-query"
_HOST_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


def code_for(l):
    """Stable per-listing, per-seller code. Nothing is stored; it can't be guessed without the site's secret key."""
    key = str(current_app.config["SECRET_KEY"]).encode()
    return hmac.new(key, f"own:{l['id']}:{l['seller_id']}".encode(), hashlib.sha256).hexdigest()[:32]


def host_of(url):
    """Lower-case hostname of a listing URL, or None if it isn't a normal public web address."""
    try:
        u = urllib.parse.urlsplit((url or "").strip())
    except ValueError:
        return None
    if u.scheme not in ("http", "https") or u.username or u.password:
        return None
    try:
        if u.port not in (None, 80, 443):
            return None
    except ValueError:
        return None
    host = (u.hostname or "").lower().rstrip(".")
    try:
        host = host.encode("idna").decode()
    except UnicodeError:
        return None
    return host if _HOST_RE.match(host) else None


def _public(host):
    """True only if every address the name resolves to is a public internet address."""
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except OSError:
        return False
    if not infos:
        return False
    for info in infos:
        try:
            if not ipaddress.ip_address(info[4][0]).is_global:
                return False
        except ValueError:
            return False
    return True


class _Guard(urllib.request.HTTPRedirectHandler):
    max_redirections = 3

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        host = host_of(newurl)
        if not host or not _public(host):
            raise urllib.error.URLError("redirect to a disallowed address")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def http_get(url):
    """Fetch a small page from a public website. Returns text, or None on any problem."""
    host = host_of(url)
    if not host or not _public(host):
        return None
    opener = urllib.request.build_opener(_Guard())
    req = urllib.request.Request(url, headers={"User-Agent": "VALUERAQ-ownership-check/1.0", "Accept": "text/html,text/plain"})
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.read(MAX_BYTES).decode("utf-8", "replace")
    except Exception:
        return None


def dns_txt(host):
    """TXT records for a hostname via DNS-over-HTTPS. Returns a list of strings."""
    q = urllib.parse.urlencode({"name": host, "type": "TXT"})
    req = urllib.request.Request(f"{DOH_URL}?{q}", headers={"Accept": "application/dns-json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read(MAX_BYTES))
    except Exception:
        return []
    out = []
    for a in data.get("Answer") or []:
        if a.get("type") == 16:
            out.append("".join(re.findall(r'"([^"]*)"', a.get("data", ""))) or a.get("data", ""))
    return out


def _meta_has(html, code):
    for tag in re.findall(r"<meta\b[^>]*>", html or "", re.I):
        if re.search(r"""name\s*=\s*["']?%s["']?""" % re.escape(META_NAME), tag, re.I) and code in tag:
            return True
    return False


def check(l, fetch=None, txt=None):
    """Look for the listing's code. Returns the method that matched ('dns', 'file', 'meta') or None."""
    fetch, txt = fetch or http_get, txt or dns_txt
    host = host_of(l["website_url"])
    if not host:
        return None
    code = code_for(l)
    names = [host] + ([host[4:]] if host.startswith("www.") else [])
    for name in names:
        if any(TXT_PREFIX + code in rec.replace(" ", "") for rec in txt(name)):
            return "dns"
    base = f"https://{host}"
    body = fetch(base + FILE_PATH)
    if body and code in body[:2000]:
        return "file"
    if _meta_has(fetch(base + "/"), code):
        return "meta"
    return None
