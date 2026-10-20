---
title: What Is Revenue Churn?
term: Revenue Churn
aliases: revenue churn, gross revenue churn, net revenue churn, MRR churn, dollar churn
meta_title: Revenue Churn: Definition, Formula & Example
meta_description: Revenue churn is the share of recurring revenue lost in a period. See gross vs net revenue churn, a worked example and why buyers of SaaS businesses check it.
h1: Revenue Churn
definition: Revenue churn is the share of a subscription business's recurring revenue that is lost in a period through cancellations and downgrades, usually measured monthly against the revenue at the start of that period.
cluster: saas
page_type: reference
keywords: revenue churn, gross revenue churn, net revenue churn, mrr churn, revenue churn rate
related: /glossary/churn/, /glossary/mrr/, /glossary/expansion-revenue/, /glossary/net-revenue-retention/, /glossary/retention-rate/, /tools/saas-valuation/, /guides/saas-valuation/
updated: 2026-10-20
publish_at: 2026-10-20T19:00Z
image: /static/img/articles/revenue-churn.png
image_alt: Featured image for the glossary entry What Is Revenue Churn
score: 8.6
---

## How it works

Revenue churn counts dollars, not customers. Start with the [MRR](/glossary/mrr/) at the beginning of the month and ask how much of it has gone by the end. There are two versions:

**Gross revenue churn = (MRR lost to cancellations + MRR lost to downgrades) ÷ MRR at the start of the month**

**Net revenue churn = (MRR lost − [expansion revenue](/glossary/expansion-revenue/)) ÷ MRR at the start of the month**

Gross churn ignores anything the existing customers added. Net churn subtracts upgrades and extra seats from the same customers, so it can fall below zero when expansion is larger than the losses. New customers are left out of both figures.

Stripe's guide to SaaS metrics defines the related idea of net revenue retention as "The percentage of revenue that is retained from existing customers over a given period of time" ([Stripe](https://stripe.com/resources/more/essential-saas-metrics)). Revenue churn is the other side of that measure.

## Example

A SaaS business starts the month with $20,000 of MRR. During the month, cancellations remove $700 and downgrades remove $300. Existing customers add $500 through upgrades. The numbers are an illustration, not a market figure.

- **Gross revenue churn** = ($700 + $300) ÷ $20,000 = **5%**
- **Net revenue churn** = ($1,000 − $500) ÷ $20,000 = **2.5%**

Gross churn of 5% a month compounds. Over 12 months, (1 − 0.05)¹² is about 0.54, so roughly 46% of the starting revenue would be gone if nothing were added.

## Why it matters in a valuation

Recurring revenue is only worth what stays. Buyers of SaaS businesses ask for monthly revenue churn over at least a year, split into cancellations and downgrades, and they compare gross and net. A low gross figure shows customers rarely leave. A low net figure with a high gross one means the business depends on upgrades to cover steady losses.

VALUERAQ's [SaaS valuation tool](/tools/saas-valuation/) asks for monthly churn and adjusts the multiple of annual recurring revenue (its default range is 2.0x to 5.0x, explained in the [methodology](/methodology/)). It does not model net revenue retention, so a business with strong expansion should explain that to buyers separately.

## Related terms

[Churn](/glossary/churn/) covers customer churn as well as revenue churn. [Net revenue retention](/glossary/net-revenue-retention/) is the matching retention measure. [Retention rate](/glossary/retention-rate/) shows the share of customers or revenue kept.
