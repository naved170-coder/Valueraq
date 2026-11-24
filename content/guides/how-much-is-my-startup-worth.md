---
title: How Much Is My Startup Worth? Valuation for Revenue-Stage Startups
meta_title: How Much Is My Startup Worth? 3 Worked Examples
meta_description: A startup with revenue is priced on a multiple of ARR or yearly profit. See which method fits your stage and 3 worked examples. Free calculator included.
h1: How Much Is My Startup Worth? Valuation for Revenue-Stage Startups
section: Valuation
cluster: valuation
order: 60
page_type: article
answer: A startup that earns revenue is usually worth a multiple of its annual recurring revenue (for subscription software) or of its yearly profit (for most other businesses), adjusted for growth, churn, customer concentration and how much the founder does. A startup with no revenue has no earnings to multiply, so its value rests on judgement about the team, product and market.
keywords: how much is my startup worth, startup valuation calculator, value my startup
published: 2026-11-25
updated: 2026-11-25
publish_at: 2026-11-24T19:00Z
image: /static/img/articles/how-much-is-my-startup-worth.png
image_alt: Featured image for the guide How Much Is My Startup Worth?
score: 8.7
related: /guides/saas-valuation/, /guides/micro-saas-valuation/, /guides/how-to-sell-a-saas-business/, /guides/revenue-vs-profit-multiples/, /guides/saas-metrics-buyers-check/, /guides/can-you-sell-a-website-with-no-revenue/
cta: /tools/saas-valuation/
cta_text: Enter your MRR, growth and churn to see a low, midpoint and high value for your startup.
---

## Key takeaway

How much your startup is worth depends first on its stage. If it earns real revenue, a buyer will price it from what it earns: a multiple of annual recurring revenue (ARR) for subscription software, or a multiple of yearly profit for most other businesses. Growth, churn, customer concentration and founder dependence then move that multiple up or down. If it earns nothing yet, there are no earnings to multiply, and any number is a judgement about the team, the product and the market, not a calculation.

This guide is for founders who have revenue and want to know what the business could sell for. It does not try to predict what an investor might pay for shares in a funding round.

## Start with your stage

The same word, "valuation", covers very different questions. Pick the row that matches your startup.

| Stage | What exists | What drives the number | Best fit |
|---|---|---|---|
| No product or revenue | An idea, a team, maybe a prototype | Judgement about team and market | Not a calculation; see the FAQ |
| Product, small or irregular revenue | Early customers, under a year of data | Run rate, early retention, potential | A cautious ARR range, with a heavy discount |
| Steady subscription revenue | Monthly recurring revenue and churn data | ARR multiple, adjusted for growth and churn | [SaaS valuation](/guides/saas-valuation/) |
| Steady profit (app, store, site, newsletter) | Twelve months of profit | Profit multiple, adjusted for risk | [Profit multiples](/guides/revenue-vs-profit-multiples/) |

The rest of this page covers the last two rows, where a calculation is possible.

## Why a funding "valuation" is not a sale price

Many articles on startup valuation are written for founders raising money. That is a different deal. A funding round sets a price for a slice of the company, usually in return for shares with special rights, and the founders keep running the business. A sale hands the whole business to a buyer for cash, and the buyer then owns the risk.

So a number quoted for a funding round says little about what a buyer would pay you today. A buyer purchasing a small startup looks at what it earns, how safely it will keep earning, and how much work it will take to run. That is what the methods below measure.

## Method 1: a multiple of ARR (subscription startups)

