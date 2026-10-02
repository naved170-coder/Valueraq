# VALUERAQ

Digital business valuation tools and marketplace, with the SEO specification built into the architecture.
Read `ARCHITECTURE.md` for how each part of the SEO specification is implemented.

## What's included

| Area | What it does |
|---|---|
| Valuation tools | 6 tools (website, SaaS, AI, app, newsletter, ecommerce) + 3 calculators, one shared engine (`app/valuation.py`) |
| Content | 9 guides, 17 glossary terms, 6 category guides, methodology, data sources, FAQ, about, contact, editorial policy, verification, marketplace rules, privacy, terms (`content/*.md`) |
| Marketplace | Category pages, pagination, filters (noindex), listing pages, sell flow, moderation, quality scoring, duplicate/spam detection, 301/410 handling, buyer inquiries |
| Accounts | Signup/login, private saved reports, 14-day Pro trial (no card), Stripe subscriptions, featured listings, customer portal |
| SEO system | Canonicals, robots meta + headers, segmented sitemaps, robots.txt, JSON-LD (validated), breadcrumbs, internal-linking engine, glossary auto-links, redirect table with chain collapse, 410s |
| Admin (`/admin/`) | SEO audit crawler + quality scores, per-page overrides with change log, redirects/410s, keyword import, Search Console/Bing import, listing moderation, blog CMS with pre-publish gate, analytics funnels, Core Web Vitals |
| Analytics | First-party only: channel attribution (organic/AI/direct…), tool and marketplace funnels, field Web Vitals |

## Run locally

```bash
pip install -r requirements.txt
python manage.py run                      # http://localhost:5000
python manage.py create-admin you@example.com
python -m unittest discover -s tests -v   # 54 tests, including the pre-launch SEO acceptance audit
python manage.py audit                    # crawl the whole site and list SEO issues
```

## Deploy (Render, about 10 minutes)

1. Put this folder in a GitHub repository.
2. In Render, choose **New → Blueprint**, select the repository. `render.yaml` creates the web service and a persistent disk for the database.
3. Fill in `ADMIN_EMAILS` (your email). Leave the Stripe keys empty until you're ready.
4. After the first deploy, open the site, sign up with your admin email, and visit `/admin/seo/` → **Run audit now**.
5. Point DNS for `www.valueraq.com` and `valueraq.com` at the service, then set `ENFORCE_CANONICAL_HOST=1`. All other hosts (including the apex domain) then 301 to `https://www.valueraq.com`.
6. Add the site to Google Search Console and Bing Webmaster Tools, set the verification env vars, and submit `https://www.valueraq.com/sitemap.xml`.

Any host that runs Python works (Railway, Fly.io, a VPS): run `gunicorn wsgi:app` with the env vars in `.env.example`. Put a CDN such as Cloudflare in front for caching and compression; public pages already send `s-maxage` cache headers.

Run `python manage.py expire-featured` once a day (for example as a Render cron job) to end featured listings on time.

## Payments (Stripe)

1. Create four recurring prices: Pro monthly and yearly, and Featured listing monthly and yearly (one subscription per featured listing).
2. Set `STRIPE_SECRET_KEY` and the four price IDs: `STRIPE_PRICE_PRO_MONTHLY`, `STRIPE_PRICE_PRO_YEARLY`, `STRIPE_PRICE_FEATURED_MONTHLY`, `STRIPE_PRICE_FEATURED_YEARLY`.
3. Add a webhook endpoint `https://www.valueraq.com/api/stripe/webhook/` for `checkout.session.completed` and `customer.subscription.*`, then set `STRIPE_WEBHOOK_SECRET`.
4. Enable the Customer Portal in Stripe.

Until keys are set, payment buttons say payments aren't available, and admins can grant Pro manually at `/admin/users/`.

## Email (Resend)

Set `RESEND_API_KEY` (and optionally `EMAIL_FROM`, default `VALUERAQ <no-reply@valueraq.com>`; the domain must be verified in Resend). The site then sends: welcome, forgot password, buyer inquiry to the seller, listing approved / needs changes, and new listing or contact message to the admins in `ADMIN_EMAILS`. Email never blocks a page: it is sent on a background thread and failures are only logged. `/admin/backups/` has a "Send me a test email" button.

## Backups (Cloudflare R2)

Set `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` and `R2_BUCKET` (a private bucket; token with Object Read & Write on that bucket only). The web service then uploads a compressed, integrity-checked snapshot of the database to `backups/` every 24 hours and keeps the newest 30. Status, "Back up now" and downloads are at `/admin/backups/`.

To restore, open the Render **Shell** for the web service and run:

```bash
python manage.py restore-backup backups/valueraq-YYYYMMDD-HHMMSS.db.gz          # downloads and verifies only
python manage.py restore-backup backups/valueraq-YYYYMMDD-HHMMSS.db.gz --apply  # replaces the live database
```

`--apply` keeps the previous database as `valueraq.db.before-restore`. Restart the service afterwards.

## Decisions for the owner before launch

- **Prices:** Pro $29/month or $290/year, featured listing $39/month or $390/year per listing, and 3 free saved reports are placeholders in `app/config.py`.
- **Default multiples:** the ranges in `app/valuation.py` are editorial assumptions and are labelled as such everywhere. Review them; any change should bump `METHODOLOGY_VERSION` and add a row to the change log in `content/pages/methodology.md`.
- **Legal pages:** `privacy.md` and `terms.md` describe how the platform actually works, but they are drafts. A lawyer should add the legal entity name, address, governing law and jurisdiction-specific privacy wording.
- **Contact email:** `CONTACT_EMAIL` defaults to `hello@valueraq.com` (used in Organization schema). Set it to an inbox that exists.
- **Author/E-E-A-T:** guides are credited to the "VALUERAQ Editorial Team". To credit a real person, add them to `AUTHORS` in `app/content.py` with their genuine experience, and set `author:` in a guide's front matter.
- **AI crawlers:** nothing is blocked by default. Add user agents to `BLOCKED_CRAWLERS` if you decide otherwise.

## Editing content

Guides, glossary terms, tool copy and trust pages are Markdown files in `content/`. Front matter controls the title tag, meta description, H1, direct answer, topic cluster, related links and dates. Update `updated:` only for substantive changes. Blog posts are written in the admin CMS and must pass the pre-publish SEO gate. AI-assisted posts also need a named human reviewer.

## Project layout

```
app/
  __init__.py        app factory, canonical host, redirects/410, headers, caching, gzip
  config.py          brand, domain, plans, thresholds, crawler policy
  seo.py schema.py   metadata, canonicals, robots, overrides, JSON-LD + validator
  linkgraph.py       page registry, related links, glossary auto-linking, link suggestions
  valuation.py       valuation engine (single source of truth)
  marketplace.py     listing lifecycle, quality, duplicates, indexation
  redirects.py       301s without chains, 410s, change logging
  audit.py           SEO QA crawler, quality score, change monitoring, publish gate
  analytics.py billing.py auth.py mailer.py storage.py backup.py
  views/             public, marketplace, account, admin, api, robots/sitemaps
  templates/ static/
content/             Markdown content
tests/               unit + integration + acceptance tests
```
