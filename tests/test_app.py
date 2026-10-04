"""End-to-end tests for VALUERAQ, including the §81 pre-launch SEO acceptance checks.

Run:  python -m unittest discover -s tests -v
"""
import hashlib
import hmac
import io
import json
import os
import re
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import audit, create_app, db, marketplace as M, schema, valuation as V  # noqa: E402
from app.config import TestConfig  # noqa: E402

SITE = TestConfig.SITE_URL
LONG_DESC = (
    "This business is a subscription scheduling tool for independent dental clinics in the United States. "
    "Clinics use it to manage appointments, send reminders by text message and email, and reduce missed visits. "
    "Customers pay monthly on one of three plans, and most have been subscribed for more than a year. "
    "Revenue comes entirely from subscriptions, with no setup fees. The product is built on a mainstream web "
    "framework and hosted on a managed cloud platform, with automated backups and monitoring in place. "
    "The founder handles product decisions and sales calls, while a part-time contractor answers support tickets "
    "within one business day. New customers mostly arrive through referrals from existing clinics and through "
    "a small number of partnerships with dental supply companies. The sale includes the code, domain, customer "
    "accounts, documentation and a thirty day handover period with the founder."
)


def meta(html, name):
    m = re.search(r'<meta name="%s" content="([^"]*)"' % name, html)
    return m.group(1) if m else None


def canonical(html):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    return m.group(1) if m else None


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.app = create_app(TestConfig, DATABASE_PATH=os.path.join(self.tmp, "t.db"))
        self.client = self.app.test_client()

    def csrf(self):
        with self.client.session_transaction() as s:
            s.setdefault("csrf", "tok")
            return s["csrf"]

    def signup(self, email="user@example.com", password="correct-horse-1"):
        tok = self.csrf()
        r = self.client.post("/signup/", data=dict(email=email, password=password, agree="1", csrf=tok))
        self.assertEqual(r.status_code, 302, r.data[:300])
        return email

    def logout(self):
        self.client.post("/logout/", data=dict(csrf=self.csrf()))

    def make_listing(self, category="saas", title="Profitable scheduling SaaS for dental clinics",
                     desc=LONG_DESC, publish=True, **kw):
        with self.app.app_context():
            u = db.query("SELECT id FROM users LIMIT 1", one=True)
            uid = u["id"] if u else None
            if uid is None:
                from app import auth
                uid = auth.create_user("seller@example.com", "seller-pass-123")
            t = db.now()
            fields = dict(seller_id=uid, category=category, slug=M.slugify(title), title=title,
                          headline="B2B SaaS with steady recurring revenue", description=desc,
                          business_model="B2B SaaS", asking_price=kw.get("asking_price", 480000),
                          monthly_revenue=kw.get("monthly_revenue", 20000), monthly_profit=kw.get("monthly_profit", 12000),
                          age_years=kw.get("age_years", 4), status="pending", created_at=t, updated_at=t)
            cols = ", ".join(fields)
            lid = db.execute(f"INSERT INTO listings({cols}) VALUES ({', '.join('?' for _ in fields)})",
                             tuple(fields.values()))
            M.refresh(lid)
            if publish:
                M.set_status(lid, "published", by="test")
            return db.query("SELECT * FROM listings WHERE id=?", (lid,), one=True)


# ---------------------------------------------------------------- valuation engine
class ValuationEngine(unittest.TestCase):
    def test_examples_produce_ordered_ranges(self):
        for tool, ex in V.EXAMPLES.items():
            r = V.value_business(tool, V.parse_inputs(tool, {k: str(v) for k, v in ex.items()}))
            self.assertLess(r["value"]["low"], r["value"]["mid"])
            self.assertLess(r["value"]["mid"], r["value"]["high"])
            self.assertEqual(r["base_multiple"]["origin"], "platform assumption")

    def test_profit_method_math(self):
        r = V.value_business("website", {"monthly_revenue": 1000, "monthly_profit": 1000})
        self.assertEqual(r["metric"]["value"], 12000)
        self.assertEqual(r["value"]["mid"], V.round_money(12000 * V.BASE["website"]["mid"]))

    def test_adjustments_multiply_and_cap(self):
        x = {"mrr": 10000, "growth_pct": -50, "monthly_churn": 20, "gross_margin": 20, "top_customer_pct": 60,
             "age_years": 0.2, "owner_hours": 60, "model_dependency": "single"}
        r = V.value_business("ai", x)
        self.assertEqual(r["adjustment_factor"], V.ADJ_FLOOR)
        self.assertTrue(any("capped" in w for w in r["warnings"]))

    def test_loss_making_rejected_for_profit_method(self):
        with self.assertRaises(V.ValuationError):
            V.value_business("website", {"monthly_revenue": 1000, "monthly_profit": -50})

    def test_profit_above_revenue_rejected(self):
        with self.assertRaises(V.ValuationError):
            V.value_business("app", {"monthly_revenue": 1000, "monthly_profit": 5000})

    def test_required_fields(self):
        with self.assertRaises(V.ValuationError) as cm:
            V.parse_inputs("saas", {})
        self.assertIn("mrr", cm.exception.fields)

    def test_inventory_added_for_ecommerce(self):
        r = V.value_business("ecommerce", {"monthly_revenue": 10000, "monthly_profit": 2000, "inventory_value": 5000})
        self.assertEqual(r["value_including_extras"]["mid"], r["value"]["mid"] + 5000)

    def test_business_multiple(self):
        r = V.business_multiple(300000, 120000, 90000, "website")
        self.assertEqual(r["revenue_multiple"], 2.5)
        self.assertEqual(r["profit_multiple"], 3.33)
        self.assertEqual(r["reference"]["position"], "within")

    def test_rules_table_matches_engine(self):
        factors = {r["factor"] for r in V.rules_table()}
        for tool, ex in V.EXAMPLES.items():
            for a in V.value_business(tool, ex)["adjustments"]:
                self.assertIn(a["factor"], factors)


# ---------------------------------------------------------------- technical SEO
class TechnicalSEO(Base):
    def test_every_sitemap_url_is_indexable_self_canonical_200(self):
        idx = self.client.get("/sitemap.xml").get_data(as_text=True)
        children = re.findall(r"<loc>([^<]+)</loc>", idx)
        self.assertTrue(children)
        seen_titles = {}
        for child in children:
            body = self.client.get(child.replace(SITE, "")).get_data(as_text=True)
            for loc in re.findall(r"<loc>([^<]+)</loc>", body):
                path = loc.replace(SITE, "")
                r = self.client.get(path)
                self.assertEqual(r.status_code, 200, path)
                html = r.get_data(as_text=True)
                self.assertNotIn("noindex", meta(html, "robots") or "", path)
                self.assertEqual(canonical(html), loc, path)
                self.assertEqual(html.count("<h1"), 1, path)
                title = re.search(r"<title>([^<]+)</title>", html).group(1)
                self.assertNotIn(title, seen_titles, f"duplicate title on {path} and {seen_titles.get(title)}")
                seen_titles[title] = path
                self.assertTrue(meta(html, "description"), path)

    def test_robots_txt(self):
        txt = self.client.get("/robots.txt").get_data(as_text=True)
        for p in ("/admin/", "/account/", "/api/", "/checkout/", "/reports/private/"):
            self.assertIn(f"Disallow: {p}", txt)
        for p in ("/tools/", "/guides/", "/marketplace/", "/businesses-for-sale/", "/static/"):
            self.assertNotIn(f"Disallow: {p}\n", txt)
        self.assertNotIn("Disallow: /\n", txt)
        self.assertIn(f"Sitemap: {SITE}/sitemap.xml", txt)

    def test_trailing_slash_and_case_redirects_are_301(self):
        r = self.client.get("/tools")
        self.assertEqual(r.status_code, 301)
        r = self.client.get("/Guides/")
        self.assertEqual(r.status_code, 301)
        self.assertTrue(r.headers["Location"].endswith("/guides/"))

    def test_canonical_host_redirect(self):
        app = create_app(TestConfig, DATABASE_PATH=os.path.join(self.tmp, "h.db"), ENFORCE_CANONICAL_HOST=True)
        c = app.test_client()
        r = c.get("/tools/", base_url="https://valueraq.com")
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r.headers["Location"], "https://www.valueraq.com/tools/")
        r = c.get("/tools/?x=1", base_url="http://www.valueraq.com")
        self.assertEqual(r.headers["Location"], "https://www.valueraq.com/tools/?x=1")

    def test_404_status_and_noindex(self):
        r = self.client.get("/no-such-page/")
        self.assertEqual(r.status_code, 404)
        self.assertIn("noindex", r.headers.get("X-Robots-Tag", ""))

    def test_structured_data_valid_everywhere(self):
        for path in ("/", "/tools/", "/tools/saas-valuation/", "/calculators/website-worth-calculator/",
                     "/guides/website-valuation/", "/glossary/", "/glossary/arr/", "/faq/", "/about/",
                     "/businesses-for-sale/saas/", "/methodology/"):
            html = self.client.get(path).get_data(as_text=True)
            blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
            self.assertTrue(blocks, path)
            for b in blocks:
                types, errors = schema.validate(json.loads(b))
                self.assertEqual(errors, [], path)
                self.assertNotIn("AggregateRating", types)
                self.assertNotIn("Review", types)

    def test_private_paths_send_noindex_header(self):
        for path in ("/account/", "/admin/", "/api/events/"):
            r = self.client.get(path)
            self.assertIn("noindex", r.headers.get("X-Robots-Tag", ""), path)

    def test_security_headers(self):
        r = self.client.get("/")
        self.assertIn("default-src 'self'", r.headers["Content-Security-Policy"])
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")

    def test_public_pages_cacheable_private_not(self):
        self.assertIn("s-maxage", self.client.get("/guides/").headers["Cache-Control"])
        self.assertIn("no-store", self.client.get("/login/").headers["Cache-Control"])

    def test_critical_content_in_html_without_js(self):
        html = self.client.get("/tools/website-valuation/").get_data(as_text=True)
        self.assertIn("How the valuation is calculated", html)
        self.assertIn("Estimated value of this website", html)   # example result is server-rendered
        self.assertIn("<table", html)

    def test_example_tokens_replaced(self):
        for t in ("website", "saas", "ai", "app", "newsletter", "ecommerce"):
            path = [x for x in __import__("app.catalog").catalog.TOOLS if x["key"] == t][0]["path"]
            self.assertNotIn("[[ex:", self.client.get(path).get_data(as_text=True), path)


