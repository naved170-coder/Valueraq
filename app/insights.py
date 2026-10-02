"""Rule-based listing insights. No AI and no outside data: everything here is
calculated from the figures the seller entered and the published methodology.

  * price_check(l)    asking price against the valuation tool's range
  * strength(l)       seller-facing "listing strength" score with tips
  * due_diligence(l)  buyer-facing automatic checks and a checklist
"""
from . import catalog, valuation as V

_TRAFFIC_CATS = {"websites", "newsletters", "ecommerce"}


def _tool(l):
    cat = catalog.CATS_BY_SLUG.get(l["category"])
    return cat["tool"] if cat else None


def price_check(l):
    """Compare the asking price with the tool's range for the same figures.

    Returns None when the figures can't support an estimate. Only revenue,
    profit and age are known for a listing, so the range uses fewer inputs
    than a full run of the tool; callers must say so.
    """
    tool = _tool(l)
    ask = l["asking_price"]
    if not tool or not ask or ask <= 0:
        return None
    x = {"monthly_profit": l["monthly_profit"], "age_years": l["age_years"]}
    if V.BASE[tool]["method"] == "arr":
        if not l["monthly_revenue"] or l["monthly_revenue"] <= 0:
            return None
        x["mrr"] = l["monthly_revenue"]
    else:
        x["monthly_revenue"] = l["monthly_revenue"]
    try:
        r = V.value_business(tool, x)
    except (V.ValuationError, TypeError):
        return None
    low, mid, high = r["value"]["low"], r["value"]["mid"], r["value"]["high"]
    if not low or not high:
        return None
    if ask > high:
        verdict, pct = "above", round((ask - high) / high * 100)
    elif ask < low:
        verdict, pct = "below", round((low - ask) / low * 100)
    else:
        verdict, pct = "within", 0
    t = catalog.TOOLS_BY_KEY[tool]
    return dict(low=low, mid=mid, high=high, ask=ask, verdict=verdict, pct=pct, tool_name=t["name"],
                tool_path=t["path"], basis="ARR" if V.BASE[tool]["method"] == "arr" else "annual profit")


def strength(l, ownership_verified=False):
    """Return dict(score 0-100, label, tips[list[str]]). Rewards complete, checkable listings."""
    from .marketplace import words
    tips, score = [], 0

    def part(points, ok, tip):
        nonlocal score
        if ok:
            score += points
        else:
            tips.append(tip)

    wc = len(words(l["description"] or ""))
    part(15, bool(l["asking_price"]) and bool(l["monthly_revenue"]) and l["monthly_profit"] is not None
         and bool(l["age_years"]), "Fill in asking price, monthly revenue, monthly profit and business age.")
    part(10, wc >= 120, f"Lengthen the description to at least 120 words (it has {wc}).")
    part(8, wc >= 250, "Aim for 250+ words: explain how the business earns, who runs it and what a normal week looks like.")
    part(6, bool(l["headline"]), "Add a one-line summary.")
    part(5, bool(l["business_model"]), "Choose a business model.")
    part(5, bool(l["industry"]), "Add the industry or niche.")
    part(4, bool(l["country"]), "Say where you are based.")
    part(8, bool(l["growth_note"]), "Describe growth and trends over the last 12 months.")
    part(8, bool(l["assets_included"]), "List what is included in the sale (domain, code, accounts, stock, contracts).")
    part(6, bool(l["reason_for_sale"]), "Give your reason for selling. Buyers always ask.")
    if l["category"] in _TRAFFIC_CATS:
        part(5, bool(l["monthly_traffic"]), "Add monthly visits.")
    else:
        score += 5
    part(5, bool(l["website_url"]), "Add the website address (kept private) so ownership can be checked.")
    part(7, ownership_verified, "Verify that you own the website. It takes a few minutes and adds a badge.")
    part(8, (l["verification"] or "unverified") != "unverified", "Request a revenue or traffic verification badge.")
    pc = price_check(l)
    if pc is None:
        tips.append("Enter figures that let buyers check the price (profit above zero, or recurring revenue).")
    elif pc["verdict"] == "above":
        tips.append("Your asking price is above the range our tool gives for these figures. Explain why in the description, or review the price.")
    else:
        score += 5
    score = max(0, min(100, score))
    label = "Strong" if score >= 80 else "Good" if score >= 60 else "Needs work"
    return dict(score=score, label=label, tips=tips)


