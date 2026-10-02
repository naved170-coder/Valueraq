# VALUERAQ — SEO-Aware Technical Architecture

Digital Business Intelligence + Marketplace platform.
Preferred domain: `https://www.valueraq.com` (apex `valueraq.com` and any other host 301 → www).
Language: English (US) · Primary market: United States · Default currency: USD.

This document answers §91 of the SEO specification, items 1–15, before implementation.
No product-development specification was supplied, so product scope is derived from the SEO
specification itself (tools, calculators, reports, accounts, trial, subscription, marketplace).

---

## 1. Analysis summary

The site has two conversion flywheels that must share one topical graph:

| Flywheel | Path |
|---|---|
| Tools | search → guide → free tool → valuation result → detailed report → free account → 14-day trial → Pro |
| Marketplace | search → category page → listing → buyer inquiry · seller signup → listing → featured listing |

Guides feed tools and categories. Tools feed accounts. Listings feed categories. Categories link
back to the matching tool and guide. Every public page belongs to exactly one topic cluster.

## 2–4. Product UX vs SEO conflicts and how they are resolved

| Conflict | Resolution |
|---|---|
| Calculators are interactive, but search engines and LLMs need text | Every tool page is server-rendered HTML: definition, inputs, method, worked example, limitations, FAQ. The form is a small progressive-enhancement island. It works without JavaScript (POST → server-rendered, `noindex` result). |
| Personalized valuation results are useful to users but must never be indexed | Results render inline; saved reports live at `/reports/private/<random-token>/` behind login, with `X-Robots-Tag: noindex, nofollow`, and the path is disallowed in robots.txt. |
| Marketplace filters are useful but create unbounded URLs | Filters and sort use query parameters. Any parameter makes the page `noindex, follow` with a canonical pointing at the clean category URL. Pagination uses path URLs (`/page/2/`), is self-canonical and indexable, and pages past the last one return 404. |
| An empty marketplace at launch would produce thin category pages | Category pages carry real buying/valuation guidance, metrics definitions and FAQs, so they're useful without inventory. **No listings are fabricated.** |
| Blog with zero posts | `/blog/` is `noindex` and left out of sitemaps until at least one post is published. |
| Premium gating vs crawlable methodology | Methodology, formulas, default multiples and limitations are fully public. Only per-user extras (saved reports, sensitivity tables) are gated. |
| Signup walls | No interstitials. Detailed report requires a free account; the headline estimate never does. |
| Seven valuation topics × (tool + guide) risks duplicate intent | Pillar guides exist only where the informational intent differs from the tool's commercial intent (website, SaaS, AI, general business valuation). App, newsletter and ecommerce valuation are covered in depth on their tool pages rather than split into near-duplicate guide pages. |

Stack decision: Python 3.11 + Flask + Jinja2 + SQLite (WAL). All public pages are server-rendered
HTML with no client framework. JavaScript on content pages is limited to a <2 KB analytics/web-vitals
beacon. Calculator pages add one small script. Chosen because it is fully SSR, has few dependencies,
and could be built and tested end-to-end in the build environment. SQLite runs on a persistent disk
(Render/Railway/Fly/VPS). The DB layer is isolated in `app/db.py` for a later Postgres move.

## 5. SEO-aware technical architecture

```
request
  └─ before_request
       ├─ host canonicalisation (→ https://www.valueraq.com, 301)
       ├─ trailing-slash + lowercase normalisation (301)
       ├─ redirect table lookup (cached, chain-collapsed, 301)
       └─ gone table lookup (410)
  └─ route → view builds a PageMeta (title, description, canonical, robots, h1, og, schema, breadcrumbs)
       └─ SEO overrides (admin, DB) merged on top of code defaults
  └─ Jinja render (semantic HTML, one H1, JSON-LD, breadcrumbs, related links from the link graph)
  └─ after_request
       ├─ X-Robots-Tag for private areas and noindex pages
       ├─ security headers (CSP, HSTS, nosniff, referrer policy)
       ├─ cache headers (public pages: s-maxage; private: no-store)
       └─ gzip
```

