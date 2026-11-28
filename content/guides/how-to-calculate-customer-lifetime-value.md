---
title: How to Calculate Customer Lifetime Value
meta_title: Customer Lifetime Value Formula: 3 Business Types
meta_description: Customer lifetime value is gross profit per customer over their time with you. See formulas for subscriptions, stores and content, with worked examples.
h1: How to Calculate Customer Lifetime Value
section: Analysis
cluster: analysis
order: 60
page_type: article
answer: Customer lifetime value (LTV) is the gross profit an average customer brings in before they leave. For a subscription, divide monthly revenue per customer times gross margin by monthly churn. For a store, multiply profit per order by the number of orders a customer places.
keywords: how to calculate customer lifetime value, customer lifetime value formula, ltv calculation, how to calculate ltv, clv formula
published: 2026-11-22
updated: 2026-11-28
publish_at: 2026-11-22T01:00Z
image: /static/img/articles/how-to-calculate-customer-lifetime-value.png
image_alt: How to Calculate Customer Lifetime Value (VALUERAQ guide)
score: 8.6
related: /glossary/ltv/, /glossary/ltv-to-cac-ratio/, /glossary/cac/, /glossary/churn/, /glossary/gross-margin/, /guides/saas-metrics-buyers-check/
cta: /tools/saas-valuation/
cta_text: Once you know your lifetime value, see what a buyer's profit or ARR multiple says the whole business could be worth.
---

## Key takeaway

Customer lifetime value, usually shortened to LTV or CLV, answers one question: **how much gross profit does an average customer bring in before they stop buying?** Revenue alone is the wrong number, because a customer who pays $100 but costs you $90 to serve is worth $10.

The core recipe has three parts: what a customer pays, how much of it you keep after direct costs, and how long they stay. Subscription businesses estimate "how long" from [churn](/glossary/churn/). Stores count orders. Everything else in this guide is a variation on that recipe, with the arithmetic shown so you can copy it.

All figures below are made-up examples, not market data and not a promise of results.

## The simple formula

For a business that bills customers every month:

**LTV = (average revenue per customer per month × gross margin) ÷ monthly churn rate**

Each piece:

- **Average revenue per customer per month**, sometimes called [ARPU](/glossary/arpu/): total monthly revenue divided by the number of paying customers.
- **[Gross margin](/glossary/gross-margin/)**: the share of revenue left after the direct costs of delivering the product, such as hosting, payment fees and support. Use a percentage, so 80% becomes 0.80.
- **Monthly churn rate**: the share of customers who leave in a month. Stripe describes churn as "The percentage of total customers who discontinue using a product or service during a given period."

Dividing by churn is the same as multiplying by the average customer lifetime. If 4% of customers leave each month, the average customer stays 1 ÷ 0.04 = 25 months.

## Worked example 1: a subscription product

A small software product charges an average of $40 a month. Its gross margin is 80% and monthly churn is 4%.

1. Monthly gross profit per customer: $40 × 0.80 = **$32**
2. Average lifetime: 1 ÷ 0.04 = **25 months**
3. LTV = $32 × 25 = **$800**

The same answer comes from the formula in one step: $32 ÷ 0.04 = $800.

Notice how sensitive the result is to churn. Holding everything else equal:

| Monthly churn | Average lifetime | LTV |
|---|---|---|
| 5% | 20 months | $640 |
| 4% | 25 months | $800 |
| 3% | 33.3 months | $1,067 |
| 2% | 50 months | $1,600 |

![SaaS example: LTV at four monthly churn rates ($40 a month, 80% margin): 5% churn 640$, 4% churn 800$, 3% churn 1067$, 2% churn 1600$](/static/img/articles/how-to-calculate-customer-lifetime-value-ltv-by-churn.svg){: width="720" height="272" loading="lazy" }

Cutting churn from 4% to 2% doubles LTV. That is why a buyer looking at a subscription business studies churn before almost anything else. Our guide to the [SaaS metrics buyers check](/guides/saas-metrics-buyers-check/) covers the rest of that list.

## Worked example 2: an online store

A store does not have a monthly churn rate, because customers buy when they need something. Count orders instead:

**LTV = average order value × gross margin × average number of orders per customer**

