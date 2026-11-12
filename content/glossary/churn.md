---
title: What Is Churn?
term: Churn
aliases: churn rate, customer churn, revenue churn
meta_title: Churn Rate Formula: Yearly Loss Table & Value Impact
meta_description: Churn is the share of customers or revenue lost each month. Get the formula, a yearly loss table and a worked example of how churn moves a SaaS value.
h1: Churn Rate
definition: Churn is the share of customers, or of recurring revenue, that a subscription business loses over a period, usually measured monthly.
cluster: saas
related: /glossary/mrr/, /glossary/ltv/, /tools/saas-valuation/, /guides/saas-valuation/, /glossary/revenue-churn/, /guides/saas-metrics-buyers-check/
updated: 2026-11-12
---

## Formulas

**Customer churn (monthly) = customers lost during the month ÷ customers at the start of the month**

**Revenue churn (monthly) = MRR lost to cancellations and downgrades ÷ MRR at the start of the month**

Customer churn counts people; revenue churn counts dollars. If larger customers are more loyal than smaller ones, revenue churn will be lower than customer churn.

## Example

A business starts the month with 500 customers and loses 15.

**Monthly customer churn = 15 ÷ 500 = 3%.**

## Why churn compounds

Monthly churn applies to a shrinking base each month, so the annual effect is:

**Customers remaining after 12 months = (1 − monthly churn)¹²**

| Monthly churn | Customers lost over a year (approx.) |
|---|---|
| 1% | 11% |
| 3% | 31% |
| 5% | 46% |
| 8% | 63% |

These are arithmetic results, not benchmarks.

A business starting with 1,000 customers and losing 3% a month keeps 1,000 × 0.97¹² ≈ 694 of them after a year, so it must add about 306 new customers just to stand still.

## Customer churn or revenue churn?

| | Customer churn | Revenue churn |
|---|---|---|
| Counts | Accounts that leave | Dollars of MRR lost |
| Best for | Spotting a product or onboarding problem | Seeing what leaving costs in money |
| Watch out for | Hides that one large customer left | Can look good if a few big customers stay |

Buyers usually ask for both, month by month, for at least 12 months.

## Why churn matters for valuation

High churn means a business must win many new customers just to keep revenue flat, so buyers pay less for each dollar of recurring revenue. {{BRAND}}'s [SaaS](/tools/saas-valuation/) and [AI](/tools/ai-business-valuation/) tools raise the multiple for monthly churn under 2% and lower it for churn above 5%.

Churn also sets customer lifetime: an average lifetime of roughly 1 ÷ monthly churn months, which feeds into [LTV](/glossary/ltv/).

## Worked example: what churn does to a price

A SaaS business has $20,000 in MRR, so ARR is $20,000 × 12 = $240,000. Using {{BRAND}}'s default SaaS midpoint of 3.5 times ARR and changing only the churn adjustment (the other factors are ignored here):

| Monthly churn | Adjustment | Multiple | Value |
|---|---|---|---|
| Under 2% | +10% | 3.5 × 1.10 = 3.85 | $240,000 × 3.85 = $924,000 |
| 2% to 5% | none | 3.50 | $240,000 × 3.5 = $840,000 |
| Over 5% to 8% | −10% | 3.5 × 0.90 = 3.15 | $240,000 × 3.15 = $756,000 |
| Over 8% | −20% | 3.5 × 0.80 = 2.80 | $240,000 × 2.8 = $672,000 |

The adjustments are platform assumptions, set out in the [methodology](/methodology/), not market data. Real prices depend on the whole deal.

## Customer lifetime from churn

At 3% monthly churn the average customer stays about 1 ÷ 0.03 ≈ 33 months. At 5% it is 20 months. That is why a point or two of churn changes [LTV](/glossary/ltv/) so much.

## Frequently asked questions

### What is a good churn rate?

There is no single answer, because it depends on price, customer size and product type. Compare your own trend month to month, and note that {{BRAND}}'s tools treat under 2% a month as a positive and over 5% as a concern.

### Is churn the same as cancellations?

Cancellations are part of it. Revenue churn also counts downgrades, and some definitions include failed payments that are never recovered. State which one you use.

### How do I lower churn before selling?

Find out why customers leave, fix onboarding, and move monthly customers to annual plans where it suits them. Buyers also like to see a steady trend over at least 12 months.

See also [revenue churn](/glossary/revenue-churn/) for the dollar version, and [SaaS metrics buyers check](/guides/saas-metrics-buyers-check/) for how buyers read churn alongside margin and growth.
