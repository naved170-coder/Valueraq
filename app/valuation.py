"""VALUERAQ valuation engine — methodology v1.0.

Single source of truth for every tool and calculator. Pure functions, no I/O.

Every number in a result is labelled as one of:
  user-provided · platform assumption · calculated

IMPORTANT: the base multiple ranges below are VALUERAQ editorial default
assumptions. They are not derived from a measured transaction dataset. They are
published on /methodology/ and /data-sources/ and should be replaced by sourced
figures when a licensed or proprietary dataset exists.
"""
from __future__ import annotations

METHODOLOGY_VERSION = "1.0"
METHODOLOGY_DATE = "2026-09-30"

# --------------------------------------------------------------------------
# Business types and their default base multiples (platform assumptions)
# --------------------------------------------------------------------------
BASE = {
    "website":    {"method": "profit", "low": 2.5, "mid": 3.2, "high": 4.0},
    "ecommerce":  {"method": "profit", "low": 2.0, "mid": 2.7, "high": 3.5},
    "newsletter": {"method": "profit", "low": 2.5, "mid": 3.2, "high": 4.0},
    "app":        {"method": "profit", "low": 2.0, "mid": 2.7, "high": 3.5},
    "saas":       {"method": "arr",    "low": 2.0, "mid": 3.5, "high": 5.0},
    "ai":         {"method": "arr",    "low": 1.5, "mid": 3.0, "high": 4.5},
}

TYPE_LABEL = {
    "website": "Website", "ecommerce": "Ecommerce business", "newsletter": "Newsletter",
    "app": "Mobile app", "saas": "SaaS business", "ai": "AI business",
}

TYPE_NOUN = {  # for use mid-sentence
    "website": "website", "ecommerce": "ecommerce business", "newsletter": "newsletter",
    "app": "mobile app", "saas": "SaaS business", "ai": "AI business",
}

ADJ_FLOOR, ADJ_CEIL = 0.5, 1.4

# --------------------------------------------------------------------------
# Input definitions (drive forms, validation and the methodology tables)
# --------------------------------------------------------------------------
F = {
    "monthly_revenue": dict(label="Average monthly revenue", kind="money",
                            help="Average of the last 12 months, before expenses."),
    "monthly_profit": dict(label="Average monthly net profit (SDE)", kind="money", allow_negative=True,
                           help="Revenue minus all costs, before paying yourself. Average of the last 12 months."),
    "mrr": dict(label="Monthly recurring revenue (MRR)", kind="money",
                help="Current MRR from active subscriptions. Exclude one-off fees."),
    "age_years": dict(label="Business age (years)", kind="number", step="0.5",
                      help="Time since the business first earned revenue."),
    "growth_pct": dict(label="Revenue change, last 12 months (%)", kind="percent", allow_negative=True,
                       help="Compare the latest 3 months with the same 3 months a year earlier. Use a negative number for decline."),
    "owner_hours": dict(label="Owner hours per week", kind="number",
                        help="Hours you personally spend running the business each week."),
    "top_channel_pct": dict(label="Share of traffic or sales from the largest channel (%)", kind="percent",
                            help="For example, the share of visits from Google organic search, or of sales from one marketplace."),
    "top_customer_pct": dict(label="Largest customer's share of revenue (%)", kind="percent",
                             help="Leave at 0 for consumer businesses with many small customers."),
    "monthly_churn": dict(label="Monthly customer churn (%)", kind="percent",
                          help="Share of paying customers who cancel in an average month."),
    "gross_margin": dict(label="Gross margin (%)", kind="percent",
                         help="(Revenue − direct costs such as hosting, model/API usage and payment fees) ÷ revenue."),
    "model_dependency": dict(label="AI model dependency", kind="select", options=[
        ("single", "Relies on one third-party model provider"),
        ("multi", "Can switch between several providers"),
        ("own", "Runs own or fine-tuned models it controls"),
    ], help="How exposed the product is to one provider's pricing or policy changes."),
    "monetization": dict(label="Main monetization", kind="select", options=[
        ("display", "Display advertising"), ("affiliate", "Affiliate commissions"),
        ("leadgen", "Lead generation"), ("products", "Own digital products"), ("mixed", "Mixed (no source over 60%)"),
    ]),
    "monthly_pageviews": dict(label="Monthly pageviews", kind="number", optional=True,
                              help="From your analytics. Shown in the report; value is driven by profit."),
    "platform": dict(label="Platforms", kind="select", options=[
        ("ios", "iOS only"), ("android", "Android only"), ("both", "iOS and Android")]),
    "app_model": dict(label="Revenue model", kind="select", options=[
        ("subscription", "Subscriptions"), ("iap", "In-app purchases"),
        ("ads", "Advertising"), ("paid", "Paid download")]),
    "mau": dict(label="Monthly active users", kind="number", optional=True),
    "subscribers": dict(label="Subscribers", kind="number", optional=True),
    "open_rate": dict(label="Average open rate (%)", kind="percent",
                      help="Use the last 90 days. Apple Mail Privacy Protection inflates opens; say so in your listing if relevant."),
    "newsletter_model": dict(label="Revenue model", kind="select", options=[
        ("sponsorship", "Sponsorships and ads"), ("paid", "Paid subscriptions"), ("mixed", "Mixed")]),
    "inventory_value": dict(label="Inventory value at cost", kind="money", optional=True,
                            help="Sellable stock valued at what you paid. Usually added on top of the earnings-based price."),
    "fulfillment": dict(label="Fulfillment", kind="select", options=[
        ("own", "Own warehouse"), ("3pl", "Third-party logistics (3PL)"), ("dropship", "Dropshipping")]),
}