An example store has an average order value of $60 and a gross margin of 45% after product cost, shipping and payment fees. Over their time as a customer, buyers place an average of 4 orders.

1. Gross profit per order: $60 × 0.45 = **$27**
2. LTV = $27 × 4 = **$108**

Two things move this number for a store: how much each order earns (see [average order value](/glossary/average-order-value/)) and how often customers come back. A store that wins repeat orders is worth more per customer than one that depends on first-time buyers. If you track repeat behavior, [cohort analysis](/glossary/cohort-analysis/) shows it far more reliably than an average.

## Worked example 3: a content or newsletter business

If readers are free and income comes from ads or sponsors, you can still estimate a value per reader. Divide the gross profit the audience earns in a year by the number of active readers, then multiply by the number of years a typical reader stays.

For example, a newsletter earns $24,000 a year in sponsorship income with $4,000 of direct costs (an email platform and a freelance editor), so gross profit is $20,000. It has 10,000 active readers, so gross profit per reader is $2.00 a year. If the average reader stays for 2 years, LTV is $2.00 × 2 = **$4.00**.

Small numbers like this are normal. They matter when you compare them with what it costs to gain a reader, which is where the next section comes in.

## Compare LTV with the cost to win a customer

LTV on its own does not say whether growth pays. Set it against [CAC](/glossary/cac/), the average cost of winning one customer. The result is the [LTV to CAC ratio](/glossary/ltv-to-cac-ratio/).

| | Store (example 2) | Software (example 1) |
|---|---|---|
| LTV | $108 | $800 |
| CAC | $45 | $200 |
| LTV ÷ CAC | 2.4 to 1 | 4 to 1 |
| Gross profit left per customer after CAC | $63 | $600 |

![LTV vs CAC, two example businesses: Store LTV 108$, Store CAC 45$, SaaS LTV 800$, SaaS CAC 200$](/static/img/articles/how-to-calculate-customer-lifetime-value-ltv-cac-compare.svg){: width="720" height="272" loading="lazy" }

A ratio near or below 1 to 1 means each customer returns about what they cost to win, or less. The higher it is, the more room the business has to spend on growth. The right level depends on the business, so treat any single target as a rule of thumb, not a law. The [payback period](/glossary/payback-period/) is a useful second check: it tells you how many months it takes to earn back CAC.

## Worked example 4: when churn changes in the first months

The simple formula assumes churn is the same every month. In practice many businesses lose more customers early on. If you have the data, calculate lifetime from a cohort instead.

Suppose 100 customers join in January and pay $40 a month at an 80% gross margin ($32 a month of gross profit each). You count how many are still paying:

| Month | Customers still paying | Gross profit that month |
|---|---|---|
| 1 | 100 | $3,200 |
| 2 | 90 | $2,880 |
| 3 | 84 | $2,688 |
| 4 | 80 | $2,560 |
| 5 | 77 | $2,464 |
| 6 | 75 | $2,400 |

Six months of gross profit from the cohort adds up to $16,192, or **$161.92 per original customer** so far. That is real, observed LTV for six months. To estimate the full lifetime, extend the pattern with a sensible churn rate for the later months and label the extension as an estimate.

## Subscription vs store vs content: formulas side by side

| Business type | Formula | What to measure |
|---|---|---|
| Subscription or SaaS | (monthly revenue per customer x gross margin) / monthly churn | ARPU, margin, churn |
| Online store | average order value x gross margin x orders per customer | Order value, margin, repeat rate |
| Content or newsletter | revenue per subscriber per month x margin x months subscribed | Revenue per subscriber, retention |

## How one mistake changes the answer

A subscription business has $40 monthly revenue per customer, an 80% gross margin and 4% monthly churn.

- Correct: $40 x 0.80 / 0.04 = **$800**.
- Using revenue instead of gross profit: $40 / 0.04 = $1,000, which overstates LTV by $200 (25%).
- Churn rising from 4% to 5%: $32 / 0.05 = $640, a drop of 20% from $800.

Two small slips, a wrong base and a slightly higher churn, move the figure by a fifth or a quarter. That is why buyers ask how each input was measured.

## What to show a buyer