Modules:

| Module | Responsibility |
|---|---|
| `app/config.py` | Brand, domain, locale, currency, plans, crawler policy, feature flags |
| `app/db.py` | Schema, migrations, query helpers |
| `app/seo.py` | PageMeta, canonical builder, robots directives, overrides, breadcrumbs |
| `app/schema.py` | JSON-LD builders and validator |
| `app/linkgraph.py` | Topic clusters and the internal linking engine |
| `app/valuation.py` | Valuation engine (single source of truth for all tools/calculators) |
| `app/content.py` | Markdown content loader (guides, glossary, trust pages) with front matter |
| `app/marketplace.py` | Listing lifecycle, quality checks, duplicate detection, indexation rules |
| `app/auth.py`, `app/billing.py` | Accounts, CSRF, rate limits, trial, Stripe |
| `app/analytics.py` | First-party events, organic attribution, funnels, web-vitals |
| `app/audit.py` | SEO QA crawler, quality score, orphan detection, change monitoring |
| `app/views/*` | Public, marketplace, account, admin, API, sitemap/robots routes |

## 6. URL architecture

All HTML URLs are lowercase with a trailing slash. No IDs except the listing suffix, which prevents
slug collisions between similar businesses.

| URL | Purpose | Index |
|---|---|---|
| `/` | Home | yes |
| `/tools/` | Tools hub | yes |
| `/tools/{website,saas,ai-business,app,newsletter,ecommerce}-valuation/` | Tool landing + tool | yes |
| `/calculators/` | Calculators hub | yes |
| `/calculators/website-worth-calculator/` | Profit × multiple calculator | yes |
| `/calculators/saas-valuation-calculator/` | ARR × multiple calculator | yes |
| `/calculators/business-multiple-calculator/` | Implied multiple from asking price | yes |
| `/businesses-for-sale/` | Marketplace hub by category | yes |
| `/businesses-for-sale/{websites,saas,ai-businesses,apps,newsletters,ecommerce}/` | Category landing | yes |
| `/businesses-for-sale/{cat}/page/{n}/` | Pagination | yes, only if n ≤ last page |
| `/businesses-for-sale/{cat}/?sort=…&price_max=…` | Filters | noindex, follow; canonical → category |
| `/marketplace/` | All live listings, newest first | yes |
| `/marketplace/{cat}/{slug}-{id}/` | Listing | yes only if it passes the indexation rules (§13) |
| `/guides/` · `/guides/{slug}/` | Pillar and cluster guides | yes |
| `/glossary/` · `/glossary/{term}/` | Knowledge base | yes |
| `/blog/` · `/blog/{slug}/` | Editorial posts (DB-backed) | yes once published |
| `/about/ /methodology/ /data-sources/ /pricing/ /faq/ /contact/` | Entity and trust pages | yes |
| `/editorial-policy/ /verification/ /marketplace-rules/ /privacy/ /terms/` | Trust/legal | yes |
| `/search/?q=` | Site search | noindex, follow |
| `/sell/`, `/login/`, `/signup/` | Forms | noindex |
| `/account/…`, `/reports/private/…`, `/checkout/…`, `/admin/…`, `/api/…` | Private | noindex + robots Disallow + auth |

## 7. Content and topic architecture

| Cluster | Commercial page | Informational pages | Marketplace |
|---|---|---|---|
| Website valuation | `/tools/website-valuation/`, `/calculators/website-worth-calculator/` | `/guides/website-valuation/`, `/guides/revenue-vs-profit-multiples/`, `/guides/digital-business-due-diligence/` | `/businesses-for-sale/websites/` |
| SaaS valuation | `/tools/saas-valuation/`, `/calculators/saas-valuation-calculator/` | `/guides/saas-valuation/`, glossary ARR, MRR, churn, LTV, CAC | `/businesses-for-sale/saas/` |
| AI business valuation | `/tools/ai-business-valuation/` | `/guides/ai-business-valuation/` | `/businesses-for-sale/ai-businesses/` |
| App, newsletter, ecommerce | respective tools (in-depth pages) | glossary terms, due-diligence guide | respective categories |
| Buying | `/businesses-for-sale/` | `/guides/buying-digital-businesses/`, due diligence | all categories |
| Selling | `/sell/` | `/guides/selling-digital-businesses/` | `/marketplace/` |
| Financial analysis | `/calculators/business-multiple-calculator/` | `/guides/business-valuation/`, comparisons, glossary | — |

