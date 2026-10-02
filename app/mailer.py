"""Transactional email through Resend (plain HTTPS, no SDK).

Design rules:
  * Email never breaks a page. Sending happens on a background thread and every
    failure is logged, not raised.
  * Without RESEND_API_KEY the site behaves exactly as before (messages are logged
    as skipped), so local development and tests need no account.
  * In tests, messages are collected in app.extensions["outbox"] instead of sent.
"""
import html as _html
import json
import threading
import urllib.error
import urllib.request

from flask import current_app

API = "https://api.resend.com/emails"


def enabled():
    return bool(current_app.config.get("RESEND_API_KEY"))


def _post(api_key, payload, logger):
    req = urllib.request.Request(API, data=json.dumps(payload).encode(), method="POST", headers={
        "Authorization": "Bearer " + api_key, "Content-Type": "application/json",
        "User-Agent": "valueraq-mailer/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
        logger.info("email sent: %s -> %s", payload["subject"], ", ".join(payload["to"]))
        return True
    except urllib.error.HTTPError as e:
        logger.error("email failed (%s): %s | %s", e.code, payload["subject"], e.read()[:300].decode("utf-8", "replace"))
    except Exception as e:  # network errors, timeouts
        logger.error("email failed: %s | %s", payload["subject"], e)
    return False


def _wrap(body_html, can_reply=False):
    brand = current_app.config["BRAND"]
    site = current_app.config["SITE_URL"]
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:16px;line-height:1.5;color:#12201c;'
        'max-width:560px;margin:0 auto;padding:24px">'
        f'<p style="font-weight:700;letter-spacing:.06em;color:#0d6a54;margin:0 0 16px">{brand}</p>'
        f'{body_html}'
        '<hr style="border:0;border-top:1px solid #dfe6e3;margin:24px 0">'
        f'<p style="font-size:13px;color:#5b6b66;margin:0">This is an automatic message from '
        f'<a href="{site}" style="color:#0d6a54">{site.replace("https://", "")}</a>. '        + ('' if can_reply else 'Please don\'t reply to this address.') + '</p></div>')


def send(to, subject, text, html=None, reply_to=None):
    """Queue one email. `to` is an address or a list. Returns True if queued."""
    app = current_app._get_current_object()
    recipients = [a.strip() for a in ([to] if isinstance(to, str) else to) if a and "@" in a]
    if not recipients:
        return False
    payload = {"from": app.config["EMAIL_FROM"], "to": recipients, "subject": subject, "text": text,
               "html": _wrap(html or "".join(f"<p>{_html.escape(p)}</p>" for p in text.split("\n\n")),
                             can_reply=bool(reply_to))}
    if reply_to:
        payload["reply_to"] = reply_to
    if app.config.get("TESTING"):
        app.extensions.setdefault("outbox", []).append(payload)
        return True
    if not enabled():
        app.logger.info("email skipped (RESEND_API_KEY not set): %s -> %s", subject, ", ".join(recipients))
        return False
    threading.Thread(target=_post, args=(app.config["RESEND_API_KEY"], payload, app.logger), daemon=True).start()
    return True


def _btn(url, label):
    return (f'<p style="margin:20px 0"><a href="{_html.escape(url)}" style="background:#0d6a54;color:#fff;'
            f'text-decoration:none;padding:12px 18px;border-radius:6px;font-weight:700;display:inline-block">'
            f'{_html.escape(label)}</a></p>')


def _admins():
    return current_app.config.get("ADMIN_EMAILS") or []


# ---------------------------------------------------------------- the six messages
def welcome(user):
    c = current_app.config
    site = c["SITE_URL"]
    text = (f"Welcome to {c['BRAND']}.\n\nYour account is ready. You can value a website, SaaS, AI business, app, "
            f"newsletter or ecommerce store, save detailed reports, and browse or list businesses for sale.\n\n"
            f"Start a valuation: {site}/tools/\n\nYour account: {site}/account/")
    html = (f"<p>Welcome to {c['BRAND']}.</p><p>Your account is ready. You can value a website, SaaS, AI business, "
            "app, newsletter or ecommerce store, save detailed reports, and browse or list businesses for sale.</p>"
            + _btn(site + "/tools/", "Start a valuation"))
    return send(user["email"], f"Welcome to {c['BRAND']}", text, html)


def password_reset(user, token):
    c = current_app.config
    url = f"{c['SITE_URL']}/reset-password/{token}/"
    text = (f"We received a request to reset the password for your {c['BRAND']} account.\n\n"
            f"Choose a new password here (the link works once and expires in 1 hour):\n{url}\n\n"
            "If you didn't ask for this, you can ignore this email. Your password stays the same.")
    html = (f"<p>We received a request to reset the password for your {c['BRAND']} account.</p>"
            + _btn(url, "Choose a new password")
            + "<p>The link works once and expires in 1 hour.</p>"
              "<p>If you didn't ask for this, you can ignore this email. Your password stays the same.</p>")
    return send(user["email"], f"Reset your {c['BRAND']} password", text, html)


def inquiry_to_seller(seller_email, listing_title, buyer_email, message):
    c = current_app.config
    url = c["SITE_URL"] + "/account/inquiries/"
    text = (f"A buyer has sent you a message about your listing \"{listing_title}\".\n\n"
            f"From: {buyer_email}\n\n{message}\n\n"
            f"You can reply to this email to answer the buyer directly, or see all inquiries here: {url}")
    html = (f"<p>A buyer has sent you a message about your listing <b>{_html.escape(listing_title)}</b>.</p>"
            f"<p style=\"color:#5b6b66;margin-bottom:4px\">From {_html.escape(buyer_email)}</p>"
            f"<blockquote style=\"margin:0;padding:12px 16px;background:#f2f5f3;border-left:3px solid #0d6a54;"
            f"white-space:pre-wrap\">{_html.escape(message)}</blockquote>"
            "<p>Reply to this email to answer the buyer directly.</p>" + _btn(url, "See all inquiries"))
    return send(seller_email, f"New inquiry about \"{listing_title[:60]}\"", text, html, reply_to=buyer_email)


def listing_decision(seller_email, listing_title, status, note, public_url):
    c = current_app.config
    if status == "published":
        subject = f"Your listing is live on {c['BRAND']}"
        text = (f"Good news: your listing \"{listing_title}\" has passed review and is now live.\n\n"
                f"View it: {public_url}\n\nManage it: {c['SITE_URL']}/account/listings/")
        html = (f"<p>Good news: your listing <b>{_html.escape(listing_title)}</b> has passed review and is now live.</p>"
                + _btn(public_url, "View your listing"))
    else:
        subject = f"Your {c['BRAND']} listing needs changes"
        reason = f"\n\nReviewer note: {note}" if note else ""
        text = (f"Your listing \"{listing_title}\" was not approved in its current form.{reason}\n\n"
                f"Edit it and it will be reviewed again: {c['SITE_URL']}/account/listings/")
        html = (f"<p>Your listing <b>{_html.escape(listing_title)}</b> was not approved in its current form.</p>"
                + (f"<p><b>Reviewer note:</b> {_html.escape(note)}</p>" if note else "")
                + "<p>Edit it and it will be reviewed again.</p>"
                + _btn(c["SITE_URL"] + "/account/listings/", "Edit your listing"))
    return send(seller_email, subject, text, html)


def admin_new_listing(listing_title, category, seller_email):
    c = current_app.config
    url = c["SITE_URL"] + "/admin/listings/?status=pending"
    text = (f"A listing is waiting for review.\n\nTitle: {listing_title}\nCategory: {category}\n"
            f"Seller: {seller_email}\n\nReview it: {url}")
    html = (f"<p>A listing is waiting for review.</p><p><b>{_html.escape(listing_title)}</b><br>"
            f"Category: {_html.escape(category)}<br>Seller: {_html.escape(seller_email)}</p>"
            + _btn(url, "Review listings"))
    return send(_admins(), f"New listing to review: {listing_title[:60]}", text, html)


def admin_contact_message(name, email, topic, message):
    c = current_app.config
    url = c["SITE_URL"] + "/admin/messages/"
    text = (f"New message from the contact form.\n\nFrom: {name or 'No name'} <{email}>\nTopic: {topic or '-'}\n\n"
            f"{message}\n\nReply to this email to answer them. All messages: {url}")
    html = (f"<p>New message from the contact form.</p><p style=\"color:#5b6b66;margin-bottom:4px\">"
            f"From {_html.escape(name or 'No name')} &lt;{_html.escape(email)}&gt; · Topic: {_html.escape(topic or '-')}</p>"
            f"<blockquote style=\"margin:0;padding:12px 16px;background:#f2f5f3;border-left:3px solid #0d6a54;"
            f"white-space:pre-wrap\">{_html.escape(message)}</blockquote>"
            "<p>Reply to this email to answer them.</p>" + _btn(url, "All messages"))
    return send(_admins(), f"Contact form: {(topic or 'new message')[:60]}", text, html, reply_to=email)


# ---------------------------------------------------------------- marketplace notifications
def watch_alert(to, listing_title, kind, listing_path, old_price=None, new_price=None, currency="USD"):
    c = current_app.config
    url = c["SITE_URL"] + listing_path
    manage = c["SITE_URL"] + "/account/watchlist/"
    title = _html.escape(listing_title)
    if kind == "sold":
        subject = f"Sold: {listing_title[:60]}"
        text = (f"A listing on your watchlist has been sold: \"{listing_title}\".\n\n{url}\n\n"
                f"Manage your watchlist: {manage}")
        html = f"<p>A listing on your watchlist has been <b>sold</b>: {title}.</p>" + _btn(manage, "Open your watchlist")
    else:
        from .filters import money
        old, new = money(old_price, currency), money(new_price, currency)
        subject = f"Price reduced: {listing_title[:55]}"
        text = (f"The asking price of a listing on your watchlist has dropped.\n\n\"{listing_title}\"\n"
                f"Was {old}, now {new}.\n\n{url}\n\nManage your watchlist: {manage}")
        html = (f"<p>The asking price of a listing on your watchlist has dropped.</p><p><b>{title}</b><br>"
                f"Was {old}, now <b>{new}</b>.</p>" + _btn(url, "View the listing"))
    return send(to, subject, text, html)


def message_notification(to, listing_title, from_role, body, inquiry_id):
    c = current_app.config
    url = f"{c['SITE_URL']}/account/inquiries/{inquiry_id}/"
    text = (f"You have a new message from {from_role} about \"{listing_title}\".\n\n{body}\n\n"
            f"Reply on {c['BRAND']}: {url}")
    html = (f"<p>You have a new message from {from_role} about <b>{_html.escape(listing_title)}</b>.</p>"
            f"<blockquote style=\"margin:0;padding:12px 16px;background:#f2f5f3;border-left:3px solid #0d6a54;"
            f"white-space:pre-wrap\">{_html.escape(body)}</blockquote>" + _btn(url, "Reply"))
    return send(to, f"New message about \"{listing_title[:55]}\"", text, html)


def admin_verification_request(listing_title, kind, seller_email, note):
    c = current_app.config
    url = c["SITE_URL"] + "/admin/listings/?status=published&verification=requested"
    text = (f"A seller has asked for verification.\n\nListing: {listing_title}\nRequested: {kind}\n"
            f"Seller: {seller_email}\n\nEvidence they can share:\n{note}\n\nReview: {url}")
    html = (f"<p>A seller has asked for verification.</p><p><b>{_html.escape(listing_title)}</b><br>"
            f"Requested: {_html.escape(kind)}<br>Seller: {_html.escape(seller_email)}</p>"
            f"<blockquote style=\"margin:0;padding:12px 16px;background:#f2f5f3;border-left:3px solid #0d6a54;"
            f"white-space:pre-wrap\">{_html.escape(note)}</blockquote>"
            "<p>Reply to this email to arrange the evidence check with the seller.</p>" + _btn(url, "Review requests"))
    return send(_admins(), f"Verification request: {listing_title[:55]}", text, html, reply_to=seller_email)


def verification_decision(seller_email, listing_title, label, granted, note, public_url):
    c = current_app.config
    if granted:
        subject = f"Your listing is now {label.lower()}"
        text = (f"Your listing \"{listing_title}\" now shows the \"{label}\" badge.\n\n{public_url}\n\n"
                f"What the badge means: {c['SITE_URL']}/verification/")
        html = (f"<p>Your listing <b>{_html.escape(listing_title)}</b> now shows the "
                f"<b>{_html.escape(label)}</b> badge.</p>" + _btn(public_url, "View your listing"))
    else:
        subject = "Your verification request"
        why = f"\n\nReviewer note: {note}" if note else ""
        text = (f"We couldn't verify your listing \"{listing_title}\" this time.{why}\n\n"
                f"You can request verification again from My listings: {c['SITE_URL']}/account/listings/")
        html = (f"<p>We couldn't verify your listing <b>{_html.escape(listing_title)}</b> this time.</p>"
                + (f"<p><b>Reviewer note:</b> {_html.escape(note)}</p>" if note else "")
                + _btn(c["SITE_URL"] + "/account/listings/", "Open My listings"))
    return send(seller_email, subject, text, html)


def search_alert(to, search_label, listing_title, listing_path, price_text):
    c = current_app.config
    url = c["SITE_URL"] + listing_path
    manage = c["SITE_URL"] + "/account/watchlist/"
    text = (f"A new listing matches your saved search \"{search_label}\".\n\n{listing_title}\n{price_text}\n\n{url}\n\n"
            f"Manage or delete your saved searches: {manage}")
    html = (f"<p>A new listing matches your saved search <b>{_html.escape(search_label)}</b>.</p>"
            f"<p><b>{_html.escape(listing_title)}</b><br>{_html.escape(price_text)}</p>" + _btn(url, "View the listing")
            + f'<p style="font-size:13px;color:#5b6b66">Manage or delete your saved searches in your '
              f'<a href="{manage}" style="color:#0d6a54">watchlist</a>.</p>')
    return send(to, f"New listing: {listing_title[:60]}", text, html)


def admin_error_alert(error_type, message, method, path, count):
    c = current_app.config
    url = c["SITE_URL"] + "/admin/errors/"
    text = (f"The website hit a server error.\n\nType: {error_type}\nMessage: {message}\nRequest: {method} {path}\n"
            f"Times seen: {count}\n\nDetails: {url}\n\nVisitors saw the standard error page. You'll get at most one "
            "email a day about this particular problem.")
    html = (f"<p>The website hit a server error.</p><p><b>{_html.escape(error_type)}</b>: {_html.escape(message)}<br>"
            f"Request: {_html.escape(method)} {_html.escape(path)}<br>Times seen: {count}</p>"
            "<p>Visitors saw the standard error page. You'll get at most one email a day about this particular problem.</p>"
            + _btn(url, "See error details"))
    return send(_admins(), f"Website error: {error_type}", text, html)


def login_code(to, code, purpose="login"):
    minutes = current_app.config["LOGIN_CODE_MINUTES"]
    what = "finish logging in" if purpose == "login" else "turn on two-step login"
    text = (f"Your {current_app.config['BRAND']} code is {code}\n\nEnter it to {what}. It works for {minutes} minutes.\n\n"
            "If you didn't ask for this, someone may know your password: change it in Account > Settings.")
    html = (f"<p>Enter this code to {what}:</p>"
            f'<p style="font:700 28px/1.2 monospace;letter-spacing:4px;margin:16px 0">{_html.escape(code)}</p>'
            f"<p>It works for {minutes} minutes. If you didn't ask for this, someone may know your password: "
            "change it in Account &gt; Settings.</p>")
    return send(to, f"Your {current_app.config['BRAND']} login code", text, html)  # the code stays out of the subject, which is logged
