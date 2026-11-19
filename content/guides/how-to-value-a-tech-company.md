---
title: How to Value a Tech Company, Step by Step
meta_title: Tech Company Valuation Calculator: 5 Steps + Examples
meta_description: Value a small tech company in five steps: pick ARR or earnings, apply a range, adjust for risk. Two worked examples. Free calculator included.
h1: How to Value a Tech Company, Step by Step
section: Valuation
cluster: valuation
order: 60
page_type: article
answer: A small tech company is valued by choosing the right base number (annual recurring revenue for subscription software, annual earnings for a services or product business), applying a multiple range, and then adjusting that range for growth, churn, margins, customer concentration, age and owner workload.
keywords: tech company valuation calculator, service company valuation calculator, how to value a tech company, software company valuation, small tech business valuation
published: 2026-11-20
updated: 2026-11-20
publish_at: 2026-11-20T01:00Z
image: /static/img/articles/how-to-value-a-tech-company.png
image_alt: How to Value a Tech Company, Step by Step (VALUERAQ guide)
score: 8.6
related: /guides/saas-valuation/, /guides/saas-valuation-multiples/, /guides/ai-business-valuation/, /guides/how-to-value-a-marketing-agency/, /guides/saas-metrics-buyers-check/, /glossary/arr/
cta: /calculators/saas-valuation-calculator/
cta_text: Enter your MRR, growth, churn and margin to see a low, midpoint and high range for your company.
---

## Key takeaway

"Tech company" covers very different businesses, and there is no single way to price all of them. **First decide what kind of tech company you have. Then pick the base number a buyer would use (annual recurring revenue for subscription software, annual earnings for a services or product business), apply a multiple range, and adjust that range for the risks in your numbers.**

This guide is for small and mid-sized tech businesses that change hands in private deals: subscription software (SaaS), AI products, apps, and software or IT services firms. It is not about listed companies or venture-backed startups. It gives five steps, two worked examples with every line of arithmetic, and a checklist of what a buyer will ask for.

All figures in the examples are made up to show the method. Multiples quoted for SaaS and AI come from VALUERAQ's own default ranges on the [methodology](/methodology/) page. They are defaults inside our tool, not market data, and not a promise of a price.

## Step 1: Decide which kind of tech company you have

The business model decides the method. Start here, because using the wrong base number is the most common way to get the wrong answer.

| Type of tech company | What it sells | Usual base number | Usual starting method |
|---|---|---|---|
| Subscription software (SaaS) | Monthly or yearly plans | [ARR](/glossary/arr/) | Multiple of ARR, cross-checked against profit |
| AI product | Subscriptions or usage on top of models | ARR | Multiple of ARR, with a discount if one model provider is a single point of failure |
| Mobile app | Subscriptions, in-app purchases or ads | Annual profit | Multiple of annual profit |
| Software or IT services firm | Billable hours and projects | [SDE](/glossary/sde/) or [EBITDA](/glossary/ebitda/) | Multiple of earnings |

Two businesses can sit under the same label and still need different methods. A software firm that sells monthly plans is valued like SaaS. A firm that builds custom software for clients is closer to an agency, and our guide on [how to value a marketing agency](/guides/how-to-value-a-marketing-agency/) shows that route in detail.

## Step 2: Work out the base number

### For subscription software: ARR

