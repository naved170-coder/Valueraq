---
title: What Is Cohort Analysis?
term: Cohort Analysis
aliases: cohort analysis, cohort retention, customer cohorts
meta_title: Cohort Analysis: How to Read a Retention Table (Example)
meta_description: Cohort analysis tracks customers by start month. See a 6-month retention table, how buyers read it and what a falling cohort means for a SaaS price.
h1: Cohort Analysis
definition: Cohort analysis groups customers by when they joined and follows each group over time to show how many stay, how much they spend and how that changes.
cluster: saas
page_type: reference
keywords: cohort analysis, cohort retention, cohort analysis example, what is a cohort
related: /glossary/retention-rate/, /glossary/churn/, /glossary/net-revenue-retention/, /glossary/ltv/, /guides/saas-valuation/
updated: 2026-11-13
publish_at: 2026-10-18T07:00Z
image: /static/img/articles/cohort-analysis.png
image_alt: Featured image for the glossary entry What Is Cohort Analysis
score: 8.5
---

## How it works

A cohort is a group of customers who share a starting point, most often the month they first paid. Cohort analysis follows each group separately, month after month, and records how many are still paying.

A single blended [churn](/glossary/churn/) number can hide a lot. If a business is growing fast, new customers, who tend to leave sooner, are mixed in with older ones who rarely leave. Splitting by start month shows whether recent customers behave differently from earlier ones.

## Example

A subscription business tracks three monthly cohorts and counts customers still paying after three months.

| Cohort | Customers at start | Still paying after 3 months | Retention |
|---|---|---|---|
| January | 100 | 84 | 84% |
| February | 120 | 96 | 80% |
| March | 150 | 105 | 70% |

Retention after three months is falling: 84% to 80% to 70%. The blended figure across all three groups is (84 + 96 + 105) ÷ (100 + 120 + 150) = 285 ÷ 370 = 77%. That single number would look acceptable and hide the decline. The numbers are illustrative, not market data.

The same method works for revenue: group customers by start month and track the recurring revenue each group still pays after three, six and twelve months. Comparing groups of the same age is what makes the comparison fair.

## How buyers read a retention table

Here is a made-up table of customers still paying in each month after they joined.

| Cohort | Start | Month 1 | Month 2 | Month 3 | Month 6 |
|---|---|---|---|---|---|
| January | 100 | 92 | 88 | 84 | 75 |
| February | 120 | 108 | 101 | 96 | 84 |
| March | 150 | 120 | 110 | 105 | not yet |

Read each row from left to right to see how a group fades, and each column from top to bottom to compare groups of the same age. Here the January group keeps 75% by month 6 (75 ÷ 100). At month 3 the groups keep 84%, 80% (96 ÷ 120) and 70% (105 ÷ 150), so newer cohorts are leaving faster. A buyer reads three things: whether the curve flattens (a core of loyal customers), whether newer rows sit below older ones, and how many months of history each row has.

## Why it matters in a valuation

A buyer is paying for customers who stay. Cohorts show whether the customer base is getting stickier or leakier, and whether last year's customers are still around. A steady or improving pattern supports the case that revenue will continue. A worsening pattern, as in the example, is a reason for a buyer to lower the price or ask more questions.

VALUERAQ's [SaaS valuation tool](/tools/saas-valuation/) takes one monthly churn figure and does not read cohort data, so cohort tables are best prepared separately and shared with a buyer during due diligence.

## Frequently asked questions

### How many customers do I need for cohort analysis?

Enough that one customer leaving does not move the percentage much. With a handful of customers per cohort, group by quarter instead of by month.

### Is cohort analysis only for SaaS?

No. Any business with repeat customers can use it, including stores, memberships and newsletters. Group customers by first purchase or first sign-up.

### What is the difference between cohort retention and churn?

[Churn](/glossary/churn/) is a single rate for one period. A cohort table shows how each start group behaves over time, which can reveal changes a blended churn figure hides.

## Related terms

[Retention rate](/glossary/retention-rate/) is the share of customers kept. [Churn](/glossary/churn/) is the share lost. [LTV](/glossary/ltv/) estimates what a customer is worth over their time as a customer. [Net revenue retention](/glossary/net-revenue-retention/) tracks revenue from the same customers.