TOOL_INPUTS = {
    "website": ["monthly_revenue", "monthly_profit", "age_years", "growth_pct", "monetization",
                "top_channel_pct", "owner_hours", "monthly_pageviews"],
    "saas": ["mrr", "monthly_profit", "growth_pct", "monthly_churn", "gross_margin",
             "top_customer_pct", "age_years", "owner_hours"],
    "ai": ["mrr", "monthly_profit", "growth_pct", "monthly_churn", "gross_margin",
           "model_dependency", "top_customer_pct", "age_years", "owner_hours"],
    "app": ["monthly_revenue", "monthly_profit", "age_years", "growth_pct", "platform", "app_model",
            "top_channel_pct", "owner_hours", "mau"],
    "newsletter": ["monthly_revenue", "monthly_profit", "subscribers", "open_rate", "newsletter_model",
                   "growth_pct", "age_years", "owner_hours", "top_customer_pct"],
    "ecommerce": ["monthly_revenue", "monthly_profit", "inventory_value", "fulfillment", "growth_pct",
                  "top_channel_pct", "age_years", "owner_hours"],
}

REQUIRED = {
    "website": ["monthly_revenue", "monthly_profit"],
    "ecommerce": ["monthly_revenue", "monthly_profit"],
    "newsletter": ["monthly_revenue", "monthly_profit"],
    "app": ["monthly_revenue", "monthly_profit"],
    "saas": ["mrr"],
    "ai": ["mrr"],
}

# Example inputs shown pre-filled on tool pages. Clearly labelled as a
# hypothetical example in the UI, never presented as real data.
EXAMPLES = {
    "website": dict(monthly_revenue=6000, monthly_profit=4500, age_years=4, growth_pct=10,
                    monetization="affiliate", top_channel_pct=70, owner_hours=10, monthly_pageviews=180000),
    "saas": dict(mrr=20000, monthly_profit=9000, growth_pct=30, monthly_churn=3, gross_margin=82,
                 top_customer_pct=8, age_years=3, owner_hours=25),
    "ai": dict(mrr=12000, monthly_profit=4000, growth_pct=60, monthly_churn=6, gross_margin=62,
               model_dependency="single", top_customer_pct=5, age_years=1.5, owner_hours=30),
    "app": dict(monthly_revenue=9000, monthly_profit=5500, age_years=3, growth_pct=5, platform="both",
                app_model="subscription", top_channel_pct=65, owner_hours=12, mau=40000),
    "newsletter": dict(monthly_revenue=7000, monthly_profit=6000, subscribers=45000, open_rate=42,
                       newsletter_model="sponsorship", growth_pct=15, age_years=3, owner_hours=15,
                       top_customer_pct=20),
    "ecommerce": dict(monthly_revenue=40000, monthly_profit=7000, inventory_value=35000, fulfillment="3pl",
                      growth_pct=8, top_channel_pct=55, age_years=5, owner_hours=25),
}