Annual recurring revenue is your current monthly recurring revenue multiplied by twelve. Stripe describes monthly recurring revenue as "the total amount of money a company can expect to receive from its existing customers each month" ([Stripe](https://stripe.com/resources/more/essential-saas-metrics)). Count only subscriptions that are active today. Leave out one-off setup fees, consulting and anything that will not repeat. Our entries on [MRR](/glossary/mrr/) and [ARR](/glossary/arr/) show the exact steps.

If you have $20,000 of MRR, ARR is 20,000 × 12 = $240,000.

### For services, apps and products: earnings

Use [SDE](/glossary/sde/) if a buyer will work in the business, or [EBITDA](/glossary/ebitda/) if the buyer will hire someone to do the owner's job. Start from net profit and add back the owner's pay and benefits, interest, depreciation, personal costs and genuine one-offs. BizBuySell defines add-backs as "expenses added back to a company's bottom-line profits when determining Seller's Discretionary Earnings (SDE) or EBITDA," and warns that "some add-backs can unrealistically overvalue the company" ([BizBuySell](https://www.bizbuysell.com/learning-center/article/add-backs-sde/)). Keep an invoice or bank record behind every add-back. See [how to calculate SDE](/guides/how-to-calculate-sde/) and [SDE vs EBITDA](/guides/sde-vs-ebitda/) for the full method.

## Step 3: Apply a multiple range

A multiple turns the base number into a value. The Corporate Finance Institute says multiples "utilizes different financial metrics from comparable companies to value a target company" and lets you "make quick computations to assess a company's value" ([Corporate Finance Institute](https://corporatefinanceinstitute.com/resources/valuation/multiples-analysis)). The same page lists limits, so treat the result as a starting range, not an answer.

VALUERAQ's default ranges for subscription-style tech businesses are:

| Business type | Base | Low | Midpoint | High |
|---|---|---|---|---|
| SaaS business | ARR | 2.0× | 3.5× | 5.0× |
| AI business | ARR | 1.5× | 3.0× | 4.5× |

![VALUERAQ default ARR multiple range, midpoint: AI business 3x, SaaS business 3.5x](/static/img/articles/how-to-value-a-tech-company-default-arr-ranges.svg){: width="720" height="180" loading="lazy" }

These are "VALUERAQ's default range" and nothing more. They are the starting point before the adjustments in the next step. For deeper reading on how the range behaves, see [SaaS valuation multiples](/guides/saas-valuation-multiples/) and [AI business valuation](/guides/ai-business-valuation/).

## Step 4: Adjust for what is specific to your company

The default range assumes an average company. Your company is not average, and a buyer will move the multiple up or down for the reasons below. The tool applies fixed, published rules, so you can reproduce the result by hand.

| Factor | What moves the multiple up | What moves it down |
|---|---|---|
| Revenue trend | Growth above 5% (+8%), above 25% (+15%) | Decline of more than 5% (−12%), more than 20% (−25%) |
| Churn (SaaS and AI) | Under 2% a month (+10%) | Over 5% a month (−10%), over 8% (−20%) |
| Gross margin (SaaS and AI) | Above 80% (+5%) | Under 70% (−7%), under 50% (−15%) |
| Customer concentration | 15% or less from one customer (no change) | More than 15% (−6%), more than 30% (−12%) |
| Owner involvement | Under 10 hours a week (+5%) | Over 20 hours (−5%), over 40 hours (−10%) |
| Business age | Four years or more (+5%) | One to two years (−10%) |

Each effect is a percentage change to the multiple, and the effects multiply. The model caps the combined change between −50% and +40%. The full list of rules is on the [methodology](/methodology/) page.

Buyers care about these because they are proxies for how long the revenue will last. The Corporate Finance Institute describes the Rule of 40 as "Revenue Growth Rate (%) + Profit Margin (%)" and notes it "oversimplifies a company's financial prospects by focusing on just two metrics" ([Corporate Finance Institute](https://corporatefinanceinstitute.com/resources/valuation/rule-of-40)). Use it as a quick check, then look at churn and concentration, which it ignores. Our [Rule of 40](/glossary/rule-of-40/) entry explains the arithmetic.

## Step 5: Cross-check and write down the range

Never rely on one number. After you have a value, do these checks:

- **Value a second way.** If you used ARR, divide the midpoint by annual profit. If the result is a very high multiple of profit, the value depends on growth that must still happen.
- **Check the story against the numbers.** A buyer who sees 30% growth in your pitch will ask for the monthly figures behind it.
- **Look for hidden costs.** Old code, missing documentation and unpatched systems reduce what a buyer will pay. See [technical debt](/glossary/technical-debt/).
- **Quote a range, not a point.** A low, midpoint and high value is more honest than one figure.

## Worked example 1: a stronger subscription software company

A small SaaS company has $20,000 MRR, 30% revenue growth over the last twelve months, 3% monthly churn, 82% gross margin, its largest customer is 10% of revenue, it is three years old and the owner works 15 hours a week.

**Base number:** ARR = 20,000 × 12 = **$240,000**.

**Adjustments from the table:**

| Factor | Value | Effect |
|---|---|---|
| Age | 3 years | 0% (baseline) |
| Revenue trend | +30% | +15% |
| Owner involvement | 15 hours | 0% (baseline) |
| Customer concentration | 10% | 0% |
| Churn | 3% | 0% (baseline) |
| Gross margin | 82% | +5% |

Combined factor = 1.15 × 1.05 = 1.2075.

**Adjusted multiples:** low 2.0 × 1.2075 = 2.42×, midpoint 3.5 × 1.2075 = 4.23×, high 5.0 × 1.2075 = 6.04×.

| Case | Multiple | Value on $240,000 ARR |
|---|---|---|
| Low | 2.42× | $580,800 |
| Midpoint | 4.23× | $1,015,200 |
| High | 6.04× | $1,449,600 |

Each value is $240,000 times the multiple, for example 240,000 × 4.23 = 1,015,200.

## Worked example 2: a weaker company with the same kind of product

Another SaaS company has $10,000 MRR, flat revenue, 6% monthly churn, 60% gross margin, a customer that makes up 35% of revenue, a business age of one year and an owner working 40 hours a week.

**Base number:** ARR = 10,000 × 12 = **$120,000**.

| Factor | Value | Effect |
|---|---|---|
| Age | 1 year | −10% |
| Revenue trend | 0% | 0% (baseline) |
| Owner involvement | 40 hours | −5% |
| Customer concentration | 35% | −12% |
| Churn | 6% | −10% |
| Gross margin | 60% | −7% |

Combined factor = 0.90 × 0.95 × 0.88 × 0.90 × 0.93 = 0.63 (rounded).

**Adjusted multiples:** low 2.0 × 0.63 = 1.26×, midpoint 3.5 × 0.63 = 2.20×, high 5.0 × 0.63 = 3.15×.

| Case | Multiple | Value on $120,000 ARR |
|---|---|---|
| Low | 1.26× | $151,200 |
| Midpoint | 2.20× | $264,000 |
| High | 3.15× | $378,000 |

![Adjusted midpoint multiple of ARR (two examples): Weaker SaaS 2.2x, Stronger SaaS 4.23x](/static/img/articles/how-to-value-a-tech-company-example-midpoints.svg){: width="720" height="180" loading="lazy" }

The two businesses use the same default range, and the midpoint multiple differs by almost a factor of two (4.23× against 2.20×). Most of that gap comes from the buyer's view of risk, not from the product.

## Worked example 3: a small IT services firm

A services firm has no recurring subscriptions. It bills clients for projects and support. Revenue was $500,000 in the last twelve months. Net profit was $70,000.

| Step | Amount |
|---|---|
| Net profit | $70,000 |
| + Owner's pay | $100,000 |
| + Depreciation | $3,000 |
| + One-off legal bill | $7,000 |
| **SDE** | **$180,000** |

Check: 70,000 + 100,000 + 3,000 + 7,000 = 180,000.

If the owner also leads delivery and a replacement would cost $85,000 a year, a buyer who will hire that person looks at 180,000 − 85,000 = **$95,000**.

VALUERAQ has no default range for services firms, so the multiples below are what-if figures for the arithmetic. They are not market data and not a VALUERAQ default.

| What-if multiple of SDE | Value on $180,000 SDE |
|---|---|
| 2.0× | $360,000 |
| 2.5× | $450,000 |
| 3.0× | $540,000 |

Each line is $180,000 times the multiple. Ask an accountant or a business broker for comparable sales before you set an asking price.

## What a buyer will ask to see

A buyer of a tech company checks the same story from several angles. Have these ready:

- Twelve to twenty-four months of revenue by month, split into recurring and one-off.
- A customer list with each customer's share of revenue, start date and plan.
- Churn by month, and how you calculate it. Stripe defines churn as "the percentage of total customers who discontinue using a product or service during a given period" ([Stripe](https://stripe.com/resources/more/essential-saas-metrics)).
- A profit and loss statement with a written list of add-backs.
- Hosting, software and contractor costs, to show real gross margin.
- A note on who owns the code, domains, accounts and customer data, and where they are stored.
- A description of what the owner does each week and who could take it over. See [key person risk](/glossary/key-person-risk/).

Our [SaaS metrics buyers check](/guides/saas-metrics-buyers-check/) guide goes through the numbers buyers look at first. The U.S. Small Business Administration also advises anyone buying a business to carry out a "thorough, objective investigation" and to "consider hiring an attorney and an accountant" ([SBA](https://www.sba.gov/business-guide/plan-your-business/buy-existing-business-or-franchise)).

## Where a calculator helps and where it does not

A calculator is the fastest way to test the arithmetic above. {{BRAND}}'s [SaaS valuation calculator](/calculators/saas-valuation-calculator/) takes MRR, growth, churn, gross margin and the other inputs in the table and returns a low, midpoint and high value, and the [SaaS valuation tool](/tools/saas-valuation/) shows each adjustment. It is built for subscription software and AI businesses. For a services firm, use the SDE arithmetic in example 3 and treat any figure as a starting point.

No calculator knows your contracts, your code or your team. Use it to get a defensible range, then ask a professional to check it before you sign anything.

## Frequently asked questions

### What is the fastest way to value a tech company?

For subscription software, multiply monthly recurring revenue by twelve to get ARR, then multiply by a range that reflects growth, churn and margin. For a services firm, calculate SDE and apply a range of multiples. Either way, quote a range, not a single number.

### Do tech companies sell for a multiple of revenue or profit?

Subscription software is often discussed as a multiple of ARR, because recurring revenue is the clearest sign of future income. Services firms, apps and many small products are priced on profit. Our guide on [revenue vs profit multiples](/guides/revenue-vs-profit-multiples/) explains when each applies.

### Why do two similar tech companies have different values?

Because buyers price risk. Churn, customer concentration, growth and owner workload change how long the revenue is likely to last. The two SaaS examples above start from the same default range and end at midpoint multiples of 4.23× and 2.20×.

### Can I value a tech company that is not making a profit?

Yes. Subscription businesses are often valued on ARR when profit is low or negative. The Corporate Finance Institute notes revenue-based multiples are used when a company has no positive EBITDA or net income, but that they ignore "profitability and cash flow generation" ([Corporate Finance Institute](https://corporatefinanceinstitute.com/resources/valuation/ev-to-revenue-multiple)). Expect buyers to push toward the low end of the range.

## Sources

- [Stripe, Essential SaaS metrics](https://stripe.com/resources/more/essential-saas-metrics)
- [Corporate Finance Institute, Multiples analysis](https://corporatefinanceinstitute.com/resources/valuation/multiples-analysis)
- [Corporate Finance Institute, Rule of 40](https://corporatefinanceinstitute.com/resources/valuation/rule-of-40)
- [Corporate Finance Institute, EV to revenue multiple](https://corporatefinanceinstitute.com/resources/valuation/ev-to-revenue-multiple)
- [BizBuySell, Add-Backs for Seller's Discretionary Earnings](https://www.bizbuysell.com/learning-center/article/add-backs-sde/)
- [U.S. Small Business Administration, Buy an existing business or franchise](https://www.sba.gov/business-guide/plan-your-business/buy-existing-business-or-franchise)
- {{BRAND}}, [methodology](/methodology/)

This guide is general information, not financial, tax or legal advice. Ask an accountant or lawyer before you buy or sell.