# ---------------------------------------------------------------- facets, pagination, search
class FacetsAndPagination(Base):
    def test_filter_urls_noindex_with_clean_canonical(self):
        html = self.client.get("/businesses-for-sale/saas/?sort=price_asc&price_max=100000").get_data(as_text=True)
        self.assertIn("noindex", meta(html, "robots"))
        self.assertEqual(canonical(html), SITE + "/businesses-for-sale/saas/")

    def test_tracking_params_noindex(self):
        html = self.client.get("/guides/website-valuation/?utm_source=x").get_data(as_text=True)
        self.assertIn("noindex", meta(html, "robots"))
        self.assertEqual(canonical(html), SITE + "/guides/website-valuation/")

    def test_pagination_bounds(self):
        self.assertEqual(self.client.get("/businesses-for-sale/saas/page/2/").status_code, 404)
        r = self.client.get("/businesses-for-sale/saas/page/1/")
        self.assertEqual(r.status_code, 301)
        self.app.config["LISTINGS_PER_PAGE"] = 1
        self.make_listing(title="Profitable scheduling SaaS for dental clinics")
        self.make_listing(title="Invoice reminder SaaS for freelance designers", desc=LONG_DESC.replace("dental", "design").replace("scheduling", "invoicing") + " Different words entirely for uniqueness: " + " ".join(f"word{i}" for i in range(200)))
        r = self.client.get("/businesses-for-sale/saas/page/2/")
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertEqual(canonical(html), SITE + "/businesses-for-sale/saas/page/2/")
        self.assertIn("index, follow", meta(html, "robots"))
        self.assertEqual(self.client.get("/businesses-for-sale/saas/page/3/").status_code, 404)
        sm = self.client.get("/sitemap-categories.xml").get_data(as_text=True)
        self.assertIn("/businesses-for-sale/saas/page/2/", sm)

    def test_search_noindex(self):
        html = self.client.get("/search/?q=churn").get_data(as_text=True)
        self.assertIn("noindex", meta(html, "robots"))
        self.assertIn("/glossary/churn/", html)

    def test_empty_blog_not_indexed_or_in_sitemap(self):
        html = self.client.get("/blog/").get_data(as_text=True)
        self.assertIn("noindex", meta(html, "robots"))
        self.assertNotIn("sitemap-blog", self.client.get("/sitemap.xml").get_data(as_text=True))


# ---------------------------------------------------------------- marketplace indexation
class MarketplaceIndexation(Base):
    def test_quality_listing_indexable_and_in_sitemap(self):
        l = self.make_listing()
        self.assertEqual(l["indexable"], 1, l["quality_flags"])
        path = M.listing_path(l)
        html = self.client.get(path).get_data(as_text=True)
        self.assertIn("index, follow", meta(html, "robots"))
        self.assertEqual(canonical(html), SITE + path)
        self.assertIn(path, self.client.get("/sitemap-listings.xml").get_data(as_text=True))
        self.assertIn("Asking price", html)
        self.assertIn('"@type": "Product"', html.replace('"@type":"Product"', '"@type": "Product"'))

    def test_thin_listing_noindex_not_in_sitemap(self):
        l = self.make_listing(title="Tiny SaaS for sale here", desc="Short description of a small SaaS tool. " * 3)
        self.assertEqual(l["indexable"], 0)
        html = self.client.get(M.listing_path(l)).get_data(as_text=True)
        self.assertIn("noindex", meta(html, "robots"))
        self.assertNotIn(M.listing_path(l), self.client.get("/sitemap-listings.xml").get_data(as_text=True))

    def test_pending_listing_hidden(self):
        l = self.make_listing(publish=False)
        self.assertEqual(self.client.get(M.listing_path(l)).status_code, 404)

    def test_wrong_slug_redirects_to_canonical(self):
        l = self.make_listing()
        r = self.client.get(f"/marketplace/saas/some-old-name-{l['id']}/")
        self.assertEqual(r.status_code, 301)
        self.assertTrue(r.headers["Location"].endswith(M.listing_path(l)))

    def test_removed_without_replacement_is_410(self):
        l = self.make_listing()
        with self.app.app_context():
            M.set_status(l["id"], "removed", by="test")
        r = self.client.get(M.listing_path(l))
        self.assertEqual(r.status_code, 410)
        self.assertNotIn(M.listing_path(l), self.client.get("/sitemap-listings.xml").get_data(as_text=True))

    def test_removed_with_replacement_is_301_no_chain(self):
        a = self.make_listing(title="Scheduling SaaS for dental clinics A")
        b = self.make_listing(title="Scheduling SaaS for dental clinics B",
                              desc=LONG_DESC + " " + " ".join(f"extra{i}" for i in range(300)))
        with self.app.app_context():
            M.set_status(a["id"], "removed", by="test", replacement_id=b["id"])
        r = self.client.get(M.listing_path(a))
        self.assertEqual(r.status_code, 301)
        self.assertTrue(r.headers["Location"].endswith(M.listing_path(b)))
        # b's title changes → a must point straight at b's new URL (no chain).
        with self.app.app_context():
            M.change_slug(b["id"], "Renamed dental scheduling SaaS")
            from app import redirects
            self.assertEqual(len(redirects.chains()), 0)
            newb = db.query("SELECT * FROM listings WHERE id=?", (b["id"],), one=True)
        r = self.client.get(M.listing_path(a))
        self.assertTrue(r.headers["Location"].endswith(M.listing_path(newb)))

    def test_sold_listing_noindex_with_notice(self):
        l = self.make_listing()
        with self.app.app_context():
            M.set_status(l["id"], "sold", by="test")
        r = self.client.get(M.listing_path(l))
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertIn("noindex", meta(html, "robots"))
        self.assertIn("has been sold", html)

    def test_duplicate_detection(self):
        self.make_listing()
        dup = self.make_listing(title="Copy of the dental scheduling SaaS")
        self.assertEqual(dup["indexable"], 0)
        self.assertIn("similar", dup["quality_flags"])

    def test_spam_and_contact_details(self):
        spam = LONG_DESC + " Guaranteed income! WhatsApp me at +1 555 123 4567 or mail me@spam.com http://a.io http://b.io http://c.io"
        l = self.make_listing(title="Spammy listing that should fail", desc=spam)
        self.assertEqual(l["indexable"], 0)
        html = self.client.get(M.listing_path(l)).get_data(as_text=True)
        self.assertNotIn("me@spam.com", html)
        self.assertNotIn("555 123 4567", html)

    def test_listing_description_from_data(self):
        l = self.make_listing()
        html = self.client.get(M.listing_path(l)).get_data(as_text=True)
        d = meta(html, "description")
        self.assertIn("$480,000", d)
        self.assertLessEqual(len(d), 160)

    def test_no_fabricated_listings_on_fresh_install(self):
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) n FROM listings", one=True)["n"], 0)
        self.assertIn("No SaaS businesses are listed for sale right now",
                      self.client.get("/businesses-for-sale/saas/").get_data(as_text=True))


