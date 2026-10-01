"""End-to-end tests for VALUERAQ, including the §81 pre-launch SEO acceptance checks.

Run:  python -m unittest discover -s tests -v
"""
import hashlib
import hmac
import json
import os
import re
import sys
import tempfile
import time
import unittest

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
        self.assertIn("$390", html)
        self.assertIn("Save 17%", html)
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


# ---------------------------------------------------------------- admin
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
