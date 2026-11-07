"""Structured catalog of tools, calculators and marketplace categories.

Long-form copy lives in content/*.md; this module holds the facts that other
parts of the system (routing, linking, sitemaps, schema) need.
"""

TOOLS = [
    dict(key="website", slug="website-valuation", name="Website Valuation Tool",
         meta_title="Free Website Valuation Tool: Instant Value, No Sign-Up",
         description="Free: what is your website worth? Enter profit, age and traffic for a value range in about a minute, with every adjustment explained and a value table.",
         short="Content, affiliate, ad and lead-gen sites",
         category="websites", guide="/guides/website-valuation/", calculator="/calculators/website-worth-calculator/",
         glossary=["sde", "profit-multiple", "traffic"]),
    dict(key="saas", slug="saas-valuation", name="SaaS Valuation Tool",
         meta_title="Free SaaS Valuation Calculator: ARR Multiple, No Sign-Up",
         description="Free: value your SaaS from ARR, growth, churn and margin. See the ARR multiple, every adjustment and a value table from $60k to $1M ARR. No email needed.",
         short="Subscription software businesses",
         category="saas", guide="/guides/saas-valuation/", calculator="/calculators/saas-valuation-calculator/",
         glossary=["arr", "mrr", "churn"]),
    dict(key="ai", slug="ai-business-valuation", name="AI Business Valuation Tool",
         meta_title="Free AI Business Valuation: What Is Your AI Tool Worth?",
         description="Free: value an AI tool or AI SaaS from ARR, model costs and provider dependence. See why headline AI multiples don't apply and get a value range. No sign-up.",
         short="AI tools, AI SaaS and API products",
         category="ai-businesses", guide="/guides/ai-business-valuation/", calculator="/calculators/saas-valuation-calculator/",
         glossary=["arr", "gross-margin", "churn"]),
    dict(key="app", slug="app-valuation", name="App Valuation Tool",
         meta_title="Free App Valuation Calculator: What Is My App Worth?",
         description="Free: value your iOS or Android app from profit, revenue model and channel risk. Value table included, plus why buyers don't pay per user. No sign-up.",
         short="iOS and Android apps",
         category="apps", guide="/guides/business-valuation/", calculator="/calculators/business-multiple-calculator/",
         glossary=["sde", "profit-multiple", "churn"]),
    dict(key="newsletter", slug="newsletter-valuation", name="Newsletter Valuation Tool",
         meta_title="Free Newsletter Valuation Calculator: What's My List Worth?",
         description="Free: value your newsletter from profit, open rate, revenue model and sponsor mix. See a value table, a per-subscriber check and why open rates mislead.",
         short="Sponsored and paid newsletters",
         category="newsletters", guide="/guides/business-valuation/", calculator="/calculators/business-multiple-calculator/",
         glossary=["sde", "customer-concentration", "profit-multiple"]),
    dict(key="ecommerce", slug="ecommerce-valuation", name="Ecommerce Valuation Tool",
         meta_title="Free Ecommerce Valuation Calculator: Store Value + Stock",
         description="Free: value your Shopify, Amazon FBA or DTC store from profit, channels and fulfillment, with stock added at cost. Value table and model comparison included.",
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
         meta_title="Free Website Worth Calculator: Based on Profit, Not Guesses",
         description="Free: most website worth calculators guess from your domain name. This one uses your monthly profit, the number buyers pay for, and shows the range instantly.",
         short="Monthly profit × months-of-profit multiple", cluster="website",
         tool="/tools/website-valuation/"),
    dict(key="saas_quick", slug="saas-valuation-calculator", name="SaaS Valuation Calculator",
         meta_title="Free ARR Multiple Calculator: SaaS Value in 3 Inputs",
         description="Free: enter MRR, growth and churn to see ARR, the adjusted ARR multiple and a value range, plus a value table from $60k to $1M ARR and 5 ways to raise it.",
         short="MRR, growth and churn → ARR multiple", cluster="saas",
         tool="/tools/saas-valuation/"),
    dict(key="business_multiple", slug="business-multiple-calculator", name="Business Multiple Calculator",
         meta_title="Free Business Multiple Calculator: Is the Asking Price Fair?",
         description="Free: enter an asking price and profit or revenue to see the multiple and payback, then compare it with typical ranges for websites, SaaS, stores and apps.",
         short="Asking price → implied multiples and payback", cluster="buying",
         tool="/tools/website-valuation/"),
]
CALCS_BY_SLUG = {c["slug"]: c for c in CALCULATORS}
for c in CALCULATORS:
    c["path"] = f"/calculators/{c['slug']}/"

CATEGORIES = [
    dict(slug="websites", plural="websites", tool="website", name="Websites for Sale", singular="website",
         meta_title="Websites for Sale – Free Listing, No Commission",
         description="Browse content, affiliate, ad and lead-gen websites for sale with price, revenue, profit and age. Free to list, free to contact sellers, no commission.",
         definition="A website for sale is an online business, usually a content, affiliate, advertising or "
                    "lead-generation site, offered with its domain, content, traffic and revenue streams."),
    dict(slug="saas", plural="SaaS businesses", tool="saas", name="SaaS Businesses for Sale", singular="SaaS business",
         meta_title="SaaS Businesses for Sale – Free Listing, No Commission",
         description="Browse SaaS businesses for sale with MRR, profit, churn and age. Free to list, free to contact sellers, no commission. Check any price with the free tool.",
         definition="A SaaS business for sale is a subscription software company offered with its code, customer "
                    "contracts and recurring revenue."),
    dict(slug="ai-businesses", plural="AI businesses", tool="ai", name="AI Businesses for Sale", singular="AI business",
         meta_title="AI Businesses for Sale – Free Listing, No Commission",
         description="Browse AI tools and AI SaaS businesses for sale with revenue, profit and model details. Free to list, free to contact sellers, no commission on the sale.",
         definition="An AI business for sale is a product whose core function depends on machine-learning models, "
                    "such as an AI writing tool, an AI API product or an AI-powered SaaS."),
    dict(slug="apps", plural="apps", tool="app", name="Apps for Sale", singular="app",
         meta_title="Apps for Sale: iOS & Android – Free Listing, No Commission",
         description="Browse iOS and Android apps for sale with revenue model, profit and users. Free to list, free to contact sellers, no commission on the sale.",
         definition="An app for sale is a mobile application offered with its source code, store listings, user "
                    "base and revenue."),
    dict(slug="newsletters", plural="newsletters", tool="newsletter", name="Newsletters for Sale", singular="newsletter",
         meta_title="Newsletters for Sale – Free Listing, No Commission",
         description="Browse newsletters for sale with subscribers, open rates and sponsor revenue. Free to list, free to contact sellers, no commission on the sale.",
         definition="A newsletter for sale is an email publication offered with its subscriber list, content "
                    "archive, brand and sponsor or subscription revenue."),
    dict(slug="ecommerce", plural="ecommerce businesses", tool="ecommerce", name="Ecommerce Businesses for Sale", singular="ecommerce business",
         meta_title="Ecommerce Stores for Sale – Free Listing, No Commission",
         description="Browse Shopify, Amazon FBA and DTC stores for sale with revenue, profit and stock. Free to list, free to contact sellers, no commission on the sale.",
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