# ---------------------------------------------------------------- accounts, reports, selling
class AccountsAndReports(Base):
    def test_csrf_required(self):
        r = self.client.post("/signup/", data=dict(email="a@b.co", password="x" * 12, agree="1"))
        self.assertEqual(r.status_code, 400)

    def test_signup_login_logout(self):
        self.signup()
        self.assertEqual(self.client.get("/account/").status_code, 200)
        self.logout()
        self.assertEqual(self.client.get("/account/").status_code, 302)
        tok = self.csrf()
        r = self.client.post("/login/", data=dict(email="user@example.com", password="correct-horse-1", csrf=tok))
        self.assertEqual(r.status_code, 302)

    def test_valuation_to_private_report_flow(self):
        r = self.client.post("/tools/result/website/", data=dict(monthly_revenue="6000", monthly_profit="4500"),
                             headers={"Accept": "application/json"})
        self.assertTrue(r.json["ok"])
        self.signup()
        r = self.client.get("/account/reports/new/")
        self.assertEqual(r.status_code, 302)
        loc = r.headers["Location"]
        self.assertIn("/reports/private/", loc)
        rep = self.client.get(loc)
        self.assertEqual(rep.status_code, 200)
        self.assertIn("noindex", rep.headers["X-Robots-Tag"])
        self.assertIn("Sensitivity", rep.get_data(as_text=True))
        # another user cannot see it
        self.logout()
        self.signup("other@example.com")
        self.assertEqual(self.client.get(loc).status_code, 404)

    def test_no_js_result_page(self):
        r = self.client.post("/tools/result/saas/", data=dict(mrr="5000"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("noindex", r.headers.get("X-Robots-Tag", ""))
        r = self.client.post("/tools/result/saas/", data=dict(mrr=""))
        self.assertEqual(r.status_code, 422)

    def test_free_report_limit_and_trial(self):
        self.signup()
        for _ in range(3):
            self.client.post("/tools/result/website/", data=dict(monthly_revenue="100", monthly_profit="50"),
                             headers={"Accept": "application/json"})
            self.client.get("/account/reports/new/")
        self.client.post("/tools/result/website/", data=dict(monthly_revenue="100", monthly_profit="50"),
                         headers={"Accept": "application/json"})
        r = self.client.get("/account/reports/new/")
        self.assertTrue(r.headers["Location"].endswith("/account/reports/"))
        self.client.post("/account/trial/", data=dict(csrf=self.csrf()))
        with self.app.app_context():
            u = db.query("SELECT * FROM users WHERE email='user@example.com'", one=True)
            self.assertEqual(u["plan"], "trial")
            self.assertGreater(u["trial_ends_at"], time.time() + 13 * 86400)
        r = self.client.get("/account/reports/new/")
        self.assertIn("/reports/private/", r.headers["Location"])
        # a second trial is refused
        self.client.post("/account/trial/", data=dict(csrf=self.csrf()))
        with self.app.app_context():
            self.assertEqual(db.query("SELECT trial_used FROM users WHERE email='user@example.com'", one=True)[0], 1)

    def test_sell_flow_creates_pending_listing(self):
        self.signup()
        data = dict(csrf=self.csrf(), category="saas", title="Scheduling SaaS for dental clinics",
                    headline="Steady B2B SaaS", description=LONG_DESC, business_model="B2B SaaS",
                    asking_price="480000", monthly_revenue="20000", monthly_profit="12000", age_years="4",
                    confirm="1")
        r = self.client.post("/sell/", data=data)
        self.assertEqual(r.status_code, 302)
        with self.app.app_context():
            l = db.query("SELECT * FROM listings", one=True)
            self.assertEqual(l["status"], "pending")
            self.assertEqual(l["indexable"], 0)

    def test_inquiry(self):
        l = self.make_listing()
        self.signup("buyer@example.com")
        r = self.client.post(M.listing_path(l) + "inquire/",
                             data=dict(csrf=self.csrf(), message="I'd like to see the MRR history and churn by month."))
        self.assertEqual(r.status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) n FROM inquiries", one=True)["n"], 1)

    def test_open_redirect_blocked(self):
        tok = self.csrf()
        r = self.client.post("/signup/", data=dict(email="x@example.com", password="correct-horse-1", agree="1",
                                                   csrf=tok, next="//evil.com/"))
        self.assertEqual(r.headers["Location"], "/account/")


# ---------------------------------------------------------------- billing
class Billing(Base):
    def test_webhook_signature_and_idempotency(self):
        self.app.config["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
        self.signup()
        with self.app.app_context():
            db.execute("UPDATE users SET stripe_customer_id='cus_1'")
        evt = {"id": "evt_1", "type": "customer.subscription.updated",
               "data": {"object": {"id": "sub_1", "customer": "cus_1", "status": "active", "current_period_end": 1}}}
        payload = json.dumps(evt).encode()
        ts = int(time.time())
        sig = hmac.new(b"whsec_test", f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
        bad = self.client.post("/api/stripe/webhook/", data=payload, headers={"Stripe-Signature": f"t={ts},v1=bad"})
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post("/api/stripe/webhook/", data=payload, headers={"Stripe-Signature": f"t={ts},v1={sig}"})
        self.assertEqual(ok.status_code, 200)
        again = self.client.post("/api/stripe/webhook/", data=payload, headers={"Stripe-Signature": f"t={ts},v1={sig}"})
        self.assertEqual(again.json["result"], "duplicate")
        with self.app.app_context():
            self.assertEqual(db.query("SELECT plan FROM users", one=True)["plan"], "pro")

    def test_checkout_without_keys_is_graceful(self):
        self.signup()
        r = self.client.post("/checkout/pro_monthly/", data=dict(csrf=self.csrf()), follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn("isn", r.get_data(as_text=True))

    def _hook(self, evt):
        payload = json.dumps(evt).encode()
        ts = int(time.time())
        sig = hmac.new(b"whsec_test", f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
        return self.client.post("/api/stripe/webhook/", data=payload, headers={"Stripe-Signature": f"t={ts},v1={sig}"})

    def test_featured_subscription_features_listing_without_touching_plan(self):
        self.app.config["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
        self.signup()
        lst = self.make_listing()
        with self.app.app_context():
            uid = db.query("SELECT id FROM users", one=True)["id"]
            db.execute("UPDATE users SET stripe_customer_id='cus_1'")
        md = {"kind": "featured", "listing_id": str(lst["id"]), "user_id": str(uid), "plan": "featured_yearly"}
        self._hook({"id": "evt_f1", "type": "checkout.session.completed",
                    "data": {"object": {"subscription": "sub_f", "client_reference_id": str(uid), "metadata": md}}})
        end = int(time.time()) + 365 * 86400
        r = self._hook({"id": "evt_f2", "type": "customer.subscription.updated",
                        "data": {"object": {"id": "sub_f", "customer": "cus_1", "status": "active", "metadata": md,
                                            "items": {"data": [{"current_period_end": end}]}}}})
        self.assertEqual(r.json["result"], "featured active")
        with self.app.app_context():
            l = db.query("SELECT * FROM listings WHERE id=?", (lst["id"],), one=True)
            self.assertEqual(l["is_featured"], 1)
            self.assertEqual(l["featured_subscription_id"], "sub_f")
            self.assertGreater(l["featured_until"], end)
            self.assertEqual(db.query("SELECT plan FROM users", one=True)["plan"], "free")
        self._hook({"id": "evt_f3", "type": "customer.subscription.deleted",
                    "data": {"object": {"id": "sub_f", "customer": "cus_1", "status": "canceled", "metadata": md}}})
        with self.app.app_context():
            self.assertEqual(db.query("SELECT is_featured FROM listings WHERE id=?", (lst["id"],), one=True)["is_featured"], 0)

    def test_pricing_shows_monthly_yearly_and_comparison(self):
        html = self.client.get("/pricing/").get_data(as_text=True)
        self.assertIn('data-period="month"', html)
        self.assertIn("$250", html)
        self.assertIn("$350", html)
        self.assertIn("Save 28%", html)
        self.assertIn("Save 25%", html)
        self.assertNotIn("$290", html)
        self.assertNotIn("$390", html)
        self.assertIn('id="compare"', html)
        self.assertNotIn("one-off", html)


class RevenueSources(Base):
    def test_combine_rule(self):
        total, main, summary, errs = V.combine_revenue_sources(["affiliate", "display"], ["4,000", "2000"])
        self.assertEqual((total, main, errs), (6000, "affiliate", {}))
        self.assertIn("Affiliate commissions $4,000", summary)
        _, main, _, _ = V.combine_revenue_sources(["affiliate", "display"], ["3000", "3000"])
        self.assertEqual(main, "mixed")
        _, _, _, errs = V.combine_revenue_sources(["affiliate"], ["abc"])
        self.assertIn("monthly_revenue", errs)

    def test_website_form_posts_rows(self):
        from werkzeug.datastructures import MultiDict
        r = self.client.post("/tools/result/website/", headers={"Accept": "application/json"}, data=MultiDict([
            ("src_type", "display"), ("src_amount", "5000"), ("src_type", "leadgen"), ("src_amount", "1000"),
            ("src_type", ""), ("src_amount", ""), ("monthly_profit", "4000")]))
        self.assertTrue(r.json["ok"], r.json)
        self.assertIn("Value another business", r.json["html"])
        empty = self.client.post("/tools/result/website/", headers={"Accept": "application/json"},
                                 data={"src_type": "", "src_amount": "", "monthly_profit": "4000"})
        self.assertIn("monthly_revenue", empty.json["fields"])

    def test_tool_page_has_grey_examples_and_clear(self):
        html = self.client.get("/tools/website-valuation/").get_data(as_text=True)
        self.assertIn("+ Add revenue source", html)
        self.assertIn('placeholder="e.g. 4,500"', html)
        self.assertIn('type="reset"', html)



class ChangePassword(Base):
    def test_change_password_flow(self):
        self.signup()
        other = self.app.test_client()
        with other.session_transaction() as s:
            s["csrf"] = "tok2"
        other.post("/login/", data=dict(email="user@example.com", password="correct-horse-1", csrf="tok2"))
        self.assertEqual(other.get("/account/settings/").status_code, 200)
        page = self.client.get("/account/settings/").get_data(as_text=True)
        self.assertIn("Change password", page)
        tok = self.csrf()
        bad = self.client.post("/account/settings/", data=dict(csrf=tok, current_password="wrong-one-123",
                                                               new_password="new-password-99", confirm_password="new-password-99"))
        self.assertEqual(bad.status_code, 422)
        self.assertIn("isn&#39;t your current password", bad.get_data(as_text=True))
        mismatch = self.client.post("/account/settings/", data=dict(csrf=tok, current_password="correct-horse-1",
                                                                    new_password="new-password-99", confirm_password="other-password-99"))
        self.assertIn("don&#39;t match", mismatch.get_data(as_text=True))
        ok = self.client.post("/account/settings/", data=dict(csrf=tok, current_password="correct-horse-1",
                                                              new_password="new-password-99", confirm_password="new-password-99"),
                              follow_redirects=True)
        self.assertIn("Your password has been changed", ok.get_data(as_text=True))
        self.assertEqual(self.client.get("/account/settings/").status_code, 200)  # this device stays signed in
        self.assertEqual(other.get("/account/settings/").status_code, 302)       # other device signed out
        self.logout()
        with self.app.app_context():
            from app import auth
            self.assertIsNone(auth.verify("user@example.com", "correct-horse-1"))
            self.assertIsNotNone(auth.verify("user@example.com", "new-password-99"))



class Emails(Base):
    def outbox(self):
        return self.app.extensions.setdefault("outbox", [])

    def test_welcome_inquiry_contact_and_listing_emails(self):
        self.signup("seller@example.com")
        self.assertEqual(self.outbox()[-1]["subject"], "Welcome to VALUERAQ")
        lst = self.make_listing()
        self.logout()
        self.signup("buyer@example.com")
        path = M.listing_path(lst)
        self.client.post(path + "inquire/", data=dict(csrf=self.csrf(), message="I'd like to see the last 12 months of revenue, please."))
        m = self.outbox()[-1]
        self.assertEqual(m["to"], ["seller@example.com"])
        self.assertEqual(m["reply_to"], "buyer@example.com")
        self.assertIn("last 12 months", m["text"])
        self.assertNotIn("don\'t reply", m["html"])
        self.client.post("/contact/", data=dict(csrf=self.csrf(), name="Ann", email="ann@example.com", topic="Help",
                                                message="Please tell me how featured listings work."))
        m = self.outbox()[-1]
        self.assertEqual(m["to"], ["admin@example.com"])
        self.assertEqual(m["reply_to"], "ann@example.com")
        with self.app.app_context():
            from app import mailer
            mailer.listing_decision("seller@example.com", "My SaaS", "rejected", "Add 12 months of revenue.", "https://x/")
        self.assertIn("Add 12 months of revenue.", self.outbox()[-1]["text"])

    def test_email_without_key_never_breaks_the_page(self):
        self.app.config["TESTING"] = False  # real code path, no API key
        try:
            with self.app.test_request_context():
                from app import mailer
                self.assertFalse(mailer.send("a@example.com", "Hi", "Body"))
        finally:
            self.app.config["TESTING"] = True


class ForgotPassword(Base):
    def test_reset_flow(self):
        self.signup()
        self.logout()
        box = self.app.extensions.setdefault("outbox", [])
        self.assertIn("Forgot password?", self.client.get("/login/").get_data(as_text=True))
        # unknown address: same answer, no email
        n = len(box)
        r = self.client.post("/forgot-password/", data=dict(csrf=self.csrf(), email="nobody@example.com"))
        self.assertIn("If that email has an account", r.get_data(as_text=True))
        self.assertEqual(len(box), n)
        r = self.client.post("/forgot-password/", data=dict(csrf=self.csrf(), email="User@Example.com"))
        self.assertIn("If that email has an account", r.get_data(as_text=True))
        link = re.search(r"/reset-password/([0-9a-f]+)/", box[-1]["text"])
        self.assertTrue(link)
        url = link.group(0)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertIn("noindex", self.client.get(url).get_data(as_text=True))
        short = self.client.post(url, data=dict(csrf=self.csrf(), new_password="short", confirm_password="short"))
        self.assertEqual(short.status_code, 422)
        ok = self.client.post(url, data=dict(csrf=self.csrf(), new_password="brand-new-pass-9", confirm_password="brand-new-pass-9"))
        self.assertEqual(ok.status_code, 302)
        self.assertEqual(self.client.get(url).status_code, 410)  # link works once
        with self.app.app_context():
            from app import auth
            self.assertIsNone(auth.verify("user@example.com", "correct-horse-1"))
            self.assertIsNotNone(auth.verify("user@example.com", "brand-new-pass-9"))
            self.assertIsNone(db.query("SELECT 1 FROM password_resets WHERE token_hash=?", (link.group(1),), one=True))

    def test_expired_and_throttled(self):
        self.signup()
        with self.app.app_context():
            from app import auth
            u = db.query("SELECT * FROM users", one=True)
            t = auth.create_reset_token(u)
            db.execute("UPDATE password_resets SET expires_at=?", (db.now() - 1,))
            self.assertIsNone(auth.reset_token_user(t))
            auth.create_reset_token(u), auth.create_reset_token(u)
            self.assertIsNone(auth.create_reset_token(u))  # 3 per hour per account
        self.assertEqual(self.client.get("/reset-password/" + t + "/").status_code, 410)


class FakeStore:
    def __init__(self):
        self.objects = {}

    def put(self, key, data, content_type=None):
        self.objects[key] = data

    def get(self, key):
        return self.objects[key]

    def delete(self, key):
        del self.objects[key]

    def list(self, prefix=""):
        return [(k, len(v), "") for k, v in sorted(self.objects.items()) if k.startswith(prefix)]


class Backups(Base):
    def test_signing_matches_aws_published_examples(self):
        from app.storage import EMPTY_SHA, sign
        ak, sk, d, host = "AKIAIOSFODNN7EXAMPLE", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "20130524T000000Z", "examplebucket.s3.amazonaws.com"
        self.assertTrue(sign("GET", host, "/test.txt", {}, {"Range": "bytes=0-9"}, EMPTY_SHA, ak, sk, "us-east-1", d)
                        .endswith("f0e8bdb87c964420e857bd35b5d6ed310bd44f0170aba48dd91039c6036bdb41"))
        self.assertTrue(sign("GET", host, "/", {"max-keys": "2", "prefix": "J"}, {}, EMPTY_SHA, ak, sk, "us-east-1", d)
                        .endswith("34b48302e7b5fa45bde8084f4b7868a86f0a534bc59db6670ed5711ef69dc6f7"))
        ph = hashlib.sha256(b"Welcome to Amazon S3.").hexdigest()
        self.assertTrue(sign("PUT", host, "/test%24file.text", {}, {"Date": "Fri, 24 May 2013 00:00:00 GMT",
                             "x-amz-storage-class": "REDUCED_REDUNDANCY"}, ph, ak, sk, "us-east-1", d)
                        .endswith("98ad721746da40c64f1a55b78f14c238d841ea1380cd77a1b5971af0ece108bd"))

    def test_backup_restores_to_identical_data_and_prunes(self):
        import gzip
        import sqlite3
        from app import backup
        self.signup()
        self.make_listing()
        store = FakeStore()
        self.app.config["BACKUP_KEEP"] = 2
        with self.app.app_context():
            self.assertTrue(backup.due())
            row = backup.run("manual", store=store)
            self.assertEqual(row["status"], "ok", row)
            self.assertFalse(backup.due())
            restored = os.path.join(self.tmp, "restored.db")
            with open(restored, "wb") as fh:
                fh.write(gzip.decompress(store.objects[row["object_key"]]))
            conn = sqlite3.connect(restored)
            self.assertEqual(conn.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(conn.execute("SELECT email FROM users").fetchone()[0], "user@example.com")
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0], 1)
            store.objects["backups/valueraq-20200101-000000.db.gz"] = b"old"
            store.objects["backups/valueraq-20200102-000000.db.gz"] = b"old"
            backup.prune(store)
            self.assertEqual(len(store.objects), 2)
            self.assertIn(row["object_key"], store.objects)

    def test_failure_is_recorded_not_raised_and_one_worker_claims(self):
        from app import backup

        class Broken(FakeStore):
            def put(self, *a, **k):
                raise RuntimeError("storage down")
        with self.app.app_context():
            row = backup.run("scheduled", store=Broken())
            self.assertEqual(row["status"], "failed")
            self.assertIn("storage down", db.query("SELECT error FROM backups", one=True)["error"])
            self.assertTrue(backup.due())
            self.assertTrue(backup._claim("2026100211"))
            self.assertFalse(backup._claim("2026100211"))
            self.assertIsNone(backup.tick())  # storage not configured in tests

    def test_admin_backups_page_requires_admin(self):
        self.signup()
        self.assertEqual(self.client.get("/admin/backups/").status_code, 404)
        self.logout()
        self.signup("admin@example.com")
        html = self.client.get("/admin/backups/").get_data(as_text=True)
        self.assertIn("Backups are off", html)
        self.assertIn("Send me a test email", html)



class MarketplaceAccountFeatures(Base):
    def setUp(self):
        super().setUp()
        self.signup("seller@example.com")
        self.lst = self.make_listing(asking_price=480000)
        self.path = M.listing_path(self.lst)
        self.logout()
        self.box = self.app.extensions.setdefault("outbox", [])

    def login(self, email, pw="correct-horse-1"):
        return self.client.post("/login/", data=dict(email=email, password=pw, csrf=self.csrf()))

    def test_watchlist_save_remove_and_alerts(self):
        self.assertIn("Save to watchlist", self.client.get(self.path).get_data(as_text=True))
        self.assertEqual(self.client.post(self.path + "save/", data=dict(csrf=self.csrf())).status_code, 302)  # to login
        self.signup("buyer@example.com")
        self.client.post(self.path + "save/", data=dict(csrf=self.csrf()))
        self.assertIn("Saved", self.client.get(self.path).get_data(as_text=True))
        page = self.client.get("/account/watchlist/").get_data(as_text=True)
        self.assertIn(self.lst["title"], page)
        self.assertIn("noindex", page)
        with self.app.app_context():
            from app.views.market_account import notify_watchers
            self.assertEqual(notify_watchers(self.lst["id"]), 0)                 # nothing changed
            db.execute("UPDATE listings SET asking_price=400000 WHERE id=?", (self.lst["id"],))
            self.assertEqual(notify_watchers(self.lst["id"]), 1)
            self.assertIn("Price reduced", self.box[-1]["subject"])
            self.assertIn("$400,000", self.box[-1]["text"])
            self.assertEqual(notify_watchers(self.lst["id"]), 0)                 # not told twice
            M.set_status(self.lst["id"], "sold", by="test")
            self.assertEqual(notify_watchers(self.lst["id"], old_status="published"), 1)
            self.assertTrue(self.box[-1]["subject"].startswith("Sold"))
        self.assertIn("Sold", self.client.get("/account/watchlist/").get_data(as_text=True))
        # the seller can't save their own listing
        self.logout()
        self.login("seller@example.com")
        with self.app.app_context():
            M.set_status(self.lst["id"], "published", by="test")
        self.client.post(self.path + "save/", data=dict(csrf=self.csrf()))
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) n FROM watchlist", one=True)["n"], 1)

    def test_message_thread_unread_and_privacy(self):
        self.signup("buyer@example.com")
        self.client.post(self.path + "inquire/", data=dict(csrf=self.csrf(), message="Could you share the last 12 months of revenue?"))
        with self.app.app_context():
            iid = db.query("SELECT id FROM inquiries", one=True)["id"]
        self.logout()
        self.login("seller@example.com")
        self.assertIn('aria-label="1 unread"', self.client.get("/account/").get_data(as_text=True))
        t = self.client.get(f"/account/inquiries/{iid}/").get_data(as_text=True)
        self.assertIn("last 12 months of revenue", t)
        self.assertNotIn("unread", self.client.get("/account/").get_data(as_text=True))
        self.client.post(f"/account/inquiries/{iid}/", data=dict(csrf=self.csrf(), message="Yes, <b>here</b> it is."))
        self.assertEqual(self.box[-1]["to"], ["buyer@example.com"])
        self.assertIn(f"/account/inquiries/{iid}/", self.box[-1]["text"])
        self.logout()
        self.login("buyer@example.com")
        lst = self.client.get("/account/inquiries/").get_data(as_text=True)
        self.assertIn("1 new", lst)
        self.assertNotIn("seller@example.com", lst)                             # seller's email stays private
        t = self.client.get(f"/account/inquiries/{iid}/").get_data(as_text=True)
        self.assertIn("&lt;b&gt;here&lt;/b&gt;", t)                              # user text is escaped
        self.assertNotIn("seller@example.com", t)
        self.assertNotIn("1 new", self.client.get("/account/inquiries/").get_data(as_text=True))
        # a third person can't open the thread
        self.logout()
        self.signup("other@example.com")
        self.assertEqual(self.client.get(f"/account/inquiries/{iid}/").status_code, 404)
        self.assertEqual(self.client.post(f"/account/inquiries/{iid}/", data=dict(csrf=self.csrf(), message="hi there")).status_code, 404)

    def test_seller_analytics_counts_views_messages_and_saves(self):
        for _ in range(3):
            self.client.get(self.path)                                         # anonymous views
        self.signup("buyer@example.com")
        self.client.post(self.path + "save/", data=dict(csrf=self.csrf()))
        self.client.post(self.path + "inquire/", data=dict(csrf=self.csrf(), message="Interested, please send more detail."))
        self.logout()
        self.login("seller@example.com")
        self.client.get(self.path)                                             # owner view is not counted
        with self.app.app_context():
            self.assertEqual(db.query("SELECT SUM(views) n FROM listing_views", one=True)["n"],
                             db.query("SELECT view_count FROM listings", one=True)["view_count"])
        html = self.client.get("/account/analytics/").get_data(as_text=True)
        self.assertIn("Views by week", html)
        self.assertIn(self.lst["title"], html)
        self.logout()
        self.signup("nolistings@example.com")
        self.assertIn("haven't listed a business yet", self.client.get("/account/analytics/").get_data(as_text=True))

    def test_verification_request_and_badge(self):
        self.assertNotIn("vbadge", self.client.get(self.path).get_data(as_text=True))
        self.login("seller@example.com")
        self.assertIn("Get a verification badge", self.client.get("/account/listings/").get_data(as_text=True))
        lid = self.lst["id"]
        short = self.client.post(f"/account/listings/{lid}/verification/", data=dict(csrf=self.csrf(), type="revenue_verified", note="x"),
                                 follow_redirects=True)
        self.assertIn("what evidence", short.get_data(as_text=True))
        self.client.post(f"/account/listings/{lid}/verification/", data=dict(
            csrf=self.csrf(), type="revenue_verified", note="Read-only Stripe access and 12 months of payout statements."))
        self.assertEqual(self.box[-1]["to"], ["admin@example.com"])
        self.assertIn("Verification requested on", self.client.get("/account/listings/").get_data(as_text=True))
        self.logout()
        self.signup("admin@example.com")
        self.assertIn("Read-only Stripe access", self.client.get("/admin/listings/?verification=requested").get_data(as_text=True))
        self.client.post(f"/admin/listings/{lid}/", data=dict(csrf=self.csrf(), action="verify", verification="revenue_verified"))
        self.assertEqual(self.box[-1]["to"], ["seller@example.com"])
        self.assertIn("revenue verified", self.box[-1]["subject"])
        self.logout()
        page = self.client.get(self.path).get_data(as_text=True)
        self.assertIn('class="vbadge"', page)
        self.assertIn("Revenue verified", page)
        with self.app.app_context():
            self.assertIsNone(db.query("SELECT verification_requested_at v FROM listings", one=True)["v"])
        self.app.config["VERIFICATION_REQUESTS_ENABLED"] = False
        self.login("seller@example.com")
        self.assertNotIn("Request a higher verification level", self.client.get("/account/listings/").get_data(as_text=True))


# ---------------------------------------------------------------- admin
class Phase2SearchHubAndLogs(Base):
    def setUp(self):
        super().setUp()
        self.box = self.app.extensions.setdefault("outbox", [])

    def test_saved_search_save_duplicate_alert_and_delete(self):
        self.signup("seller@example.com")
        self.make_listing()
        self.logout()
        page = self.client.get("/businesses-for-sale/saas/").get_data(as_text=True)
        self.assertIn("to save this search and get an email", page)
        self.signup("buyer@example.com")
        self.assertIn("Save this search", self.client.get("/businesses-for-sale/saas/").get_data(as_text=True))
        for _ in range(2):                                                      # second time is a duplicate
            r = self.client.post("/account/searches/save/", data=dict(csrf=self.csrf(), category="saas"))
            self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.post("/account/searches/save/", data=dict(csrf=self.csrf(), category="nope")).status_code, 400)
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) n FROM saved_searches", one=True)["n"], 1)
            sid = db.query("SELECT id FROM saved_searches", one=True)["id"]
        self.assertIn("Saved searches", self.client.get("/account/watchlist/").get_data(as_text=True))
        other = self.make_listing(category="ecommerce", title="Outdoor gear ecommerce store with repeat buyers")
        match = self.make_listing(title="Invoicing SaaS for freelance designers and studios")
        with self.app.app_context():
            from app.views.market_account import notify_saved_searches
            seller = db.query("SELECT id FROM users WHERE email='seller@example.com'", one=True)["id"]
            db.execute("UPDATE listings SET seller_id=?", (seller,))
            n = len(self.box)
            self.assertEqual(notify_saved_searches(other["id"]), 0)             # wrong category
            self.assertEqual(notify_saved_searches(match["id"]), 1)
            self.assertEqual(len(self.box), n + 1)
            self.assertEqual(self.box[-1]["to"], ["buyer@example.com"])
            self.assertIn("Invoicing SaaS", self.box[-1]["text"])
            db.execute("UPDATE listings SET seller_id=(SELECT id FROM users WHERE email='buyer@example.com')")
            self.assertEqual(notify_saved_searches(match["id"]), 0)             # never about your own listing
            self.assertIn(M.listing_path(match), self.box[-1]["text"])
        self.client.post(f"/account/searches/{sid}/delete/", data=dict(csrf=self.csrf()))
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) n FROM saved_searches", one=True)["n"], 0)

    def test_saved_search_limit_and_ownership(self):
        from app.views import market_account as MA
        self.signup("buyer@example.com")
        for i in range(MA.SEARCH_LIMIT + 2):
            self.client.post("/account/searches/save/", data=dict(csrf=self.csrf(), category="saas", price_max=str(1000 + i)))
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) n FROM saved_searches", one=True)["n"], MA.SEARCH_LIMIT)
            sid = db.query("SELECT id FROM saved_searches", one=True)["id"]
        self.logout()
        self.signup("other@example.com")
        self.client.post(f"/account/searches/{sid}/delete/", data=dict(csrf=self.csrf()))   # not theirs
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) n FROM saved_searches", one=True)["n"], MA.SEARCH_LIMIT)

    def test_hub_sections_appear_only_with_data(self):
        self.assertNotIn("Most viewed this month", self.client.get("/businesses-for-sale/").get_data(as_text=True))
        self.signup("seller@example.com")
        lst = self.make_listing()
        self.logout()
        self.client.get(M.listing_path(lst))
        self.signup("buyer@example.com")
        self.client.post(M.listing_path(lst) + "save/", data=dict(csrf=self.csrf()))
        hub = self.client.get("/businesses-for-sale/").get_data(as_text=True)
        for heading in ("Top categories", "Most viewed this month", "Most saved by buyers"):
            self.assertIn(heading, hub)
        self.assertNotIn("Featured listings", hub)                              # nothing is featured

    def test_listing_page_is_not_edge_cached(self):
        self.signup("seller@example.com")
        lst = self.make_listing()
        self.logout()
        self.assertEqual(self.client.get(M.listing_path(lst)).headers["Cache-Control"], "no-cache")

    def test_activity_log_records_and_is_admin_only(self):
        self.signup("user@example.com")
        self.logout()
        self.client.post("/login/", data=dict(email="user@example.com", password="wrong-password-9", csrf=self.csrf()))
        self.client.post("/login/", data=dict(email="user@example.com", password="correct-horse-1", csrf=self.csrf()))
        self.assertEqual(self.client.get("/admin/activity/").status_code, 404)
        self.assertEqual(self.client.get("/admin/errors/").status_code, 404)
        with self.app.app_context():
            acts = [r["action"] for r in db.query("SELECT action FROM activity_log ORDER BY id")]
        self.assertEqual(acts, ["signup", "login_failed", "login"])
        self.logout()
        self.signup("admin@example.com")
        page = self.client.get("/admin/activity/").get_data(as_text=True)
        self.assertIn("login failed", page)
        self.assertIn("user@example.com", page)
        self.assertNotIn("wrong-password-9", page)                              # passwords are never logged

    def test_error_log_groups_repeats_and_alerts_once(self):
        from app import activity
        def boom():
            raise ValueError("kaboom <b>")
        for _ in range(3):
            with self.app.test_request_context("/tools/website-valuation/"):
                try:
                    boom()
                except ValueError as e:
                    activity.record_error(e)
        with self.app.app_context():
            rows = db.query("SELECT * FROM error_log")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["count"], 3)
        alerts = [m for m in self.box if m["subject"].startswith("Website error")]
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["to"], ["admin@example.com"])
        self.signup("admin@example.com")
        page = self.client.get("/admin/errors/").get_data(as_text=True)
        self.assertIn("ValueError", page)
        self.assertIn("kaboom &lt;b&gt;", page)
        with self.app.app_context():
            fp = db.query("SELECT fingerprint FROM error_log", one=True)["fingerprint"]
        self.client.post("/admin/errors/", data=dict(csrf=self.csrf(), fingerprint=fp))
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) n FROM error_log", one=True)["n"], 0)

    def test_llms_txt_and_comparison_guides(self):
        r = self.client.get("/llms.txt")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.mimetype.startswith("text/plain"))
        body = r.get_data(as_text=True)
        self.assertIn("/guides/sde-vs-ebitda/", body)
        self.assertNotIn("/account/", body)
        self.assertNotIn("/admin/", body)
        for path in ("/guides/sde-vs-ebitda/", "/guides/ways-to-sell-a-digital-business/"):
            r = self.client.get(path)
            self.assertEqual(r.status_code, 200)
            html = r.get_data(as_text=True)
            self.assertEqual(html.count("<h1"), 1)
            self.assertTrue(canonical(html).endswith(path))
        sm = "".join(self.client.get(p).get_data(as_text=True) for p in ("/sitemap.xml", "/sitemap-pages.xml"))
        self.assertNotIn("llms.txt", sm)


