"""Optional AI commentary for saved reports (premium). Clearly labelled as
AI-generated in the UI. Uses the Anthropic Messages API over plain HTTPS; the key
never reaches the browser. If no key is configured the feature is hidden."""
import json
import urllib.request

from flask import current_app

PROMPT = """You are writing a short, cautious commentary on a small digital business valuation.
The valuation below was calculated by a transparent formula; do not change its numbers.
Write 3 short paragraphs (under 180 words total) for the business owner:
1. What drives the estimate most (use the adjustments listed).
2. The two biggest risks a buyer will probe, and what evidence would reduce them.
3. One practical step to improve value before a sale.
Rules: no new statistics, no market data, no promises, no invented facts. Plain English.

Valuation data (JSON):
{data}"""


def enabled():
    return bool(current_app.config.get("ANTHROPIC_API_KEY"))


def commentary(result):
    if not enabled():
        return None
    data = {k: result[k] for k in ("type_label", "method", "metric", "multiple", "value", "adjustments",
                                   "confidence", "warnings")}
    body = json.dumps({
        "model": current_app.config["ANTHROPIC_MODEL"],
        "max_tokens": 400,
        "messages": [{"role": "user", "content": PROMPT.format(data=json.dumps(data, default=str))}],
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, method="POST", headers={
        "x-api-key": current_app.config["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            out = json.loads(r.read())
        return "".join(b.get("text", "") for b in out.get("content", [])).strip() or None
    except Exception:
        return None