| Show | Why a buyer asks |
|---|---|
| Churn by month for 12 months | One good month proves nothing |
| Gross margin with the costs listed | Confirms the margin is not overstated |
| LTV and CAC by channel | Shows which marketing pays back |
| How you count cancelled-then-returned customers | Changes churn |

## Step-by-step checklist

1. **Pick the right period.** Use at least 12 months of data, so one unusual month does not distort the average.
2. **Take revenue per customer** from your payment records, net of refunds.
3. **Subtract direct costs** to get gross margin. Include payment fees, hosting, shipping and customer support tied to delivering the product. Leave out general overhead.
4. **Choose how to measure lifetime.** Subscription: 1 ÷ monthly churn. Store: average orders per customer. Audience: average years a reader stays.
5. **Multiply it through** and write down the inputs next to the answer.
6. **Compare with CAC** and calculate the ratio and payback period.
7. **Re-check by segment.** Customers from different channels or plans often have very different lifetimes.

## Common mistakes

- **Using revenue instead of gross profit.** This overstates LTV, sometimes by half.
- **Using a very low churn rate from a short window.** A great month or two is not a trend.
- **Mixing customers and orders.** Make sure the churn rate and the revenue figure refer to the same group.
- **Ignoring discounts and refunds** when computing average revenue.
- **Forgetting expansion.** If customers upgrade over time, the simple formula understates LTV. Track [net revenue retention](/glossary/net-revenue-retention/) if upgrades matter in your business.
- **Treating the average as a promise.** The formula is an estimate. Buyers often prefer actual cohort data.

## Three ways to raise lifetime value

Once you can calculate LTV, each part of the formula points to something you can change:

1. **Keep customers longer.** Lower churn has the biggest effect, as the table above shows. Look at why customers leave in their first months: unclear onboarding, a slow first delivery or a price that did not match the promise.
2. **Earn more per customer.** Annual plans, bundles and sensible upgrades raise revenue per customer without needing new customers. For a store, a higher average order value does the same job.
3. **Protect the margin.** Shipping, payment fees and support time all sit between revenue and gross profit. A small saving per order repeats for every order a customer places.

Change one input at a time and recalculate, so you know which change moved the number.

## Why lifetime value matters in a sale

When you sell an online business, a buyer wants to know whether today's revenue will still be there next year. A healthy LTV with a low churn rate suggests customers stick around, which supports a stronger price. A low LTV or a rising churn rate raises questions. VALUERAQ's [methodology](/methodology/) uses profit or recurring revenue and not LTV directly, so LTV is best treated as supporting evidence you can show a buyer, not as an input to the number.

For a quick view of what a buyer's multiples imply for your business, the free [SaaS valuation tool](/tools/saas-valuation/) gives a default range in about a minute. The range is a starting point, not an appraisal.

## Frequently asked questions

### What is the formula for customer lifetime value?

For subscriptions: (average monthly revenue per customer × gross margin) ÷ monthly churn rate. For stores: average order value × gross margin × average orders per customer. Both give gross profit per customer over their lifetime.

### Should LTV use revenue or profit?

Profit, specifically gross profit. Revenue ignores the cost of serving the customer. Using gross profit makes the number comparable with the cost to acquire the customer.

### What is a good LTV to CAC ratio?

It varies by business. A ratio near or below 1 to 1 is a warning sign, because each customer returns about what they cost to win. Higher is better, but there is no single correct target, so compare your own ratio over time and by channel.

### How often should I recalculate LTV?

Quarterly is a sensible rhythm for most small businesses, and again before you share numbers with a buyer. Recalculate sooner after a price change or a big change in marketing.

### Can I use LTV in a valuation?

Not directly. Buyers use profit or recurring revenue to price a business and LTV as evidence that the revenue will last.

### How do I calculate LTV with no churn data yet?

Use a short window and say so. Early churn is unreliable, so show the months you have rather than a forecast.

## Sources

- Stripe, [Essential SaaS metrics](https://stripe.com/resources/more/essential-saas-metrics)
- VALUERAQ, [Valuation methodology](/methodology/)
- VALUERAQ glossary, [LTV](/glossary/ltv/), [CAC](/glossary/cac/) and [churn](/glossary/churn/)