class Phase2Insights(Base):
    def setUp(self):
        super().setUp()
        self.box = self.app.extensions.setdefault("outbox", [])
        self.signup("seller@example.com")

    def login(self, email, pw="correct-horse-1"):
        return self.client.post("/login/", data=dict(email=email, password=pw, csrf=self.csrf()))

    # ---- price check, listing strength and buyer checks
    def test_price_check_matches_the_valuation_engine(self):
        from app import insights, valuation as V
        l = self.make_listing(asking_price=480000)            # SaaS: $20k MRR, $12k profit, 4 years
        with self.app.app_context():
            pc = insights.price_check(l)
            r = V.value_business("saas", dict(mrr=20000, monthly_profit=12000, age_years=4))
            self.assertEqual((pc["low"], pc["high"]), (r["value"]["low"], r["value"]["high"]))
            self.assertEqual(pc["verdict"], "within" if r["value"]["low"] <= 480000 <= r["value"]["high"] else pc["verdict"])
            db.execute("UPDATE listings SET asking_price=? WHERE id=?", (r["value"]["high"] * 2, l["id"]))
            l2 = db.query("SELECT * FROM listings WHERE id=?", (l["id"],), one=True)
            pc2 = insights.price_check(l2)
            self.assertEqual((pc2["verdict"], pc2["pct"]), ("above", 100))
            db.execute("UPDATE listings SET category='websites', monthly_profit=0 WHERE id=?", (l["id"],))
            self.assertIsNone(insights.price_check(db.query("SELECT * FROM listings WHERE id=?", (l["id"],), one=True)))

    def test_listing_strength_rises_with_detail_and_shows_on_my_listings(self):
        from app import insights
        l = self.make_listing()
        with self.app.app_context():
            before = insights.strength(l)
            db.execute("UPDATE listings SET growth_note='Up 20% year on year', assets_included='Code, domain, customers', "
                       "reason_for_sale='Starting a new company', industry='Dental', country='United States', "
                       "website_url='https://example.com' WHERE id=?", (l["id"],))
            after = insights.strength(db.query("SELECT * FROM listings WHERE id=?", (l["id"],), one=True))
        self.assertGreater(after["score"], before["score"])
        self.assertLess(len(after["tips"]), len(before["tips"]))
        self.assertLessEqual(after["score"], 100)
        page = self.client.get("/account/listings/").get_data(as_text=True)
        self.assertIn("Listing strength", page)
        self.assertIn("Price check:", page)
        self.assertIn("Prove you own example.com", page)

    def test_buyer_checks_on_listing_page(self):
        from app import insights
        l = self.make_listing(asking_price=3000000, age_years=0.5)
        with self.app.app_context():
            dd = insights.due_diligence(l)
        titles = " | ".join(f["title"] for f in dd["flags"])
        self.assertIn("Less than one year old", titles)
        self.assertIn("Figures are not verified", titles)
        self.assertEqual(dd["flags"][0]["level"], "risk")                       # risks listed first
        self.assertTrue(any("12.5× annual recurring revenue" in f["title"] and f["level"] == "risk" for f in dd["flags"]))
        self.assertTrue(any("billing-system export" in q for q in dd["checklist"]))
        self.logout()
        page = self.client.get(M.listing_path(l)).get_data(as_text=True)
        self.assertIn("Automatic checks", page)
        self.assertIn("not a verification and not advice", page)
        with self.app.app_context():
            M.set_status(l["id"], "sold", by="test")
        self.assertNotIn("Automatic checks", self.client.get(M.listing_path(l)).get_data(as_text=True))

    # ---- website ownership
    def test_ownership_host_rules_block_private_and_odd_addresses(self):
        from app import ownership as O
        self.assertEqual(O.host_of("https://www.Example.com/path"), "www.example.com")
        for bad in ("http://127.0.0.1/", "http://localhost/", "https://10.0.0.5/", "ftp://example.com/",
                    "https://user:pw@example.com/", "https://example.com:8080/", "http://169.254.169.254/latest/",
                    "https://[::1]/", "javascript:alert(1)", "", None):
            self.assertIsNone(O.host_of(bad), bad)
        with mock.patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("10.1.2.3", 443))]):
            self.assertFalse(O._public("intranet.example.com"))
            self.assertIsNone(O.http_get("https://intranet.example.com/"))     # resolves to a private address
        with mock.patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 443))]):
            self.assertTrue(O._public("example.com"))

    def test_ownership_check_by_file_meta_and_dns(self):
        from app import ownership as O
        l = self.make_listing()
        with self.app.app_context():
            db.execute("UPDATE listings SET website_url='https://www.example.com' WHERE id=?", (l["id"],))
            l = db.query("SELECT * FROM listings WHERE id=?", (l["id"],), one=True)
            code = O.code_for(l)
            none = lambda *_: None
            self.assertIsNone(O.check(l, fetch=none, txt=lambda h: []))
            self.assertIsNone(O.check(l, fetch=lambda u: "wrong", txt=lambda h: ["valueraq-verify=nope"]))
            self.assertEqual(O.check(l, fetch=lambda u: code if u.endswith("/valueraq-verify.txt") else "", txt=lambda h: []), "file")
            meta = f'<html><head><meta name="valueraq-verify" content="{code}"></head></html>'
            self.assertEqual(O.check(l, fetch=lambda u: meta if u.endswith(".com/") else None, txt=lambda h: []), "meta")
            self.assertIsNone(O.check(l, fetch=lambda u: f"<p>{code}</p>" if u.endswith(".com/") else None, txt=lambda h: []))
            self.assertEqual(O.check(l, fetch=none, txt=lambda h: [f"valueraq-verify={code}"] if h == "example.com" else []), "dns")
            other = dict(l); other["seller_id"] = 999
            self.assertNotEqual(O.code_for(other), code)                        # codes are per seller

    def test_ownership_badge_flow_and_reset_on_url_change(self):
        from app import ownership as O
        l = self.make_listing()
        path = M.listing_path(l)
        post = lambda: self.client.post(f"/account/listings/{l['id']}/ownership/", data=dict(csrf=self.csrf()))
        post()                                                                 # no website address yet
        with self.app.app_context():
            self.assertIsNone(db.query("SELECT ownership_verified_at v FROM listings", one=True)["v"])
            db.execute("UPDATE listings SET website_url='https://example.com' WHERE id=?", (l["id"],))
        with mock.patch.object(O, "http_get", return_value=None), mock.patch.object(O, "dns_txt", return_value=[]):
            post()
        self.assertNotIn("Website ownership confirmed", self.client.get(path).get_data(as_text=True))
        with self.app.app_context():
            code = O.code_for(db.query("SELECT * FROM listings WHERE id=?", (l["id"],), one=True))
        with mock.patch.object(O, "http_get", return_value=code), mock.patch.object(O, "dns_txt", return_value=[]):
            post()
        self.assertIn("Website ownership confirmed", self.client.get(path).get_data(as_text=True))
        with self.app.app_context():
            row = db.query("SELECT * FROM listings WHERE id=?", (l["id"],), one=True)
            self.assertEqual((row["ownership_method"], row["ownership_host"]), ("file", "example.com"))
            self.assertTrue(db.query("SELECT 1 FROM activity_log WHERE action='ownership_verified'", one=True))
            form = {f: ("" if row[f] is None else row[f]) for f in
                    ("category", "title", "headline", "description", "business_model", "asking_price",
                     "monthly_revenue", "monthly_profit", "age_years")}
        form.update(csrf=self.csrf(), website_url="https://another-site.com", confirm="1")
        self.assertEqual(self.client.post(f"/account/listings/{l['id']}/edit/", data=form).status_code, 302)
        with self.app.app_context():
            self.assertIsNone(db.query("SELECT ownership_verified_at v FROM listings", one=True)["v"])
        # someone else can't run the check on this listing
        self.logout()
        self.signup("other@example.com")
        self.assertEqual(post().status_code, 404)

    # ---- attachments
    def _thread(self):
        l = self.make_listing()
        self.logout()
        self.signup("buyer@example.com")
        self.client.post(M.listing_path(l) + "inquire/", data=dict(csrf=self.csrf(), message="Could you share the last 12 months of revenue?"))
        with self.app.app_context():
            return db.query("SELECT id FROM inquiries", one=True)["id"]

    def test_attachments_upload_download_limits_and_privacy(self):
        iid = self._thread()
        url = f"/account/inquiries/{iid}/"
        self.assertNotIn('type="file"', self.client.get(url).get_data(as_text=True))   # storage not set up: no upload box
        store = self.app.extensions["file_store"] = FakeStore()
        self.assertIn('type="file"', self.client.get(url).get_data(as_text=True))
        send = lambda name, data, msg="": self.client.post(url, data=dict(
            csrf=self.csrf(), message=msg, file=(io.BytesIO(data), name)), content_type="multipart/form-data")
        send("statement.pdf", b"%PDF-1.7 fake statement", "Here is the statement")
        send("run.exe", b"MZ....")                                             # type not allowed
        send("fake.pdf", b"<html>not a pdf</html>")                            # content doesn't match the name
        send("big.txt", b"a" * (self.app.config["ATTACH_MAX_BYTES"] + 1))      # too big
        send("notes.txt", b"plain notes")                                      # a file with no message is fine
        with self.app.app_context():
            files = db.query("SELECT * FROM message_files ORDER BY id")
        self.assertEqual([f["name"] for f in files], ["statement.pdf", "notes.txt"])
        self.assertEqual(len(store.objects), 2)
        self.assertTrue(all(k.startswith(f"attachments/{iid}/") for k in store.objects))
        self.assertIn("[File attached: statement.pdf]", self.box[-2]["text"])
        page = self.client.get(url).get_data(as_text=True)
        self.assertIn("statement.pdf", page)
        r = self.client.get(f"{url}files/{files[0]['id']}/")
        self.assertEqual(r.data, b"%PDF-1.7 fake statement")
        self.assertIn("attachment", r.headers["Content-Disposition"])
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(r.mimetype, "application/octet-stream")
        self.logout()
        self.login("seller@example.com")
        self.assertEqual(self.client.get(f"{url}files/{files[0]['id']}/").status_code, 200)   # the seller can
        self.logout()
        self.signup("other@example.com")
        self.assertEqual(self.client.get(f"{url}files/{files[0]['id']}/").status_code, 404)   # nobody else
        self.logout()
        self.assertEqual(self.client.get(f"{url}files/{files[0]['id']}/").status_code, 302)

    def test_attachment_limit_per_conversation(self):
        iid = self._thread()
        self.app.extensions["file_store"] = FakeStore()
        self.app.config["ATTACH_PER_THREAD"] = 2
        for i in range(3):
            self.client.post(f"/account/inquiries/{iid}/", data=dict(csrf=self.csrf(), message="", file=(io.BytesIO(b"x"), f"n{i}.txt")),
                             content_type="multipart/form-data")
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) n FROM message_files", one=True)["n"], 2)

    # ---- two-step login
    def _code(self):
        import re
        return re.search(r"\b(\d{6})\b", self.box[-1]["text"]).group(1)

    def test_two_step_login_for_admin(self):
        self.logout()
        self.signup("admin@example.com")
        page = self.client.get("/account/settings/").get_data(as_text=True)
        self.assertIn("Two-step login", page)
        ts = lambda **kw: self.client.post("/account/settings/two-step/", data=dict(csrf=self.csrf(), **kw))
        ts(action="confirm", code="000000")                                    # can't switch on without a real code
        with self.app.app_context():
            self.assertEqual(db.query("SELECT twofa_enabled v FROM users WHERE email='admin@example.com'", one=True)["v"], 0)
        ts(action="send")
        ts(action="confirm", code=self._code())
        with self.app.app_context():
            self.assertEqual(db.query("SELECT twofa_enabled v FROM users WHERE email='admin@example.com'", one=True)["v"], 1)
        self.logout()
        r = self.login("admin@example.com")
        self.assertTrue(r.headers["Location"].endswith("/login/code/"))
        self.assertEqual(self.client.get("/admin/").status_code, 302)           # password alone isn't enough
        self.assertEqual(self.client.post("/login/code/", data=dict(csrf=self.csrf(), code="123456")).status_code, 422)
        good = self._code()
        self.client.post("/login/code/", data=dict(csrf=self.csrf(), resend="1"))
        self.assertEqual(self.client.post("/login/code/", data=dict(csrf=self.csrf(), code=good)).status_code, 422)  # old code dead
        r = self.client.post("/login/code/", data=dict(csrf=self.csrf(), code=self._code()))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.client.get("/admin/").status_code, 200)
        ts(action="disable", current_password="wrong")
        with self.app.app_context():
            self.assertEqual(db.query("SELECT twofa_enabled v FROM users WHERE email='admin@example.com'", one=True)["v"], 1)
        ts(action="disable", current_password="correct-horse-1")
        self.logout()
        self.assertTrue(self.login("admin@example.com").headers["Location"].endswith("/account/"))

    def test_two_step_code_locks_after_five_wrong_tries_and_is_admin_only(self):
        self.assertNotIn("Two-step login", self.client.get("/account/settings/").get_data(as_text=True))
        self.assertEqual(self.client.post("/account/settings/two-step/", data=dict(csrf=self.csrf(), action="send")).status_code, 404)
        self.assertEqual(self.client.get("/login/code/").status_code, 302)     # nothing pending
        self.logout()
        self.signup("admin@example.com")
        with self.app.app_context():
            db.execute("UPDATE users SET twofa_enabled=1 WHERE email='admin@example.com'")
        self.logout()
        self.login("admin@example.com")
        good = self._code()
        for _ in range(5):
            self.client.post("/login/code/", data=dict(csrf=self.csrf(), code="000001"))
        self.assertEqual(self.client.post("/login/code/", data=dict(csrf=self.csrf(), code=good)).status_code, 422)
        # the emergency switch turns the second step off
        self.app.config["ADMIN_2FA"] = False
        self.assertTrue(self.login("admin@example.com").headers["Location"].endswith("/account/"))

    # ---- UX and content
    def test_home_paths_hub_cards_getting_started_and_new_pages(self):
        self.logout()
        home = self.client.get("/").get_data(as_text=True)
        self.assertIn("What would you like to do?", home)
        hub = self.client.get("/businesses-for-sale/").get_data(as_text=True)
        self.assertIn("The marketplace is open for its first listings", hub)
        self.assertIn("Browse by type", hub)
        self.signup("new@example.com")
        acct = self.client.get("/account/").get_data(as_text=True)
        self.assertIn("Getting started", acct)
        self.assertIn("0 of 3 done", acct)
        self.client.post("/account/searches/save/", data=dict(csrf=self.csrf(), category="saas"))
        self.assertIn("1 of 3 done", self.client.get("/account/").get_data(as_text=True))
        self.assertIn("1. The basics", self.client.get("/sell/").get_data(as_text=True))
        for path in ("/guides/newsletter-valuation/", "/guides/app-valuation/", "/guides/ecommerce-valuation/",
                     "/glossary/earnout/", "/glossary/escrow/", "/glossary/asset-sale/", "/glossary/letter-of-intent/",
                     "/glossary/seller-financing/", "/glossary/net-revenue-retention/", "/glossary/average-order-value/",
                     "/glossary/open-rate/"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        self.assertIn("Website ownership", self.client.get("/verification/").get_data(as_text=True))


class SocialProfiles(Base):
    def test_footer_links_and_schema_same_as(self):
        html = self.client.get("/").get_data(as_text=True)
        urls = ["https://www.linkedin.com/company/145275373/", "https://x.com/valueraq",
                "https://www.facebook.com/profile.php?id=61594665137424"]
        for u in urls:
            self.assertIn(f'href="{u}" target="_blank" rel="noopener me"', html)
        graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))["@graph"]
        org = [n for n in graph if n["@type"] == "Organization"][0]
        self.assertEqual(org["sameAs"], urls)
        self.assertIn("Follow VALUERAQ", self.client.get("/guides/saas-valuation/").get_data(as_text=True))