class ValuationError(ValueError):
    pass


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------
def _num(raw):
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().replace(",", "").replace("$", "").replace("%", "")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        raise ValuationError("Enter numbers only, for example 4500.")


MIX_THRESHOLD = 0.60  # one source above this share of revenue is the "main" monetization


def combine_revenue_sources(types, amounts):
    """Rows of (monetization type, monthly revenue) from the Website tool.
    Returns (total, main_type, summary_text, errors). Blank rows are ignored."""
    allowed = dict(F["monetization"]["options"])
    rows, errors = [], {}
    for t, a in zip(types, amounts):
        t = (t or "").strip()
        try:
            v = _num(a)
        except ValuationError as e:
            errors["monthly_revenue"] = str(e)
            continue
        if not t and not v:
            continue
        if t and (t not in allowed or t == "mixed"):
            errors["monetization"] = "Choose one of the listed sources."
            continue
        if v is not None and v < 0:
            errors["monthly_revenue"] = "Revenue can't be negative."
            continue
        rows.append((t, v or 0.0))
    total = sum(v for _, v in rows)
    by_type = {}
    for t, v in rows:
        by_type[t] = by_type.get(t, 0.0) + v
    main = None
    typed = {t: v for t, v in by_type.items() if t}
    if typed and total > 0:
        top, top_v = max(typed.items(), key=lambda kv: kv[1])
        main = top if (top_v / total > MIX_THRESHOLD or len(typed) == 1) else "mixed"
    summary = "; ".join(f"{allowed.get(t, 'Unspecified')} ${v:,.0f}" for t, v in rows) if len(rows) > 1 else None
    return total, main, summary, errors


def parse_inputs(tool, form):
    if tool not in TOOL_INPUTS:
        raise ValuationError("Unknown tool.")
    out, errors = {}, {}
    summary = None
    if tool == "website" and hasattr(form, "getlist") and form.getlist("src_amount"):
        total, main, summary, errors = combine_revenue_sources(form.getlist("src_type"), form.getlist("src_amount"))
        form = {k: form.get(k) for k in form.keys()}
        form["monthly_revenue"] = str(total) if total else ""
        form["monetization"] = main or ""
    for key in TOOL_INPUTS[tool]:
        spec = F[key]
        raw = form.get(key)
        if spec["kind"] == "select":
            allowed = [o[0] for o in spec["options"]]
            val = (raw or "").strip()
            if val and val not in allowed:
                errors[key] = "Choose one of the listed options."
            out[key] = val or None
            continue
        try:
            val = _num(raw)
        except ValuationError as e:
            errors[key] = str(e)
            continue
        if val is not None:
            if val < 0 and not spec.get("allow_negative"):
                errors[key] = "This value can't be negative."
            if spec["kind"] == "percent" and not (-100 <= val <= 1000):
                errors[key] = "Enter a percentage between -100 and 1000."
            if spec["kind"] == "money" and abs(val) > 1e10:
                errors[key] = "That figure is too large to value here."
        out[key] = val
    for key in REQUIRED[tool]:
        if out.get(key) in (None, 0) and key not in errors:
            errors[key] = "Required."
    if errors:
        err = ValuationError("Please check the highlighted fields.")
        err.fields = errors
        raise err
    if summary:
        out["revenue_sources"] = summary
    return out


# --------------------------------------------------------------------------
# Adjustment rules — each returns (effect, reason) or None
# --------------------------------------------------------------------------
def display_value(key, v):
    if v is None:
        return None
    spec = F[key]
    if spec["kind"] == "select":
        return dict(spec["options"]).get(v, v)
    if spec["kind"] == "percent":
        return f"{v:g}%"
    if spec["kind"] == "money":
        return f"${v:,.0f}"
    return f"{v:g}"


