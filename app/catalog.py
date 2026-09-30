"""Structured catalog of tools, calculators and marketplace categories.

Long-form copy lives in content/*.md; this module holds the facts that other
parts of the system (routing, linking, sitemaps, schema) need.
"""

TOOLS = [
    dict(key="website", slug="website-valuation", name="Website Valuation Tool",
         meta_title="Website Valuation Tool – Estimate What Your Website Is Worth",
         description="Estimate a content, affiliate or ad-supported website's value from its profit, age, growth "
                     "and traffic risk. Free, with the full method shown.",
         short="Content, affiliate, ad and lead-gen sites",
         category="websites", guide="/guides/website-valuation/", calculator="/calculators/website-worth-calculator/",
         glossary=["sde", "profit-multiple", "traffic"]),
    dict(key="saas", slug="saas-valuation", name="SaaS Valuation Tool",
         meta_title="SaaS Valuation Tool – Estimate SaaS Business Value from ARR",
         description="Estimate a SaaS company's value from ARR, growth, churn, gross margin and customer "
                     "concentration. Free, with every assumption shown.",
         short="Subscription software businesses",
         category="saas", guide="/guides/saas-valuation/", calculator="/calculators/saas-valuation-calculator/",
         glossary=["arr", "mrr", "churn"]),
    dict(key="ai", slug="ai-business-valuation", name="AI Business Valuation Tool",
         meta_title="AI Business Valuation Tool – Value an AI Tool or AI SaaS",
         description="Estimate what an AI tool or AI SaaS business is worth, including the effect of gross margin "
                     "and dependence on third-party model providers.",
         short="AI tools, AI SaaS and API products",
         category="ai-businesses", guide="/guides/ai-business-valuation/", calculator="/calculators/saas-valuation-calculator/",
         glossary=["arr", "gross-margin", "churn"]),
    dict(key="app", slug="app-valuation", name="App Valuation Tool",
         meta_title="App Valuation Tool – Estimate Your Mobile App's Value",
         description="Estimate a mobile app's value from profit, revenue model, platforms, growth and "
                     "acquisition-channel risk. Free, with the method shown.",
         short="iOS and Android apps",
         category="apps", guide="/guides/business-valuation/", calculator="/calculators/business-multiple-calculator/",
         glossary=["sde", "profit-multiple", "churn"]),
    dict(key="newsletter", slug="newsletter-valuation", name="Newsletter Valuation Tool",
         meta_title="Newsletter Valuation Tool – Estimate What Your Newsletter Is Worth",
         description="Estimate a newsletter business's value from profit, subscriber engagement, revenue model "
                     "and sponsor concentration. Free, with the method shown.",
         short="Sponsored and paid newsletters",
         category="newsletters", guide="/guides/business-valuation/", calculator="/calculators/business-multiple-calculator/",
         glossary=["sde", "customer-concentration", "profit-multiple"]),
    dict(key="ecommerce", slug="ecommerce-valuation", name="Ecommerce Valuation Tool",
         meta_title="Ecommerce Valuation Tool – Estimate Your Online Store's Value",
         description="Estimate an ecommerce store's value from profit, fulfillment model, channel risk and "
                     "inventory. Free, with the method shown.",
         short="Online stores, DTC and Amazon brands",
         category="ecommerce", guide="/guides/business-valuation/", calculator="/calculators/business-multiple-calculator/",
         glossary=["sde", "customer-concentration", "conversion-rate"]),
]
TOOLS_BY_SLUG = {t["slug"]: t for t in TOOLS}
TOOLS_BY_KEY = {t["key"]: t for t in TOOLS}
for t in TOOLS:
    t["path"] = f"/tools/{t['slug']}/"

CALCULATORS = [
    dict(key="website_worth", slug="website-worth-calculator", name="Website Worth Calculator",
         meta_title="Website Worth Calculator – Monthly Profit × Multiple",
         description="Work out what a website could be worth by multiplying monthly profit by a months-of-profit "
                     "multiple, with a table of values at common multiples.",
         short="Monthly profit × months-of-profit multiple", cluster="website",
         tool="/tools/website-valuation/"),
    dict(key="saas_quick", slug="saas-valuation-calculator", name="SaaS Valuation Calculator",
         meta_title="SaaS Valuation Calculator – Quick ARR Multiple Estimate",
         description="A quick SaaS valuation from three numbers: MRR, growth and churn. Shows ARR, the adjusted ARR "
                     "multiple and a value range.",
         short="MRR, growth and churn → ARR multiple", cluster="saas",
         tool="/tools/saas-valuation/"),
    dict(key="business_multiple", slug="business-multiple-calculator", name="Business Multiple Calculator",
         meta_title="Business Multiple Calculator – Revenue & Profit Multiples",
         description="Turn an asking price into revenue and profit multiples, months of profit and payback period, "
                     "and compare it with VALUERAQ's default ranges.",
         short="Asking price → implied multiples and payback", cluster="buying",
         tool="/tools/website-valuation/"),
]
CALCS_BY_SLUG = {c["slug"]: c for c in CALCULATORS}
for c in CALCULATORS:
    c["path"] = f"/calculators/{c['slug']}/"