class GoogleAnalytics(Base):
    def test_ga_loads_on_public_pages_with_consent_bar_and_csp(self):
        r = self.client.get("/")
        html = r.get_data(as_text=True)
        self.assertIn('data-ga-id="G-TEST123"', html)
        self.assertIn('id="cookie-bar"', html)
        self.assertIn(" hidden>", html.split('id="cookie-bar"')[1][:80])        # shown by script only when no choice is stored
        self.assertIn("data-cookie-settings", html)
        csp = r.headers["Content-Security-Policy"]
        self.assertIn("script-src 'self' https://www.googletagmanager.com;", csp)
        self.assertIn("https://*.google-analytics.com", csp)
        self.assertNotIn("unsafe-inline' https://www.googletagmanager", csp)
        self.assertNotIn("<script>", html)                                      # still no inline scripts
        js = self.client.get("/static/js/ga.js").get_data(as_text=True)
        self.assertIn('ad_storage: "denied"', js)
        self.assertIn('analytics_storage: choice === "granted" ? "granted" : "denied"', js)
        self.assertIn("Google Analytics", self.client.get("/privacy/").get_data(as_text=True))

    def test_ga_not_on_private_pages_and_can_be_switched_off(self):
        self.signup()
        self.assertNotIn("data-ga-id", self.client.get("/account/").get_data(as_text=True))
        self.app.config["GA_MEASUREMENT_ID"] = ""
        r = self.client.get("/")
        self.assertNotIn("ga.js", r.get_data(as_text=True))
        self.assertIn("script-src 'self';", r.headers["Content-Security-Policy"])
        self.assertNotIn("google", r.headers["Content-Security-Policy"].replace("fonts.googleapis.com", ""))


