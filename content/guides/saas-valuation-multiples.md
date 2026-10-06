---
title: SaaS Valuation Multiples: What They Are and How to Use Them
meta_title: SaaS Valuation Multiples Explained, with Examples
meta_description: What a SaaS valuation multiple is, why the same revenue can earn 1.75 or 4.9 times ARR, and how to check a multiple against profit before you rely on it.
h1: SaaS Valuation Multiples: What They Are and How to Use Them
section: Valuation
cluster: saas
order: 60
page_type: article
answer: A SaaS valuation multiple is the number you multiply annual recurring revenue (ARR) by to estimate what a subscription software business is worth. VALUERAQ's default range for a small SaaS business is 2.0 to 5.0 times ARR, and growth, churn, gross margin, customer concentration, age and owner workload move a business up or down from there.
keywords: saas valuation multiples, saas revenue multiples, saas company valuation multiples, saas ebitda multiples, saas valuation
published: 2026-10-07
updated: 2026-10-07
publish_at: 2026-10-07T01:00Z
image: /static/img/articles/saas-valuation-multiples.png
image_alt: Featured image for the guide SaaS Valuation Multiples, What They Are and How to Use Them
score: 9.0
related: /tools/saas-valuation/, /calculators/saas-valuation-calculator/, /guides/saas-valuation/, /guides/saas-valuation-methods/, /glossary/arr/, /glossary/churn/
cta: /tools/saas-valuation/
cta_text: Enter your MRR, growth, churn and margin to see the multiple your business earns.
---

## Key takeaway

Two SaaS businesses with the same revenue can deserve very different multiples. In the examples below, $120,000 of ARR is valued at a midpoint of 3.78 times in one case and 1.75 times in another, a gap of $244,000. The multiple is a summary of how long the revenue is likely to last and how much of it turns into profit. Read it that way and it becomes useful. Quote it without that context and it misleads.

All figures here come from the [SaaS valuation tool](/tools/saas-valuation/) using {{BRAND}}'s published default assumptions. They are estimates, not records of real sales.

## What a SaaS multiple is

**Value = ARR × multiple**

[ARR](/glossary/arr/) is annual recurring revenue: current monthly recurring revenue ([MRR](/glossary/mrr/)) multiplied by 12. Stripe describes ARR as the money a company can expect to receive from its existing customers during a year. One-off fees, setup charges and services are left out.

SaaS is valued on revenue more often than other small businesses because subscription income repeats. A customer paying this month will probably pay next month. That makes the revenue itself a reasonable guide to the future, in a way that a store's sales or a blog's ad income is not.

The Corporate Finance Institute notes that revenue multiples are used when a company has little or no profit, which is common for software businesses that spend on growth. It also lists the main weakness: a revenue multiple "ignores profitability and cash flow generation." The rest of this guide is about working around that weakness.

## The default range and what moves it

{{BRAND}} starts every small SaaS business at 2.0 (low), 3.5 (midpoint) and 5.0 (high) times ARR. Six rules then adjust it.

| Factor | Lowers the multiple | Raises it |
|---|---|---|
| Monthly churn | Over 8%: −20%. Over 5% to 8%: −10% | Under 2%: +10% |
| Revenue trend, last 12 months | Down over 20%: −25%. Down 5% to 20%: −12% | Up 5% to 25%: +8%. Up 25% to 75%: +15%. Above 75%: +20% |
| Gross margin | Under 50%: −15%. 50% to under 70%: −7% | Above 80%: +5% |
| Largest customer's share of revenue | Over 30%: −12%. Over 15% to 30%: −6% | No bonus; 15% or less is the baseline |
| Business age | Under 1 year: −20%. 1 to 2 years: −10% | 4 years or more: +5% |
| Owner hours a week | Over 40: −10%. 20 to 40: −5% | Under 10: +5% |

The percentages are multiplied together, and the total is limited to between 0.5 and 1.4. So the lowest possible range is 1.0 to 2.5 times ARR and the highest is 2.8 to 7.0.

These are editorial assumptions set out in the [methodology](/methodology/). They are not averages from a transaction database.

## Three businesses, three multiples

### A steady business

MRR is $10,000, so ARR is $120,000. The business is three years old and revenue is up 15% on last year. Monthly [churn](/glossary/churn/) is 3% and gross margin is 78%. The largest customer is 5% of revenue and the founder works 15 hours a week.

- Adjustments: revenue trend +8%, everything else at the baseline
- Adjustment factor: 1.08
- Multiple: 2.16 low, 3.78 midpoint, 5.40 high
- **Value: $259,000 to $648,000, midpoint $454,000**

### A strong business

MRR is $25,000, so ARR is $300,000. The business is five years old and growing 40% a year. Churn is 1.5% a month and gross margin is 85%. No customer is above 4% and the founder works 8 hours a week.

- Adjustments: age +5%, trend +15%, owner hours +5%, churn +10%, margin +5%
- Adjustment factor: 1.05 × 1.15 × 1.05 × 1.10 × 1.05 = 1.46, limited to 1.40
- Multiple: 2.80 low, 4.90 midpoint, 7.00 high
- **Value: $840,000 to $2,100,000, midpoint $1,470,000**

### A leaky business

MRR is $10,000, so ARR is $120,000, the same as the first example. The business is 18 months old and revenue is down 8%. Churn is 9% a month and gross margin is 60%. One customer provides 20% of revenue and the founder works 45 hours a week.