Comparison pages (§48) at launch: website vs SaaS valuation; revenue vs profit multiples.
Glossary at launch (§63): ARR, MRR, EBITDA, SDE, revenue multiple, profit multiple, churn, CAC,
LTV, traffic, conversion rate, customer concentration, SaaS, marketplace, digital business,
due diligence.

## 8. Database SEO fields

SEO metadata is stored separately from business data (`seo_overrides`, keyed by path) so admins can
override without touching content. Listings and blog posts also carry their own SEO columns.

```
seo_overrides(path PK, meta_title, meta_description, h1, canonical_url, robots_directive,
              og_title, og_description, og_image, schema_extra, indexable, sitemap_included,
              updated_at, updated_by)
seo_change_log(id, path, field, old_value, new_value, changed_by, changed_at, reason)
redirects(id, from_path UNIQUE, to_path, status 301|308, created_at, reason)
gone_urls(path PK, reason, created_at)                      -- 410
listings(… slug, meta_title, meta_description, indexable, sitemap_included, published_at,
         updated_at, quality_score, quality_flags, content_hash, status …)
blog_posts(… slug, meta_title, meta_description, canonical_url, robots_directive, og_image,
           indexable, sitemap_included, published_at, updated_at, reviewed_by, …)
keywords(id, keyword, intent, target_path, search_volume, difficulty, cpc, source, source_date)
                                                           -- metrics NULL unless imported
search_performance(path, query, clicks, impressions, ctr, position, period_start, period_end, source)
seo_audit_runs / seo_audit_pages                           -- QA snapshots for change monitoring
```

Guides and glossary are Markdown files with front matter (`title, meta_title, meta_description,
h1, cluster, primary_intent, primary_question, related, published, updated, reviewed,
methodology_version`), versioned in git.

## 9. Sitemap architecture

`/sitemap.xml` is a sitemap index listing only non-empty children:

| File | Contents |
|---|---|
| `/sitemap-pages.xml` | Home, hubs, trust and legal pages |
| `/sitemap-tools.xml` | Tools and calculators |
| `/sitemap-guides.xml` | Guides and glossary |
| `/sitemap-blog.xml` | Published, indexable posts |
| `/sitemap-categories.xml` | Category pages and existing pagination pages |
| `/sitemap-listings.xml` | Indexable listings only (split at 45,000 URLs) |

A single `is_indexable(path)` resolver decides inclusion, so sitemaps, meta robots and the audit
can't disagree. `lastmod` comes only from real content changes (front-matter `updated`, DB
`updated_at`), never from the request time.

## 10. Structured data architecture

| Page | JSON-LD |
|---|---|
| All | `Organization` + `WebSite` (sitewide `@id` graph) |
| Hierarchical pages | `BreadcrumbList` matching the visible breadcrumbs |
| Tools, calculators | `WebApplication` (free `Offer`, no ratings) |
| Guides, blog | `Article` with author, `datePublished`, `dateModified` |
| Glossary term | `DefinedTerm` in a `DefinedTermSet` |
| Category, hubs | `CollectionPage` + `ItemList` of visible items |
| Listing | `Product` + `Offer` built only from seller-provided fields that are shown on the page |
| FAQ page | `FAQPage` (visible Q&A only) |
| About / Contact | `AboutPage` / `ContactPage` |

Never emitted: `Review`, `AggregateRating` (no genuine review system yet), `Dataset` (no
proprietary dataset yet). `app/schema.py` validates required properties per type in tests and in
the admin audit.

## 11. Internal linking architecture