class ContactAndRefundPolicy(Base):
    def test_contact_details_on_page_and_in_schema(self):
        html = self.client.get("/contact/").get_data(as_text=True)
        self.assertIn('href="mailto:hello@valueraq.com"', html)
        self.assertIn('href="tel:+12172909383"', html)
        self.assertIn("+1 217 290 9383", html)
        graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))["@graph"]
        org = [n for n in graph if n["@type"] == "Organization"][0]
        self.assertEqual((org["email"], org["telephone"]), ("hello@valueraq.com", "+12172909383"))
        self.assertEqual(org["contactPoint"]["contactType"], "customer support")

    def test_refund_policy_page(self):
        r = self.client.get("/refund-policy/")
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertEqual(html.count("<h1"), 1)
        self.assertIn("within 7 days", html)
        self.assertTrue(canonical(html).endswith("/refund-policy/"))
        self.assertIn("/refund-policy/</loc>", self.client.get("/sitemap-pages.xml").get_data(as_text=True))
        self.assertIn('href="/refund-policy/"', self.client.get("/").get_data(as_text=True))
        self.assertIn("/refund-policy/", self.client.get("/terms/").get_data(as_text=True))
        self.assertIn("mailto:refund@valueraq.com", html)
        self.assertNotIn("help@valueraq.com", html)

    def test_legal_pages_name_the_owner(self):
        for slug in ("terms", "privacy", "disclaimer"):
            html = self.client.get(f"/{slug}/").get_data(as_text=True)
            self.assertIn("owned and operated by Advent Business Consultax LLC", html, slug)
            self.assertIn("18W100 22nd St, Suite 124, Oakbrook Terrace, IL 60181", html, slug)
            self.assertNotIn("Pakistan", html, slug)
        home = self.client.get("/").get_data(as_text=True)
        graph = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', home, re.S).group(1))["@graph"]
        org = [n for n in graph if n["@type"] == "Organization"][0]
        self.assertEqual(org["legalName"], "Advent Business Consultax LLC")
        self.assertEqual((org["address"]["postalCode"], org["address"]["addressCountry"]), ("60181", "US"))

    def test_policy_and_help_pages_exist_and_are_linked(self):
        home = self.client.get("/").get_data(as_text=True)
        sm = self.client.get("/sitemap-pages.xml").get_data(as_text=True)
        for slug in ("cookie-policy", "disclaimer", "buyer-safety", "how-it-works", "fees", "report-a-listing"):
            r = self.client.get(f"/{slug}/")
            self.assertEqual(r.status_code, 200, slug)
            html = r.get_data(as_text=True)
            self.assertEqual(html.count("<h1"), 1, slug)
            self.assertTrue(canonical(html).endswith(f"/{slug}/"))
            self.assertIn(f'href="/{slug}/"', home)                             # in the footer of every page
            self.assertIn(f"/{slug}/</loc>", sm)
            self.assertNotIn("help@valueraq.com", html)
        fees = self.client.get("/fees/").get_data(as_text=True)
        cfg = self.app.config
        for plan in ("pro_monthly", "pro_yearly"):
            self.assertIn(f"${cfg['PLANS'][plan]['price_usd']}", fees)          # the page can't drift from real prices
        for plan in ("featured_monthly", "featured_yearly"):
            self.assertIn(f"${cfg['FEATURED_PLANS'][plan]['price_usd']}", fees)
        cookies = self.client.get("/cookie-policy/").get_data(as_text=True)
        for name in ("vq_sid", "vq_ch", "vq_lp", "_ga", "vq_cookie_choice"):
            self.assertIn(name, cookies)
        self.assertIn('href="/cookie-policy/"', home.split('id="cookie-bar"')[1][:600])