def _num_rule(factor, key, tools, bands):
    return dict(factor=factor, input=key, tools=tools, kind="numeric", bands=bands)


def _sel_rule(factor, key, tools, mapping):
    return dict(factor=factor, input=key, tools=tools, kind="select", mapping=mapping)


# Each numeric band: (condition text, predicate, effect, reason). First match wins.
RULES = [
    _num_rule("Business age", "age_years", None, [
        ("under 1 year", lambda v: v < 1, -0.20, "Under one year of history gives buyers little evidence that earnings will last."),
        ("1 to under 2 years", lambda v: v < 2, -0.10, "One to two years of history is short for most buyers."),
        ("2 to under 4 years", lambda v: v < 4, 0.0, "Two to four years of history is treated as the baseline."),
        ("4 years or more", lambda v: True, 0.05, "Four or more years of history supports durability."),
    ]),
    _num_rule("Revenue trend", "growth_pct", None, [
        ("below −20%", lambda v: v < -20, -0.25, "Revenue fell more than 20% year on year."),
        ("−20% to below −5%", lambda v: v < -5, -0.12, "Revenue is declining."),
        ("−5% to +5%", lambda v: v <= 5, 0.0, "Revenue is roughly flat, the baseline."),
        ("above +5% to +25%", lambda v: v <= 25, 0.08, "Revenue is growing steadily."),
        ("above +25% to +75%", lambda v: v <= 75, 0.15, "Revenue is growing quickly."),
        ("above +75%", lambda v: True, 0.20, "Very fast growth, capped because it is hard to sustain."),
    ]),
    _num_rule("Owner involvement", "owner_hours", None, [
        ("over 40 hours/week", lambda v: v > 40, -0.10, "More than full-time owner work means a buyer must replace that labour."),
        ("over 20 to 40 hours/week", lambda v: v > 20, -0.05, "Substantial weekly owner time."),
        ("10 to 20 hours/week", lambda v: v >= 10, 0.0, "Moderate owner time, the baseline."),
        ("under 10 hours/week", lambda v: True, 0.05, "Low owner time makes the business easier to transfer."),
    ]),
    _num_rule("Channel concentration", "top_channel_pct", None, [
        ("over 80% from one channel", lambda v: v > 80, -0.12, "Over 80% from one channel. A single algorithm or policy change could hit revenue."),
        ("over 60% to 80%", lambda v: v > 60, -0.06, "Most traffic or sales come from one channel."),
        ("60% or less", lambda v: True, 0.0, "Channels are reasonably diversified."),
    ]),
    _num_rule("Customer concentration", "top_customer_pct", None, [
        ("over 30% from one customer", lambda v: v > 30, -0.12, "One customer provides more than 30% of revenue."),
        ("over 15% to 30%", lambda v: v > 15, -0.06, "One customer provides a notable share of revenue."),
        ("15% or less", lambda v: True, 0.0, "No single customer dominates revenue."),
    ]),
    _num_rule("Churn", "monthly_churn", ("saas", "ai"), [
        ("over 8% per month", lambda v: v > 8, -0.20, "Monthly churn above 8% replaces most of the customer base within a year."),
        ("over 5% to 8%", lambda v: v > 5, -0.10, "Monthly churn is high."),
        ("2% to 5%", lambda v: v >= 2, 0.0, "Monthly churn between 2% and 5% is the baseline."),
        ("under 2%", lambda v: True, 0.10, "Monthly churn under 2% indicates sticky revenue."),
    ]),
    _num_rule("Gross margin", "gross_margin", ("saas", "ai"), [
        ("under 50%", lambda v: v < 50, -0.15, "Gross margin under 50% leaves little room after direct costs."),
        ("50% to under 70%", lambda v: v < 70, -0.07, "Gross margin is below typical software levels."),
        ("70% to 80%", lambda v: v <= 80, 0.0, "Gross margin of 70–80% is the baseline."),
        ("above 80%", lambda v: True, 0.05, "Gross margin above 80%."),
    ]),
    _sel_rule("Model provider dependency", "model_dependency", ("ai",), {
        "single": (-0.10, "Relying on one model provider exposes margins and product to that provider's decisions."),
        "multi": (0.0, "The product can switch providers."),
        "own": (0.05, "Owned or fine-tuned models reduce provider risk."),
    }),
    _sel_rule("Monetization", "monetization", ("website",), {
        "display": (0.0, "Display advertising is the baseline."),
        "affiliate": (-0.03, "Affiliate programmes can change commission rates or close."),
        "leadgen": (0.0, "Lead generation is valued at the baseline."),
        "products": (0.03, "Owned products give more control over revenue."),
        "mixed": (0.03, "Diversified revenue sources."),
    }),
    _sel_rule("Platforms", "platform", ("app",), {
        "both": (0.03, "Available on both major app stores."),
        "ios": (0.0, "Single-platform app, the baseline."),
        "android": (0.0, "Single-platform app, the baseline."),
    }),
    _sel_rule("Revenue model", "app_model", ("app",), {
        "subscription": (0.05, "Subscription revenue is more predictable."),
        "iap": (0.0, "In-app purchases are the baseline."),
        "ads": (-0.05, "Ad revenue depends on ad rates and user volume."),
        "paid": (-0.05, "Paid downloads depend on continuous new sales."),
    }),
    _num_rule("Audience engagement", "open_rate", ("newsletter",), [
        ("under 25%", lambda v: v < 25, -0.08, "Open rate under 25% suggests low engagement."),
        ("25% to 45%", lambda v: v <= 45, 0.0, "Open rate of 25–45% is the baseline."),
        ("above 45%", lambda v: True, 0.05, "Open rate above 45% (check for inflation from privacy features)."),
    ]),
    _sel_rule("Revenue model", "newsletter_model", ("newsletter",), {
        "paid": (0.05, "Paid subscriptions are recurring and direct."),
        "sponsorship": (0.0, "Sponsorship revenue is the baseline."),
        "mixed": (0.03, "Diversified revenue."),
    }),
    _sel_rule("Fulfillment", "fulfillment", ("ecommerce",), {
        "own": (0.0, "Own fulfillment is the baseline, though it adds operational transfer work."),
        "3pl": (0.03, "Outsourced logistics is easier to hand over."),
        "dropship": (-0.08, "Dropshipping depends on suppliers the buyer does not control."),
    }),
]