CATEGORIES = [
    dict(slug="websites", plural="websites", tool="website", name="Websites for Sale", singular="website",
         meta_title="Websites for Sale – Browse Online Businesses",
         description="Browse content, affiliate, ad-supported and lead-generation websites for sale, with asking "
                     "price, revenue, profit and age shown for every listing.",
         definition="A website for sale is an online business, usually a content, affiliate, advertising or "
                    "lead-generation site, offered with its domain, content, traffic and revenue streams."),
    dict(slug="saas", plural="SaaS businesses", tool="saas", name="SaaS Businesses for Sale", singular="SaaS business",
         meta_title="SaaS Businesses for Sale – Buy SaaS Companies",
         description="Browse SaaS businesses for sale with MRR, profit, churn and age listed. Filter by price and "
                     "revenue, and value any listing with the SaaS tool.",
         definition="A SaaS business for sale is a subscription software company offered with its code, customer "
                    "contracts and recurring revenue."),
    dict(slug="ai-businesses", plural="AI businesses", tool="ai", name="AI Businesses for Sale", singular="AI business",
         meta_title="AI Businesses for Sale – AI Tools & AI SaaS",
         description="Browse AI tools and AI SaaS businesses for sale. See revenue, profit, age and model-provider "
                     "details, and check value with the AI valuation tool.",
         definition="An AI business for sale is a product whose core function depends on machine-learning models, "
                    "such as an AI writing tool, an AI API product or an AI-powered SaaS."),
    dict(slug="apps", plural="apps", tool="app", name="Apps for Sale", singular="app",
         meta_title="Apps for Sale – Buy iOS & Android Apps",
         description="Browse iOS and Android apps for sale with revenue model, profit and active-user figures "
                     "provided by sellers. Value any app with the free tool.",
         definition="An app for sale is a mobile application offered with its source code, store listings, user "
                    "base and revenue."),
    dict(slug="newsletters", plural="newsletters", tool="newsletter", name="Newsletters for Sale", singular="newsletter",
         meta_title="Newsletters for Sale – Buy Email Newsletter Businesses",
         description="Browse newsletters for sale with subscriber counts, open rates, sponsorship and paid-"
                     "subscription revenue provided by sellers.",
         definition="A newsletter for sale is an email publication offered with its subscriber list, content "
                    "archive, brand and sponsor or subscription revenue."),
    dict(slug="ecommerce", plural="ecommerce businesses", tool="ecommerce", name="Ecommerce Businesses for Sale", singular="ecommerce business",
         meta_title="Ecommerce Businesses for Sale – Buy Online Stores",
         description="Browse ecommerce stores for sale, including DTC and marketplace brands, with revenue, "
                     "profit, fulfillment and inventory details from sellers.",
         definition="An ecommerce business for sale is an online store offered with its brand, product listings, "
                    "supplier relationships, customer data and usually its inventory."),
]
CATS_BY_SLUG = {c["slug"]: c for c in CATEGORIES}
CAT_BY_TOOL = {c["tool"]: c for c in CATEGORIES}
for c in CATEGORIES:
    c["path"] = f"/businesses-for-sale/{c['slug']}/"

BUSINESS_MODELS = {
    "websites": ["Affiliate content", "Display advertising", "Lead generation", "Digital products", "Mixed"],
    "saas": ["B2B SaaS", "B2C SaaS", "Plugin / extension", "API", "Marketplace SaaS"],
    "ai-businesses": ["AI SaaS", "AI API", "AI content tool", "AI agent / automation", "AI data product"],
    "apps": ["Subscriptions", "In-app purchases", "Advertising", "Paid download"],
    "newsletters": ["Sponsorships", "Paid subscriptions", "Mixed"],
    "ecommerce": ["DTC brand", "Amazon FBA", "Dropshipping", "Print on demand", "Wholesale / B2B"],
}

SORTS = {
    "newest": ("Newest", "published_at DESC"),
    "price_asc": ("Price: low to high", "asking_price ASC"),
    "price_desc": ("Price: high to low", "asking_price DESC"),
    "profit_desc": ("Profit: high to low", "monthly_profit DESC"),
}


def ucfirst(s):
    return s[:1].upper() + s[1:] if s else s