class CoreGuidesAndComparisons(Base):
    def test_core_guides_and_comparison_pages_exist(self):
        slugs = ["website-valuation", "saas-valuation", "how-to-sell-a-website", "how-to-buy-a-saas-business",
                 "digital-business-due-diligence", "website-valuation-methods", "saas-valuation-methods",
                 "ai-business-valuation-methods", "valueraq-vs-flippa", "valueraq-vs-acquire",
                 "website-vs-saas-investment", "buy-vs-build-saas"]
        index = self.client.get("/guides/").get_data(as_text=True)
        for slug in slugs:
            r = self.client.get(f"/guides/{slug}/")
            self.assertEqual(r.status_code, 200, slug)
            self.assertEqual(r.get_data(as_text=True).count("<h1"), 1, slug)
            self.assertIn(f"/guides/{slug}/", index, slug)

    def test_competitor_pages_are_honest_and_sourced(self):
        for slug, name in (("valueraq-vs-flippa", "Flippa"), ("valueraq-vs-acquire", "Acquire.com")):
            html = self.client.get(f"/guides/{slug}/").get_data(as_text=True)
            self.assertIn("is not affiliated with", html)
            self.assertIn("no track record of completed sales", html)           # says plainly that the site is new
            self.assertIn("checked on 4 October 2026", html)
            self.assertIn(f"When {name} is the better choice", html)