def rules_for(tool):
    return [r for r in RULES if (r["tools"] is None or tool in r["tools"]) and r["input"] in TOOL_INPUTS[tool]]


def rules_table():
    """Flattened rules for the public methodology page."""
    out = []
    for r in RULES:
        applies = "All types" if r["tools"] is None else ", ".join(TYPE_LABEL[t] for t in r["tools"])
        if r["kind"] == "numeric":
            rows = [(cond, eff, reason) for cond, _p, eff, reason in r["bands"]]
        else:
            opts = dict(F[r["input"]]["options"])
            rows = [(opts[k], eff, reason) for k, (eff, reason) in r["mapping"].items()]
        out.append(dict(factor=r["factor"], input=F[r["input"]]["label"], applies=applies, rows=rows))
    return out


def adjustments(tool, x):
    adj = []
    for r in rules_for(tool):
        v = x.get(r["input"])
        if v is None or v == "":
            continue
        if r["kind"] == "numeric":
            hit = next(((eff, reason) for _c, pred, eff, reason in r["bands"] if pred(v)), None)
        else:
            hit = r["mapping"].get(v)
        if hit is None:
            continue
        eff, reason = hit
        adj.append(dict(factor=r["factor"], input=r["input"], value=display_value(r["input"], v),
                        effect=float(eff), reason=reason))
    return adj


# --------------------------------------------------------------------------
# Valuation
# --------------------------------------------------------------------------
def round_money(v):
    if v is None:
        return None
    if abs(v) < 20000:
        return int(round(v / 100.0) * 100)
    if abs(v) < 1_000_000:
        return int(round(v / 1000.0) * 1000)
    return int(round(v / 10000.0) * 10000)