`app/linkgraph.py` defines clusters and typed relations (tool ↔ guide ↔ category ↔ glossary).
Every page template renders:

1. Contextual in-body links written into content.
2. A "Related" block generated from the graph (tools, guides, categories; capped, no duplicates of
   in-body links).
3. Breadcrumbs.
4. Glossary auto-linking: first mention only, maximum 3 per page, never inside headings.

New blog posts get suggested links (tools, guides, categories, glossary terms), scored by term
overlap, for the editor to accept; nothing is auto-inserted. The audit flags orphans (zero
inbound internal links) and weakly linked pages (fewer than 3 inbound links).

## 12. Programmatic SEO rules

- Programmatic pages come only from real rows: listings, categories with a definition, and paginated
  pages that exist.
- No location pages, keyword-permutation pages or filter-combination landing pages at launch.
- A curated filter landing page may be promoted to indexable only by adding it to
  `INDEXABLE_COLLECTIONS` with unique intro copy **and** at least 6 live listings.
- Page-generation gate (§73) is part of the blog/admin publish checklist.

## 13. Marketplace indexation rules

Listing states: `draft → pending → published → sold | removed`, plus `rejected`, `suspended`.

A listing is indexable only when **all** hold:
- status `published`, not a test listing, not suspended;
- passes quality checks: description ≥ 120 words, required facts present (type, asking price,
  revenue, profit, age, business model), quality score ≥ 60, no spam flags;
- not a near-duplicate (shingle Jaccard ≥ 0.8) of another live listing.

| Case | Response |
|---|---|
| Draft / pending / rejected / private | 404 to the public, visible to owner and admin with noindex |
| Published but thin | 200, `noindex, follow`, not in sitemap |
| Sold | 200 with "Sold" notice, `noindex, follow`, removed from sitemap |
| Removed with legitimate replacement | 301 to the replacement (set by admin) |
| Removed, spam or deleted without replacement | 410 with helpful links |
| Slug changed | 301 old → new, chain-collapsed, logged |

UGC safety: descriptions are plain text (no HTML), URLs are rendered as text, and any rendered link
gets `rel="ugc nofollow noopener"`. Checks cover link count, keyword stuffing, all-caps, repetition,
banned phrases and duplicate detection. Honeypot fields, rate limits and CSRF protect all forms.

## 14. LLM discoverability architecture

- All facts are in HTML text or HTML tables. Charts and ranges always have a text equivalent.
- Guides follow the §78 template where it fits: direct answer, key takeaway, explanation, how it
  works, example, factors, limitations, FAQ, related tools/guides.
- Every major concept has a one-sentence definition sentence, reused consistently sitewide.
- Methodology, default multiples, adjustments, assumptions and limitations are public and versioned
  (`methodology v1.0`). The data-sources page states plainly which values are editorial assumptions
  and that no third-party dataset is licensed yet.
- Results label every figure as **user-provided**, **platform assumption** or **calculated**.
- Crawler access is configurable (`CRAWLER_POLICY`), and no named AI crawler is blocked by default.
- Nothing hidden, no prompt-like text, no fake citations.

## 15. SEO QA system

- **Pre-publish gate** (blog posts, listings, SEO overrides): unique title/description, one H1,
  canonical valid, robots correct, minimum unique content, internal links present, alt text. Critical
  failures block publishing.
- **Audit crawler** (`/admin/seo/` and `python -m app.audit`) renders every sitemap URL plus known
  private URLs in-process and checks: status, title/description presence and uniqueness, canonical,
  H1 count, robots and sitemap consistency, JSON-LD parse and validation, broken internal links,
  redirect chains, orphan and weakly-linked pages, thin pages, missing alt text, HTML weight and
  render time, and changes since the last run (titles, canonicals, robots, schema, sitemap URLs).
- **Page quality score** (internal only, not a ranking prediction): technical 30, content 25,
  linking 20, schema 10, performance 15.
- **Field data**: a tiny first-party beacon records LCP, CLS and INP per template.
- **Automated tests** cover the pre-launch acceptance checklist (§81).