class Slogan(Base):
    def test_slogan_on_home_footer_and_description(self):
        slogan = "All valuation features, at much lower fees than the leading marketplaces."
        home = self.client.get("/").get_data(as_text=True)
        self.assertIn(f'<p class="slogan">{slogan}</p>', home)
        self.assertTrue(meta(home, "description").startswith(slogan))
        self.assertLessEqual(len(meta(home, "description")), 158)
        self.assertIn(slogan, self.client.get("/guides/saas-valuation/").get_data(as_text=True).split("site-foot")[1])


class Admin(Base):
    def login_admin(self):
        self.signup("admin@example.com")

    def test_admin_hidden_from_users(self):
        self.signup()
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    def test_override_applies_and_is_logged(self):
        self.login_admin()
        r = self.client.post("/admin/seo/page/", data=dict(csrf=self.csrf(), path="/guides/saas-valuation/",
                                                            meta_title="SaaS Valuation Guide Override", reason="test"))
        self.assertEqual(r.status_code, 302)
        html = self.client.get("/guides/saas-valuation/").get_data(as_text=True)
        self.assertIn("<title>SaaS Valuation Guide Override</title>", html)
        with self.app.app_context():
            self.assertTrue(db.query("SELECT 1 FROM seo_change_log WHERE path='/guides/saas-valuation/' "
                                     "AND field='meta_title'", one=True))

    def test_noindex_override_removes_from_sitemap(self):
        self.login_admin()
        self.client.post("/admin/seo/page/", data=dict(csrf=self.csrf(), path="/glossary/cac/", indexable="0"))
        self.logout()
        self.assertIn("noindex", meta(self.client.get("/glossary/cac/").get_data(as_text=True), "robots"))
        self.assertNotIn("/glossary/cac/", self.client.get("/sitemap-guides.xml").get_data(as_text=True))

    def test_blog_publish_gate(self):
        self.login_admin()
        tok = self.csrf()
        r = self.client.post("/admin/blog/new/", data=dict(csrf=tok, title="Thin post", body_md="Too short.",
                                                           action="publish", primary_intent="informational"))
        self.assertIn("Not published", r.get_data(as_text=True))
        body = ("## Why it matters\n\n" + "Real useful sentence about churn and SaaS valuation. " * 60 +
                "\n\nSee the [SaaS tool](/tools/saas-valuation/), the [guide](/guides/saas-valuation/) and "
                "[churn](/glossary/churn/).")
        r = self.client.post("/admin/blog/1/", data=dict(csrf=tok, title="How churn changes a SaaS price",
                                                         meta_description="What monthly churn does to the value of a "
                                                         "small SaaS business, with the arithmetic behind it.",
                                                         body_md=body, action="publish", primary_intent="informational",
                                                         ai_assisted="1"))
        self.assertIn("named human reviewer", r.get_data(as_text=True))
        r = self.client.post("/admin/blog/1/", data=dict(csrf=tok, title="How churn changes a SaaS price",
                                                         meta_description="What monthly churn does to the value of a "
                                                         "small SaaS business, with the arithmetic behind it.",
                                                         body_md=body, action="publish", primary_intent="informational",
                                                         ai_assisted="1", reviewed_by="Editor"))
        self.assertEqual(r.status_code, 302)
        self.logout()
        self.assertEqual(self.client.get("/blog/how-churn-changes-a-saas-price/").status_code, 200)
        self.assertIn("sitemap-blog", self.client.get("/sitemap.xml").get_data(as_text=True))

    def test_audit_runs_and_redirect_admin(self):
        self.login_admin()
        r = self.client.post("/admin/seo/redirects/", data=dict(csrf=self.csrf(), action="add", from_path="/old/",
                                                                to_path="/guides/"))
        self.assertEqual(self.client.get("/old/").status_code, 301)
        r = self.client.post("/admin/seo/redirects/", data=dict(csrf=self.csrf(), action="add", from_path="/gone-x/",
                                                                to_path="/"))
        self.assertEqual(self.client.get("/gone-x/").status_code, 404)  # homepage redirect refused without confirm
        self.client.post("/admin/seo/redirects/", data=dict(csrf=self.csrf(), action="gone", from_path="/gone-y/"))
        self.assertEqual(self.client.get("/gone-y/").status_code, 410)
        r = self.client.post("/admin/seo/run/", data=dict(csrf=self.csrf()), follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn("URLs crawled", r.get_data(as_text=True))


# ---------------------------------------------------------------- §81 acceptance: full audit
class PreLaunchAcceptance(Base):
    def test_full_audit_has_no_critical_issues(self):
        self.make_listing()
        with self.app.app_context():
            summary, results = audit.run(store=False)
        crit = [(r["path"], i["message"]) for r in results for i in r["issues"] if i["severity"] == "critical"]
        crit += [("site", i["message"]) for i in summary["site_issues"]]
        self.assertEqual(crit, [])
        self.assertTrue(all(p["ok"] for p in summary["probes"]), summary["probes"])
        self.assertGreater(summary["indexable"], 50)

    def test_analytics_beacon_and_classification(self):
        from app.analytics import classify
        self.assertEqual(classify("https://www.google.com/", "www.valueraq.com"), "organic")
        self.assertEqual(classify("https://chatgpt.com/", "www.valueraq.com"), "ai")
        self.assertEqual(classify("", "www.valueraq.com"), "direct")
        r = self.client.post("/api/events/", data=json.dumps({"n": "page_view", "p": "/", "sid": "s1", "first": 1,
                                                              "ref": "https://www.bing.com/"}),
                             content_type="application/json")
        self.assertEqual(r.json["ch"], "organic")
        with self.app.app_context():
            self.assertEqual(db.query("SELECT COUNT(*) n FROM events WHERE name='organic_landing'", one=True)["n"], 1)


if __name__ == "__main__":
    unittest.main()


class StaticAssets(Base):
    def test_referenced_assets_exist(self):
        for p in ("/static/css/site.css", "/static/js/v.js", "/static/js/calc.js", "/static/brand/favicon.svg",
                  "/static/brand/valueraq-logo.png", "/static/og/valueraq-default.png"):
            self.assertEqual(self.client.get(p).status_code, 200, p)


if __name__ == "__main__":
    unittest.main()