_CHECKLIST = {
    "all": [
        "Ask for 12 or more months of revenue records straight from the source (payment processor, ad network or billing system), not a spreadsheet.",
        "Match the stated profit to bank statements and ask which costs are left out, including the owner's own time.",
        "Confirm the seller controls the domain and the main accounts, and that each can be transferred to you.",
        "Agree in writing exactly what is included in the sale and how long the seller will help after it.",
        "Use an escrow service for payment and take legal advice before you sign.",
    ],
    "websites": ["Ask for read-only analytics access and check where visits come from, month by month.",
                 "Check that the content is original and that earnings don't depend on one affiliate programme or advertiser."],
    "saas": ["Ask for a billing-system export showing new, lost and upgraded subscriptions each month.",
             "Have a developer you trust review the code, hosting costs and third-party services."],
    "ai-businesses": ["Ask which AI model provider the product relies on and what it costs per customer.",
                      "Check gross margin after model and hosting costs, and how prices would cope if those costs rise."],
    "apps": ["Check app store ratings, recent reviews and any policy warnings on the developer account.",
             "Confirm the developer account or the app itself can be transferred under the store's rules."],
    "newsletters": ["Ask for subscriber growth, open rates and unsubscribes straight from the email platform.",
                    "Check how subscribers were collected and how much revenue comes from the largest sponsor."],
    "ecommerce": ["Ask for a stock count at cost and check supplier terms and who holds the supplier relationships.",
                  "Check refund and chargeback rates, and how much of sales come from one marketplace or ad channel."],
}


def due_diligence(l, ownership_verified=False):
    """Return dict(flags=[dict(level, title, text)], checklist=[str]).

    level is "risk", "caution" or "good". Flags only restate or calculate from the
    seller's own figures; they never claim the figures are true.
    """
    flags = []

    def add(level, title, text):
        flags.append(dict(level=level, title=title, text=text))

    tool = _tool(l)
    rev, profit, ask, age = l["monthly_revenue"], l["monthly_profit"], l["asking_price"], l["age_years"]
    verification = l["verification"] or "unverified"

    if verification == "unverified":
        add("caution", "Figures are not verified", "Revenue and traffic are as stated by the seller. Ask for evidence before you rely on them.")
    else:
        add("good", verification.replace("_", " ").capitalize(), "Our team compared the seller's evidence with these figures for the period checked.")
    if ownership_verified:
        add("good", "Website ownership confirmed", "The seller placed a code on the website and our system found it there.")

    if profit is None or not rev:
        add("caution", "Revenue or profit is missing", "Without both figures you can't judge the price. Ask the seller for them.")
    elif profit <= 0:
        add("risk", "The business is not making a profit", "A loss-making business is priced on its assets or audience, not on earnings. Ask how the asking price was reached.")
    else:
        margin = profit / rev * 100
        if margin > 85:
            add("caution", f"Very high profit margin ({margin:.0f}%)", "Ask which costs are left out: the owner's time, tools, contractors, refunds and fees.")
        elif margin < 10:
            add("caution", f"Thin profit margin ({margin:.0f}%)", "A small rise in costs or fall in sales would remove the profit.")

    if age:
        if age < 1:
            add("risk", "Less than one year old", "There isn't a full year of history, so seasonal swings and one-off spikes can't be ruled out.")
        elif age < 2:
            add("caution", "Under two years old", "A short track record. Look at every month's figures, not the average.")
        elif age >= 3:
            add("good", f"{age:g} years of history", "A longer record makes the figures easier to check.")
    else:
        add("caution", "Business age is missing", "Ask when the business first earned revenue.")

    if tool and ask and ask > 0:
        base = V.BASE[tool]
        metric = None
        if base["method"] == "profit" and profit and profit > 0:
            metric, noun = profit * 12, "annual profit"
        elif base["method"] == "arr" and rev and rev > 0:
            metric, noun = rev * 12, "annual recurring revenue"
        if metric:
            m = ask / metric
            rng = f"{base['low']:g}× to {base['high']:g}×"
            if m > base["high"] * 1.5:
                add("risk", f"Asking price is {m:.1f}× {noun}", f"That is well above our default range of {rng} for this type of business. The price relies on strong growth; ask the seller to justify it.")
            elif m > base["high"]:
                add("caution", f"Asking price is {m:.1f}× {noun}", f"That is above our default range of {rng} for this type of business. Ask what supports the premium.")
            elif m < base["low"]:
                add("caution", f"Asking price is {m:.1f}× {noun}", f"That is below our default range of {rng}. It may be a fair deal or a sign of a problem; ask why.")
            else:
                add("good", f"Asking price is {m:.1f}× {noun}", f"That is inside our default range of {rng} for this type of business, before adjustments.")
        if profit and profit > 0:
            months = ask / profit
            if months > 60:
                add("caution", f"About {months / 12:.1f} years to earn back the price", "At the current profit, with no growth and no decline.")

    if l["category"] in _TRAFFIC_CATS and not l["monthly_traffic"]:
        add("caution", "No traffic figure given", "Ask for monthly visits and where they come from.")
    if not l["reason_for_sale"]:
        add("caution", "No reason for selling given", "Ask why the owner is selling and what they will do next.")
    if not l["assets_included"]:
        add("caution", "The listing doesn't say what is included", "Confirm which assets, accounts and contracts come with the sale.")

    order = {"risk": 0, "caution": 1, "good": 2}
    flags.sort(key=lambda f: order[f["level"]])
    return dict(flags=flags, checklist=_CHECKLIST["all"][:2] + _CHECKLIST.get(l["category"], []) + _CHECKLIST["all"][2:])