def confidence(tool, x, adj):
    reasons = []
    score = 0
    provided = sum(1 for k in TOOL_INPUTS[tool] if x.get(k) not in (None, ""))
    share = provided / len(TOOL_INPUTS[tool])
    if share >= 0.8:
        score += 2
    elif share >= 0.5:
        score += 1
        reasons.append("Several optional inputs were left blank, so fewer risk factors were assessed.")
    else:
        reasons.append("Most optional inputs were left blank, so the estimate relies mainly on the base multiple.")
    age = x.get("age_years")
    if age is not None and age >= 2:
        score += 1
    else:
        reasons.append("Less than two years of history (or age not provided) makes earnings harder to project.")
    negative_total = sum(a["effect"] for a in adj if a["effect"] < 0)
    if any(a["effect"] <= -0.12 for a in adj) or negative_total <= -0.25:
        reasons.append("At least one significant risk factor was found; buyers will examine it closely.")
    else:
        score += 1
    level = {4: "Reasonable", 3: "Reasonable", 2: "Moderate"}.get(score, "Low")
    return level, reasons


def value_business(tool, x):
    """Return a fully labelled result dict. Raises ValuationError when the
    inputs cannot support an earnings-based estimate."""
    base = BASE[tool]
    warnings = []
    if base["method"] == "profit":
        profit = x.get("monthly_profit")
        revenue = x.get("monthly_revenue")
        if profit is None or profit <= 0:
            raise ValuationError(
                "This method values a business on its earnings, and the profit entered is zero or negative. "
                "Loss-making businesses are usually priced on their assets, audience or strategic value, "
                "which this tool does not estimate."
            )
        if revenue and profit > revenue:
            raise ValuationError("Monthly profit can't be higher than monthly revenue. Please check both figures.")
        metric_value = profit * 12
        metric = dict(key="annual_profit", label="Annual net profit (SDE)", value=metric_value,
                      formula="Average monthly net profit × 12", origin="calculated")
        margin = (profit / revenue * 100) if revenue else None
    else:
        mrr = x.get("mrr")
        metric_value = mrr * 12
        metric = dict(key="arr", label="Annual recurring revenue (ARR)", value=metric_value,
                      formula="MRR × 12", origin="calculated")
        margin = None
        p = x.get("monthly_profit")
        if p is not None and p < 0:
            warnings.append("The business is loss-making. Buyers of small SaaS and AI businesses often "
                            "weight profit heavily, so expect offers toward the low end of the range.")

    adj = adjustments(tool, x)
    factor = 1.0
    for a in adj:
        factor *= (1 + a["effect"])
    capped = False
    if factor < ADJ_FLOOR:
        factor, capped = ADJ_FLOOR, True
    if factor > ADJ_CEIL:
        factor, capped = ADJ_CEIL, True
    if capped:
        warnings.append("The combined adjustments hit the model's limit (−50% / +40%), so the range was capped.")

    m_low = base["low"] * factor
    m_mid = base["mid"] * factor
    m_high = base["high"] * factor
    value = dict(low=round_money(metric_value * m_low), mid=round_money(metric_value * m_mid),
                 high=round_money(metric_value * m_high))

    extras = []
    if tool == "ecommerce" and x.get("inventory_value"):
        inv = x["inventory_value"]
        extras.append(dict(label="Inventory at cost (added on top)", value=round_money(inv), origin="user-provided",
                           note="Inventory is normally paid for separately at cost, after a stock count at closing."))
        value_incl = dict(low=value["low"] + round_money(inv), mid=value["mid"] + round_money(inv),
                          high=value["high"] + round_money(inv))
    else:
        value_incl = None

    cross = None
    if base["method"] == "arr":
        p = x.get("monthly_profit")
        if p and p > 0:
            implied = value["mid"] / (p * 12)
            cross = dict(label="Implied multiple of annual profit", value=round(implied, 1),
                         note="The midpoint divided by annual profit. Profit-focused buyers often compare "
                              "this with 3–5× profit (a platform assumption, not market data); a much higher figure "
                              "means the price relies on growth continuing.")
        if x.get("mrr") and x.get("monthly_churn"):
            churn = x["monthly_churn"] / 100.0
            if churn > 0:
                arpa_life_months = 1 / churn
                extras.append(dict(label="Implied average customer lifetime", value=f"{arpa_life_months:.0f} months",
                                   origin="calculated", note="1 ÷ monthly churn. A rough guide; real cohorts vary."))

    level, reasons = confidence(tool, x, adj)

    # Sensitivity: value at alternative multiples around the adjusted midpoint.
    sens = []
    for delta in (-1.0, -0.5, 0.0, 0.5, 1.0):
        m = max(0.5, m_mid + delta)
        sens.append(dict(multiple=round(m, 2), value=round_money(metric_value * m)))

    return dict(
        tool=tool,
        type_label=TYPE_LABEL[tool],
        type_noun=TYPE_NOUN[tool],
        method="Multiple of annual profit (SDE)" if base["method"] == "profit" else "Multiple of ARR",
        metric=metric,
        margin_pct=round(margin, 1) if margin is not None else None,
        base_multiple=dict(low=base["low"], mid=base["mid"], high=base["high"], origin="platform assumption",
                           source=f"VALUERAQ default range, methodology v{METHODOLOGY_VERSION}"),
        adjustments=adj,
        adjustment_factor=round(factor, 3),
        multiple=dict(low=round(m_low, 2), mid=round(m_mid, 2), high=round(m_high, 2), origin="calculated"),
        value=value,
        value_including_extras=value_incl,
        extras=extras,
        cross_check=cross,
        confidence=level,
        confidence_reasons=reasons,
        warnings=warnings,
        sensitivity=sens,
        inputs={**{k: x.get(k) for k in TOOL_INPUTS[tool]},
                **({"revenue_sources": x["revenue_sources"]} if x.get("revenue_sources") else {})},
        methodology_version=METHODOLOGY_VERSION,
    )