- Adjustments: age −10%, trend −12%, owner hours −10%, concentration −6%, churn −20%, margin −7%
- Adjustment factor: 0.90 × 0.88 × 0.90 × 0.94 × 0.80 × 0.93 = 0.50, the lower limit
- Multiple: 1.00 low, 1.75 midpoint, 2.50 high
- **Value: $120,000 to $300,000, midpoint $210,000**

![Midpoint ARR multiple in each example: Leaky business 1.75x, Default midpoint 3.5x, Steady business 3.78x, Strong business 4.9x](/static/img/articles/saas-valuation-multiples-midpoints.svg){: width="720" height="272" loading="lazy" }

| | Steady | Strong | Leaky |
|---|---|---|---|
| ARR | $120,000 | $300,000 | $120,000 |
| Midpoint multiple | 3.78 | 4.90 | 1.75 |
| Midpoint value | $454,000 | $1,470,000 | $210,000 |
| Yearly profit | $48,000 | $144,000 | $24,000 |
| Midpoint as a multiple of profit | 9.5 | 10.2 | 8.8 |

## Why churn carries the most weight

Churn decides how long each dollar of ARR lasts. At 3% a month, a business keeps about 69% of its customers after a year. At 9% a month it keeps about 32%, so it must replace two thirds of its customer base every year to stand still.

The sums are simple: 0.97 multiplied by itself 12 times is 0.69, and 0.91 multiplied by itself 12 times is 0.32.

A buyer of the leaky business is mostly buying a sales treadmill. That is why churn above 8% a month carries a 20% cut, the same as for a business under a year old. Only a steep fall in revenue costs more.

## Always check the multiple against profit

A revenue multiple can hide a business that makes almost nothing. The last row of the table above is the cross-check: the midpoint value divided by yearly profit.

In all three examples the result is around 9 to 10 times profit. A buyer who thinks in profit terms will compare that with the 2.5 to 4.0 times profit in our default range for a content website and ask what justifies the difference. The answer has to be growth and retention. If neither is present, the ARR multiple is too high, whatever the table says.

Two practical rules follow:

- **For a very small SaaS business, think in profit.** A buyer who plans to live on the income will price on what the business pays its owner. The [SaaS valuation methods guide](/guides/saas-valuation-methods/) compares the two approaches.
- **If profit is negative, say why.** Losses from deliberate growth spending can be defended. Losses because the product costs more to run than it earns cannot.

## Why public-company multiples don't apply

Headlines quote revenue multiples for large listed software companies. Those figures describe businesses with hundreds of staff, audited accounts, many thousands of customers and shares that can be sold any day. A small SaaS business has none of those protections. It usually depends on one founder, one acquisition channel and a few hundred customers, and its owner cannot sell on any given day the way a shareholder can.

Size, concentration and difficulty of selling all reduce what a buyer will pay. Starting from a public-company multiple and "applying a discount" gives a number with no real basis. Start instead from the business's own figures.

## How to use a multiple well

1. **Calculate ARR from current MRR,** and leave out one-off revenue.
2. **Gather the six inputs:** churn, growth, gross margin, largest customer, age and your weekly hours.
3. **Run them through the tool** and read the adjustment list, not only the result.
4. **Divide the midpoint by yearly profit** and ask whether growth and retention support the answer.
5. **If you are buying,** work backwards from an asking price with the [SaaS valuation calculator](/calculators/saas-valuation-calculator/), then verify churn and MRR from the billing system. The guide to [buying a SaaS business](/guides/how-to-buy-a-saas-business/) covers the checks.

## Frequently asked questions

### What is a good multiple for a small SaaS business?

There is no single good number. On {{BRAND}}'s assumptions a small SaaS business falls between 1.0 and 7.0 times ARR depending on six factors, with 3.5 as the default midpoint. A business with low churn and steady growth sits above the midpoint and one that is shrinking or leaking customers sits well below it.

### Is the multiple applied to ARR or to MRR?

Either, but the numbers differ by 12. A multiple of 3.5 times ARR equals 42 times MRR. Check which one is meant before comparing two figures.

### What about SaaS EBITDA multiples?

Profit multiples apply once a SaaS business is mature and reliably profitable. For a small owner-run business the profit figure is usually SDE, not EBITDA. See [SDE vs EBITDA](/guides/sde-vs-ebitda/) for the difference.

### Do AI products get the same multiples?

{{BRAND}} uses a lower default range for AI businesses, 1.5 to 4.5 times ARR, because many depend on an outside model provider for both cost and capability. The [AI business valuation tool](/tools/ai-business-valuation/) applies it.

### Does annual billing change the multiple?

Not directly. If yearly billing reduces cancellations in your business, that shows up as lower churn, and lower churn raises the multiple.

## Sources

- Stripe, [Essential SaaS metrics](https://stripe.com/resources/more/essential-saas-metrics): definitions of MRR, ARR, churn and net revenue retention.
- Corporate Finance Institute, [Enterprise Value to Revenue Multiple](https://corporatefinanceinstitute.com/resources/valuation/ev-to-revenue-multiple): when revenue multiples are used and their limits.
- {{BRAND}}, [Valuation methodology](/methodology/): the default ranges and every adjustment rule used in the examples.
