"""Minimal S3-compatible client for Cloudflare R2 (AWS Signature Version 4, stdlib only).

Only what backups need: put, get, delete and list objects in one private bucket.
The signing code is checked in the tests against AWS's published example signatures.
"""
import datetime
import hashlib
import hmac
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

EMPTY_SHA = hashlib.sha256(b"").hexdigest()


class StorageError(RuntimeError):
    pass


def _q(s, safe="-_.~"):
    return urllib.parse.quote(str(s), safe=safe)


def sign(method, host, path, query, headers, payload_hash, access_key, secret_key, region, amz_date, service="s3"):
    """Return the Authorization header value for one request.

    `path` must already be URI-encoded; `query` is a dict of raw values;
    `headers` are the extra headers to sign (host and x-amz-* are added here).
    """
    date = amz_date[:8]
    all_headers = {"host": host, "x-amz-content-sha256": payload_hash, "x-amz-date": amz_date}
    all_headers.update({k.lower(): " ".join(str(v).split()) for k, v in headers.items()})
    signed = ";".join(sorted(all_headers))
    canonical_query = "&".join(f"{_q(k)}={_q(v)}" for k, v in sorted(query.items()))
    canonical = "\n".join([method, path, canonical_query,
                           "".join(f"{k}:{all_headers[k]}\n" for k in sorted(all_headers)), signed, payload_hash])
    scope = f"{date}/{region}/{service}/aws4_request"
    to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical.encode()).hexdigest()])

    def h(key, msg):
        return hmac.new(key, msg.encode(), hashlib.sha256).digest()

    k = h(h(h(h(("AWS4" + secret_key).encode(), date), region), service), "aws4_request")
    signature = hmac.new(k, to_sign.encode(), hashlib.sha256).hexdigest()
    return f"AWS4-HMAC-SHA256 Credential={access_key}/{scope}, SignedHeaders={signed}, Signature={signature}"


class R2:
    def __init__(self, endpoint, access_key, secret_key, bucket, region="auto", timeout=60):
        u = urllib.parse.urlsplit(endpoint if "://" in endpoint else "https://" + endpoint)
        self.scheme, self.host = u.scheme or "https", u.netloc
        # Tolerate an endpoint that was pasted with the bucket name on the end.
        self.bucket = bucket or u.path.strip("/")
        self.access_key, self.secret_key, self.region, self.timeout = access_key, secret_key, region, timeout
        if not (self.host and self.bucket and access_key and secret_key):
            raise StorageError("File storage isn't fully configured.")

    def _request(self, method, key="", query=None, body=b"", headers=None):
        query, headers = query or {}, headers or {}
        path = "/" + _q(self.bucket) + ("/" + _q(key, safe="-_.~/") if key else "")
        payload_hash = hashlib.sha256(body).hexdigest() if body else EMPTY_SHA
        amz_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        auth = sign(method, self.host, path, query, headers, payload_hash, self.access_key, self.secret_key,
                    self.region, amz_date)
        url = f"{self.scheme}://{self.host}{path}"
        if query:
            url += "?" + "&".join(f"{_q(k)}={_q(v)}" for k, v in sorted(query.items()))
        req = urllib.request.Request(url, data=body or None, method=method, headers={
            **headers, "Authorization": auth, "x-amz-date": amz_date, "x-amz-content-sha256": payload_hash})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            code = (detail.split("<Code>")[1].split("</Code>")[0] if "<Code>" in detail else "")
            raise StorageError(f"Storage returned {e.code} {code}".strip())
        except Exception as e:
            raise StorageError(f"Couldn't reach file storage: {e}")

    def put(self, key, data, content_type="application/octet-stream"):
        self._request("PUT", key, body=data, headers={"Content-Type": content_type})

    def get(self, key):
        return self._request("GET", key)

    def delete(self, key):
        self._request("DELETE", key)

    def list(self, prefix=""):
        """Return [(key, size, last_modified_iso)] for every object under prefix."""
        out, token = [], None
        while True:
            q = {"list-type": "2", "prefix": prefix}
            if token:
                q["continuation-token"] = token
            root = ET.fromstring(self._request("GET", query=q))
            ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
            for c in root.findall(f"{ns}Contents"):
                out.append((c.findtext(f"{ns}Key"), int(c.findtext(f"{ns}Size") or 0), c.findtext(f"{ns}LastModified")))
            if (root.findtext(f"{ns}IsTruncated") or "").lower() != "true":
                return out
            token = root.findtext(f"{ns}NextContinuationToken")