If your revenue is subscriptions, the usual starting point is annual recurring revenue. Stripe defines monthly recurring revenue as "the total amount of money a company can expect to receive from its existing customers each month" ([Stripe](https://stripe.com/resources/more/essential-saas-metrics)). ARR is that figure times twelve. For the full definitions, see [MRR](/glossary/mrr/) and [ARR](/glossary/arr/).

Corporate Finance Institute describes the run-rate idea as taking "a company's current revenue in a certain period (a week, month, quarter, etc.) and converts it to an annual figure", and warns that it assumes conditions stay unchanged and can be distorted by seasonality or one-off events ([CFI](https://corporatefinanceinstitute.com/resources/accounting/revenue-run-rate/)). Count only recurring subscription revenue. Leave out setup fees, one-off projects and anything that will not renew.

VALUERAQ's default range for a SaaS business is 2× to 5× ARR, with a midpoint of 3.5×. That range is a platform assumption described on the [methodology](/methodology/) page. It is not a measured market average, and a real sale can land outside it.

![Default ARR multiple range, SaaS: Low 2x, Midpoint 3.5x, High 5x](/static/img/articles/how-much-is-my-startup-worth-default-arr-range.svg){: width="720" height="226" loading="lazy" }

A revenue multiple has a known weakness. Corporate Finance Institute notes that the enterprise value to revenue multiple "ignores profitability and cash flow generation" ([CFI](https://corporatefinanceinstitute.com/resources/valuation/ev-to-revenue-multiple)). Two startups with the same ARR can be worth very different amounts if one is profitable and one is burning cash, which is why buyers also look at the metrics in [what buyers check before an offer](/guides/saas-metrics-buyers-check/).

## Method 2: a multiple of yearly profit (everything else)

For an app, a store, a content site or a newsletter, buyers price the profit. Take twelve months of revenue, subtract every cost a new owner would pay, and do not subtract the founder's own salary. This is seller's discretionary earnings, or [SDE](/glossary/sde/). If you need help finding the add-backs, see [how to calculate SDE](/guides/how-to-calculate-sde/). BizBuySell warns that "some add-backs can unrealistically overvalue the company" ([BizBuySell](https://www.bizbuysell.com/learning-center/article/add-backs-sde/)), so count only costs you can document.

VALUERAQ's default range for a mobile app is 2× to 3.5× yearly profit, with a midpoint of 2.7×. Websites and newsletters default to 2.5× to 4×. These are also platform assumptions, not market data.

The SBA describes the same logic in general terms. Its income approach "looks at projected revenue and accounts for potential risks", and its market approach "compares your business to other similar businesses that have recently sold" ([SBA](https://www.sba.gov/business-guide/manage-your-business/close-or-sell-your-business)).

## What moves the multiple

Both methods start from a base range and then adjust it for the facts of your business. These are the rules VALUERAQ's tools apply, as published on the methodology page.

| Factor | Condition | Effect on the multiple |
|---|---|---|
| Revenue trend | Growing above 25% to 75% | +15% |
| Revenue trend | Growing above 5% to 25% | +8% |
| Revenue trend | Falling 5% to 20% | −12% |
| Monthly churn (SaaS) | Under 2% | +10% |
| Monthly churn (SaaS) | Over 5% to 8% | −10% |
| Monthly churn (SaaS) | Over 8% | −20% |
| Largest customer | Over 30% of revenue | −12% |
| Largest customer | Over 15% to 30% | −6% |
| Owner time | Over 40 hours a week | −10% |
| Owner time | Under 10 hours a week | +5% |

The effects multiply together, and the combined factor is capped between 0.5 and 1.4 so no set of answers can move the multiple beyond that. The full list, including gross margin and business age, is on the [methodology](/methodology/) page.

## Worked example 1: a fast-growing SaaS startup

A SaaS startup has $15,000 in MRR, revenue growth of 40% over the last twelve months and monthly churn of 2%.

1. ARR is 15,000 × 12 = $180,000.
2. At the default range before adjustments, that is $360,000 (2× ARR), $630,000 (3.5×) and $900,000 (5×).
3. Growth of 40% falls in the "above 25% to 75%" band: +15%. Churn of 2% is in the baseline band: 0%. The combined factor is 1.15.
4. The adjusted multiples are 2.3×, about 4.02× and 5.75×.
5. The value range is $414,000 (180,000 × 2.3), about $724,000 at the midpoint and about $1,040,000 (rounded).

Add profit to the picture and a buyer may see it differently. If the startup earns $5,000 a month, annual profit is $60,000, and the midpoint of $724,000 is about 12.1× that profit. A buyer focused on profit may compare that figure with a lower profit multiple, which tells you the price depends on growth continuing.

## Worked example 2: the same ARR, more risk

Now take a startup with the same $15,000 MRR (ARR of $180,000), but no growth, 6% monthly churn and one customer that provides 35% of revenue.

1. Growth of 0% is flat: 0%.
2. Churn of 6% falls in the "over 5% to 8%" band: −10%.
3. A 35% customer share is over 30%: −12%.
4. The combined factor is 0.90 × 0.88 = 0.792.
5. The adjusted multiples are about 1.58×, 2.77× and 3.96×, giving roughly $285,000, $499,000 and $713,000.

The ARR is identical, yet the midpoint is about $225,000 lower than in example 1. That gap is what a buyer is paying for: durability. See [customer concentration](/glossary/customer-concentration/) and [churn](/glossary/churn/) for how each risk is measured.

## Worked example 3: a small app priced on profit

A mobile app earns $11,000 a month in revenue and $6,000 a month in profit, is three years old, is growing 10% and takes the founder 15 hours a week.

1. Annual profit (SDE) is 6,000 × 12 = $72,000.
2. Age of two to four years is the baseline: 0%. Growth of 10% is in the "above 5% to 25%" band: +8%. Fifteen owner hours is the baseline: 0%. The combined factor is 1.08.
3. The default 2× to 3.5× range becomes 2.16×, about 2.92× and 3.78×.
4. The value range is about $156,000, $210,000 and $272,000.

![Midpoint values in the three examples: Fast-growth SaaS $724,000, Concentrated SaaS $499,000, Profit-based app $210,000](/static/img/articles/how-much-is-my-startup-worth-example-midpoints.svg){: width="720" height="226" loading="lazy" }

## Check your own number in five steps

Use this checklist before you trust any estimate, including ours.

1. Decide which method fits: ARR if revenue is recurring subscriptions, profit if not.
2. Pull twelve months of real figures from your payment processor and bank, not from memory.
3. Remove anything that will not repeat, such as one-off projects and refunded sales.
4. List your risks honestly: churn, one big customer, one acquisition channel, founder hours.
5. Calculate a range, not a point, and expect real offers to differ from it.

You can do steps 3 to 5 in a few minutes with the free [SaaS valuation tool](/tools/saas-valuation/) or the [SaaS valuation calculator](/calculators/saas-valuation-calculator/). Both show every step and label each figure as user-provided, platform assumption or calculated.

## What a buyer will actually test

An estimate is only a starting point. The SBA advises a "thorough, objective investigation" before buying and suggests that buyers "consider hiring an attorney and an accountant" ([SBA](https://www.sba.gov/business-guide/plan-your-business/buy-existing-business-or-franchise)). Expect a buyer to ask for financial statements, proof of revenue, customer and churn data, and details of any contracts. If you plan to sell, [how to sell a SaaS business](/guides/how-to-sell-a-saas-business/) walks through the steps and documents.

## Frequently asked questions

### How much is my startup worth if it has no revenue?

There is no earnings figure to multiply, so there is no reliable formula. A buyer would be paying for the team, the code, the audience or the market position, and the price is a negotiation. The platform's tools do not estimate pre-revenue businesses. If you have some revenue, even small, you can value the run rate with a heavy discount, as in [can you sell a website with no revenue](/guides/can-you-sell-a-website-with-no-revenue/).

### Does a startup that depends on its founder lose value?

Usually yes. More than 40 owner hours a week reduces the default multiple by 10%, because the buyer must replace that labour. A business that runs in under 10 hours a week gains 5%.

### What if one customer pays most of my revenue?

That is a concentration risk. In the default rules, a customer providing over 30% of revenue lowers the multiple by 12%, and a share over 15% to 30% lowers it by 6%.

### Is a startup valuation calculator accurate?

It is an estimate. A calculator can apply published multiples and adjustments consistently, but it cannot see your contracts, code quality or buyer demand. Treat its output as a range to test against real offers, and read [how accurate a valuation calculator is](/guides/how-accurate-is-a-business-valuation-calculator/).

## Sources

- Stripe, [Essential SaaS metrics](https://stripe.com/resources/more/essential-saas-metrics): definitions of MRR, ARR and churn.
- Corporate Finance Institute, [Revenue run rate](https://corporatefinanceinstitute.com/resources/accounting/revenue-run-rate/): converting current revenue to an annual figure and its risks.
- Corporate Finance Institute, [Enterprise value to revenue multiple](https://corporatefinanceinstitute.com/resources/valuation/ev-to-revenue-multiple): why revenue multiples ignore profitability.
- U.S. Small Business Administration, [Close or sell your business](https://www.sba.gov/business-guide/manage-your-business/close-or-sell-your-business): income and market approaches.
- U.S. Small Business Administration, [Buy an existing business or franchise](https://www.sba.gov/business-guide/plan-your-business/buy-existing-business-or-franchise): what buyers investigate.
- BizBuySell Learning Center, [Add-Backs for Seller's Discretionary Earnings](https://www.bizbuysell.com/learning-center/article/add-backs-sde/): why add-backs must be documented.
- VALUERAQ, [Valuation methodology](/methodology/): the default multiples and adjustment rules used in the examples.
