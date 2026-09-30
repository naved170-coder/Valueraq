---
title: SaaS Valuation Tool
h1: SaaS Valuation Tool
answer: The SaaS Valuation Tool estimates a software-as-a-service business's value as a multiple of its annual recurring revenue (ARR), adjusted for growth, churn, gross margin, customer concentration, age and owner involvement. It also shows the multiple of profit that the result implies, so you can compare it with how profit-focused buyers think.
updated: 2026-09-30
related: /guides/saas-valuation/, /glossary/arr/, /glossary/mrr/, /glossary/churn/, /guides/website-vs-saas-valuation/
---

## What this tool does

SaaS valuation is the process of estimating what a subscription software business is worth, usually by applying a multiple to its recurring revenue and adjusting for how durable and profitable that revenue is. This tool follows that approach for small and mid-sized SaaS businesses, such as bootstrapped products, micro-SaaS and plugins with subscription revenue.

It is designed for founders preparing to sell or raise money, buyers comparing SaaS listings, and operators who want to see which metrics move value most.

## Inputs you need

| Input | Why it matters | Required |
|---|---|---|
| Monthly recurring revenue (MRR) | The base of the calculation (ARR = MRR × 12) | Yes |
| Average monthly net profit | Used to show the implied profit multiple and flag loss-making businesses | No |
| Revenue change, last 12 months | Growth is one of the strongest value drivers for SaaS | No |
| Monthly customer churn | High churn means revenue has to be constantly replaced | No |
| Gross margin | Shows how much of each dollar is left after hosting and direct costs | No |
| Largest customer's share of revenue | Losing one big customer shouldn't sink the business | No |
| Business age and owner hours | Evidence of durability, and the work a buyer inherits | No |

Count only recurring subscription revenue in MRR. Exclude setup fees, one-off services and annual prepayments counted in the month received. For annual plans, divide the contract value by 12.

## How the valuation is calculated

1. **ARR.** MRR × 12.
2. **Base multiple.** SaaS starts from a default range of [[ex:base_low]] to [[ex:base_high]] ARR (midpoint [[ex:base_mid]]). This is a {{BRAND}} platform assumption for small SaaS businesses, not a measured market figure. See [data sources](/data-sources/).
3. **Adjustments** for growth, churn, gross margin, customer concentration, age and owner time. Each has a fixed effect published on the [methodology page](/methodology/#adjustments). Effects multiply, capped between −50% and +40%.
4. **Value range.** ARR × adjusted multiples.
5. **Cross-check.** If you enter profit, the tool divides the midpoint by annual profit. A very high result means the price depends on growth continuing.

## Worked example

The form opens with a hypothetical SaaS business: $20,000 MRR, $9,000 monthly profit, 30% annual growth, 3% monthly churn, 82% gross margin, no customer above 8% of revenue, three years old, 25 owner hours a week.

- ARR: $20,000 × 12 = [[ex:metric]]
- Combined adjustment: × [[ex:factor]]
- Adjusted ARR multiple: [[ex:mlow]] to [[ex:mhigh]] (midpoint [[ex:mmid]])
- Estimated value: **[[ex:low]] to [[ex:high]]**, midpoint [[ex:mid]]
- Implied multiple of annual profit at the midpoint: [[ex:implied]]

[[ex:adjustments]]

## What affects a SaaS business's value

**Growth.** Buyers pay more for revenue that is still rising. A business growing 30% a year is worth more per dollar of ARR than one that is flat, because next year's revenue is expected to be higher.

**Churn.** Monthly churn compounds. At 3% monthly churn a business loses roughly a third of its customers in a year and must replace them just to stand still; at 8% it loses most of them. Low churn is evidence that customers depend on the product.

**Gross margin.** Most software businesses keep a large share of each dollar after hosting and third-party costs. Products with heavy infrastructure, human service or API costs keep less, which leaves less profit for the buyer.

**Customer concentration.** If one customer pays 30% or more of revenue, a buyer is partly buying that one relationship.

**Profitability.** Many buyers of small SaaS businesses care about profit as much as ARR. A business with strong ARR but no profit usually sells toward the low end of its range.

## Limitations

- Venture-backed, high-growth SaaS companies are often valued on forward revenue and growth expectations that this tool does not model.
- Net revenue retention, expansion revenue and cohort data matter to buyers but aren't inputs here.
- The base multiple is an editorial assumption; real prices vary with deal terms and buyer type.
- The estimate relies entirely on your figures. It is not an appraisal or investment advice.

## Frequently asked questions

### How do you value a SaaS business?

Most small SaaS businesses are valued as a multiple of ARR or of annual profit, with the multiple set by growth, churn, margins and risk. This tool uses an ARR multiple and shows the profit multiple it implies, so you can see both views.

### What is a good ARR multiple?

There's no single figure. {{BRAND}}'s default assumption for small SaaS is 2× to 5× ARR before adjustments. Faster growth, lower churn and higher margins push a business toward the top of its range. Read [ARR](/glossary/arr/) and the [SaaS valuation guide](/guides/saas-valuation/) for more.

### Should I use MRR or ARR?

Both describe the same revenue. The tool asks for MRR because most billing systems report it, then converts it to ARR, which is the figure multiples are usually quoted against.

### What churn rate should I enter?

Enter the average share of paying customers who cancel in a month, over the last six to twelve months. If you track revenue churn instead of customer churn, enter that and note it in any listing.

### Is the tool suitable for AI SaaS?

It works, but the [AI Business Valuation Tool](/tools/ai-business-valuation/) adds an adjustment for dependence on third-party model providers, which affects AI products' margins and risk.