# --------------------------------------------------------------------------
# Calculators
# --------------------------------------------------------------------------
def website_worth(monthly_profit, months=36):
    p = _num(monthly_profit)
    m = _num(months) if months not in (None, "") else 36
    if p is None or p <= 0:
        raise ValuationError("Enter a monthly net profit above zero.")
    if not (6 <= m <= 84):
        raise ValuationError("Use a multiple between 6 and 84 months.")
    table = [dict(months=mm, annual_multiple=round(mm / 12, 2), value=round_money(p * mm))
             for mm in (24, 30, 36, 42, 48)]
    return dict(monthly_profit=p, months=m, annual_multiple=round(m / 12, 2),
                value=round_money(p * m), annual_profit=p * 12, table=table)


def saas_quick(mrr, growth_pct=None, monthly_churn=None):
    x = {"mrr": _num(mrr), "growth_pct": _num(growth_pct), "monthly_churn": _num(monthly_churn)}
    if not x["mrr"] or x["mrr"] <= 0:
        raise ValuationError("Enter MRR above zero.")
    return value_business("saas", x)


def business_multiple(asking_price, annual_revenue=None, annual_profit=None, category=None):
    price = _num(asking_price)
    rev = _num(annual_revenue)
    prof = _num(annual_profit)
    if not price or price <= 0:
        raise ValuationError("Enter an asking price above zero.")
    if not rev and not prof:
        raise ValuationError("Enter annual revenue, annual profit, or both.")
    out = dict(asking_price=price, annual_revenue=rev, annual_profit=prof)
    out["revenue_multiple"] = round(price / rev, 2) if rev else None
    if prof and prof > 0:
        out["profit_multiple"] = round(price / prof, 2)
        out["months_of_profit"] = round(price / (prof / 12), 1)
        out["payback_years"] = round(price / prof, 1)
    else:
        out["profit_multiple"] = out["months_of_profit"] = out["payback_years"] = None
    if rev and prof:
        out["margin_pct"] = round(prof / rev * 100, 1)
    if category in BASE:
        b = BASE[category]
        compare = out["profit_multiple"] if b["method"] == "profit" else out["revenue_multiple"]
        out["reference"] = dict(category=TYPE_NOUN[category], basis="profit" if b["method"] == "profit" else "ARR/revenue",
                                low=b["low"], high=b["high"], compare=compare,
                                position=None if compare is None else
                                ("below" if compare < b["low"] else "above" if compare > b["high"] else "within"))
    return out
