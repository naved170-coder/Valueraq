"""Structured catalog of tools, calculators and marketplace categories.

Long-form copy lives in content/*.md; this module holds the facts that other
parts of the system (routing, linking, sitemaps, schema) need.
"""

TOOLS = [
    dict(key="website", slug="website-valuation", name="Website Valuation Tool",
         meta_title="Website Valuation Tool: What Is My Site Worth? (Free)",
         description="Find out what your website is worth in about a minute. Enter profit, age and traffic; get a value range with every adjustment shown. Free, no sign-up.",
         short="Content, affiliate, ad and lead-gen sites",
         category="websites", guide="/guides/website-valuation/", calculator="/calculators/website-worth-calculator/",
         glossary=["sde", "profit-multiple", "traffic"]),
    dict(key="saas", slug="saas-valuation", name="SaaS Valuation Tool",
         meta_title="SaaS Valuation Calculator: Value Your SaaS by ARR (Free)",
         description="Value your SaaS in about a minute from ARR, growth, churn and margin. See the ARR multiple and a value range with every assumption shown. Free, no sign-up.",
         short="Subscription software businesses",
         category="saas", guide="/guides/saas-valuation/", calculator="/calculators/saas-valuation-calculator/",
         glossary=["arr", "mrr", "churn"]),
    dict(key="ai", slug="ai-business-valuation", name="AI Business Valuation Tool",
         meta_title="AI Business Valuation Tool: Value an AI SaaS (Free)",
         description="What is your AI tool or AI SaaS worth? Enter ARR, growth, margin and model dependence to get a value range with the method shown. Free, no sign-up.",
         short="AI tools, AI SaaS and API products",
         category="ai-businesses", guide="/guides/ai-business-valuation/", calculator="/calculators/saas-valuation-calculator/",
         glossary=["arr", "gross-margin", "churn"]),
    dict(key="app", slug="app-valuation", name="App Valuation Tool",
         meta_title="App Valuation Calculator: What Is My App Worth? (Free)",
         description="Estimate your iOS or Android app's value from profit, revenue model, growth and channel risk. Get a value range in about a minute. Free, no sign-up.",
         short="iOS and Android apps",
         category="apps", guide="/guides/business-valuation/", calculator="/calculators/business-multiple-calculator/",
         glossary=["sde", "profit-multiple", "churn"]),
    dict(key="newsletter", slug="newsletter-valuation", name="Newsletter Valuation Tool",
         meta_title="Newsletter Valuation Tool: What Is My Newsletter Worth?",
         description="Value your newsletter from profit, open rate, revenue model and sponsor mix. Get a value range with each adjustment explained. Free, no sign-up needed.",
         short="Sponsored and paid newsletters",
         category="newsletters", guide="/guides/business-valuation/", calculator="/calculators/business-multiple-calculator/",
         glossary=["sde", "customer-concentration", "profit-multiple"]),
    dict(key="ecommerce", slug="ecommerce-valuation", name="Ecommerce Valuation Tool",
         meta_title="Ecommerce Valuation Tool: What Is My Store Worth? (Free)",
         description="Value your Shopify, Amazon or DTC store from profit, fulfillment model, channels and stock. Get a value range in about a minute. Free, no sign-up.",
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
         meta_title="Website Worth Calculator: Profit × Multiple (Free)",
         description="How much is my website worth? Enter monthly profit and see values at common multiples, plus the range most small sites sell for. Free and instant.",
         short="Monthly profit × months-of-profit multiple", cluster="website",
         tool="/tools/website-valuation/"),
    dict(key="saas_quick", slug="saas-valuation-calculator", name="SaaS Valuation Calculator",
         meta_title="ARR Multiple Calculator: Quick SaaS Value in 3 Inputs",
         description="Enter MRR, growth and churn to see your ARR, the adjusted ARR multiple and a value range. A quick, free SaaS valuation with the maths shown.",
         short="MRR, growth and churn → ARR multiple", cluster="saas",
         tool="/tools/saas-valuation/"),
    dict(key="business_multiple", slug="business-multiple-calculator", name="Business Multiple Calculator",
         meta_title="Business Multiple Calculator: Is the Asking Price Fair?",
         description="Enter an asking price and profit to see the revenue and profit multiples, months of profit and payback period, compared with typical ranges. Free.",
         short="Asking price → implied multiples and payback", cluster="buying",
         tool="/tools/website-valuation/"),
]
CALCS_BY_SLUG = {c["slug"]: c for c in CALCULATORS}
for c in CALCULATORS:
    c["path"] = f"/calculators/{c['slug']}/"

CATEGORIES = [
    dict(slug="websites", plural="websites", tool="website", name="Websites for Sale", singular="website",
         meta_title="Websites for Sale: Buy an Established Website",
         description="Browse content, affiliate, ad and lead-gen websites for sale. Every listing shows asking price, revenue, profit and age, plus a free value check.",
         definition="A website for sale is an online business, usually a content, affiliate, advertising or "
                    "lead-generation site, offered with its domain, content, traffic and revenue streams."),
    dict(slug="saas", plural="SaaS businesses", tool="saas", name="SaaS Businesses for Sale", singular="SaaS business",
         meta_title="SaaS Businesses for Sale: Buy a SaaS Company",
         description="Browse SaaS businesses for sale with MRR, profit, churn and age listed. Filter by price and check any listing's value with the free SaaS tool.",
         definition="A SaaS business for sale is a subscription software company offered with its code, customer "
                    "contracts and recurring revenue."),
    dict(slug="ai-businesses", plural="AI businesses", tool="ai", name="AI Businesses for Sale", singular="AI business",
         meta_title="AI Businesses for Sale: Buy an AI Tool or AI SaaS",
         description="Browse AI tools and AI SaaS businesses for sale with revenue, profit, age and model-provider details. Check any listing's value with the free tool.",
         definition="An AI business for sale is a product whose core function depends on machine-learning models, "
                    "such as an AI writing tool, an AI API product or an AI-powered SaaS."),
    dict(slug="apps", plural="apps", tool="app", name="Apps for Sale", singular="app",
         meta_title="Apps for Sale: Buy an iOS or Android App",
         description="Browse iOS and Android apps for sale with revenue model, profit and users listed by sellers. Check any app's value with the free valuation tool.",
         definition="An app for sale is a mobile application offered with its source code, store listings, user "
                    "base and revenue."),
    dict(slug="newsletters", plural="newsletters", tool="newsletter", name="Newsletters for Sale", singular="newsletter",
         meta_title="Newsletters for Sale: Buy an Email Newsletter Business",
         description="Browse newsletters for sale with subscribers, open rates and sponsor or paid revenue listed. Check any newsletter's value with the free tool.",
         definition="A newsletter for sale is an email publication offered with its subscriber list, content "
                    "archive, brand and sponsor or subscription revenue."),
    dict(slug="ecommerce", plural="ecommerce businesses", tool="ecommerce", name="Ecommerce Businesses for Sale", singular="ecommerce business",
         meta_title="Ecommerce Businesses for Sale: Buy an Online Store",
         description="Browse Shopify, Amazon FBA and DTC stores for sale with revenue, profit and stock details. Check any store's value with the free valuation tool.",
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
