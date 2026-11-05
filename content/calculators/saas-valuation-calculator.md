---
title: SaaS Valuation Calculator
answer: This calculator gives a quick SaaS valuation from three numbers, MRR, annual growth and monthly churn. It converts MRR to ARR, starts from VALUERAQ's default ARR multiple range, adjusts it for growth and churn, and returns a low-to-high value range. For a fuller estimate that includes margins, customer concentration and owner time, use the SaaS Valuation Tool.
updated: 2026-11-05
related: /tools/saas-valuation/, /guides/saas-valuation/, /glossary/arr/, /glossary/mrr/, /glossary/churn/
---

## How the SaaS valuation calculator works

1. **ARR = MRR × 12.** Annual recurring revenue is the standard base for SaaS multiples.
2. **Base range.** {{BRAND}}'s default assumption for small SaaS businesses is 2× to 5× ARR, midpoint 3.5×. It is an editorial assumption, published on the [methodology page](/methodology/).
3. **Growth adjustment.** Revenue growth above 5% a year raises the multiple, in steps up to +20% for very fast growth. Decline lowers it, down to −25% for revenue falling more than 20%.
4. **Churn adjustment.** Monthly churn under 2% raises the multiple by 10%. Churn between 5% and 8% lowers it by 10%, and churn above 8% lowers it by 20%.
5. **Value range** = ARR × adjusted low, midpoint and high multiples.

The calculator uses the same engine as the [SaaS Valuation Tool](/tools/saas-valuation/) with fewer inputs, so its results are consistent with the full tool.

## Why growth and churn matter most

Growth and churn describe where revenue is heading. A SaaS business growing 30% a year with low churn will likely have noticeably more ARR next year, while one with high churn must win many new customers just to hold its revenue steady. Buyers pay for that difference.

Churn compounds. Monthly churn of 3% means losing roughly 31% of customers over a year; at 8% a month it is about 63%. See [churn](/glossary/churn/) for the calculation.

## Example

A SaaS business with $20,000 MRR, 30% annual growth and 3% monthly churn:

- ARR: $20,000 × 12 = $240,000
- Growth of 30% is in the "fast growth" band: +15% to the multiple.
- Churn of 3% is in the baseline band: no change.
- Adjusted range: 2.3× to 5.75× ARR, giving roughly $552,000 to $1,380,000, with a midpoint near $966,000.

The example result shown under the calculator is calculated live by the engine and matches these figures after rounding.

## Value at different ARR levels

Default ARR multiples before adjustments:

| ARR | MRR | Low (2.0×) | Midpoint (3.5×) | High (5.0×) |
|---|---|---|---|---|
| $60,000 | $5,000 | $120,000 | $210,000 | $300,000 |
| $120,000 | $10,000 | $240,000 | $420,000 | $600,000 |
| $250,000 | $20,833 | $500,000 | $875,000 | $1,250,000 |
| $500,000 | $41,667 | $1,000,000 | $1,750,000 | $2,500,000 |
| $1,000,000 | $83,333 | $2,000,000 | $3,500,000 | $5,000,000 |

## Two directions: value from metrics, or multiple from a price

This calculator goes from your metrics to a value. If you already have an asking price and want to know the multiple it implies, use the [business multiple calculator](/calculators/business-multiple-calculator/): enter the price and the revenue or profit, and it shows the ARR or profit multiple.

## How to improve your ARR multiple

1. **Reduce churn.** Under 2% a month adds 10% in the full [SaaS tool](/tools/saas-valuation/).
2. **Grow steadily.** Growth above 5% a year adds 8%, above 25% adds 15%.
3. **Protect gross margin.** Under 50% costs 15%.
4. **Spread revenue.** No customer above 15% of revenue avoids the concentration discount.
5. **Reduce owner time.** Under 10 hours a week adds 5%.

## What this calculator leaves out

Gross margin, customer concentration, business age, owner time and profitability all affect value and are included in the full [SaaS Valuation Tool](/tools/saas-valuation/). Net revenue retention, sales efficiency and contract terms also matter to buyers but aren't modelled here. The result is an estimate from your inputs and editorial assumptions, not an appraisal or financial advice.

## Frequently asked questions

### What ARR multiple do SaaS businesses sell for?

Multiples vary widely with size, growth, churn, profitability and buyer type, and published figures often describe large, venture-backed companies. {{BRAND}}'s default for small SaaS is 2× to 5× ARR before adjustments. We do not publish market averages we can't source; see [data sources](/data-sources/).

### Can I use this for a SaaS business that isn't profitable?

Yes, it values ARR. Buyers of small SaaS businesses often weight profit heavily, so a business with no profit may sell toward the low end of the range. The full tool shows the implied profit multiple.

### What is the difference between this calculator and the SaaS valuation tool?

This calculator gives a quick estimate from MRR, growth and churn. The [SaaS valuation tool](/tools/saas-valuation/) adds gross margin, customer concentration, age and owner time, and shows every adjustment.
