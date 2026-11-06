---
title: How to Value an AI Business
meta_title: How to Value an AI Business: Steps, Metrics, Example
meta_description: Value an AI business in five steps: the metrics buyers check, a worked example and the mistakes to avoid. Includes a free AI valuation tool with no sign-up.
h1: How to Value an AI Business
section: Valuation
cluster: ai
order: 3
answer: Small AI businesses with subscription revenue are usually valued like SaaS, on a multiple of ARR or annual profit. Buyers then look harder at three AI-specific risks: dependence on third-party model providers, gross margins squeezed by inference costs, and churn once early curiosity fades. Strong evidence on all three supports a higher multiple.
published: 2026-09-30
updated: 2026-11-06
methodology_version: 1.0
related: /tools/ai-business-valuation/, /businesses-for-sale/ai-businesses/, /guides/saas-valuation/, /glossary/gross-margin/, /glossary/churn/
cta: /tools/ai-business-valuation/
cta_text: Estimate an AI business's value, including model dependence and gross margin, with the free AI Business Valuation Tool.
---

## Key takeaway

AI business valuation is the process of estimating the value of a business whose core product relies on machine-learning models. The arithmetic is the same as for SaaS, **ARR × multiple**, but the multiple has to account for risks that ordinary software businesses don't face in the same way.

## What counts as an AI business

For valuation purposes, an AI business is one whose value would largely disappear without the models it uses. Common types:

- **AI SaaS:** a subscription product built around a model, such as an AI writing, design, coding or research tool.
- **AI APIs:** services that other developers call, often wrapping one or more models with extra processing.
- **AI agents and automation:** products that complete tasks, such as handling support tickets or processing documents.
- **Owned-model businesses:** companies that train or fine-tune their own models on proprietary data.

## The AI-specific questions that set the multiple

### How much of the product does the business own?

If the product is mostly a prompt and an interface on top of a general-purpose model, a competitor or the model provider could replicate it. Value comes from what the business adds: proprietary data, integrations into customers' workflows, distribution, domain expertise built into the product, and brand.

### How exposed is the margin to model costs?

Inference costs (the price of running a model for each request) can take a large share of revenue. Buyers want [gross margin](/glossary/gross-margin/) tracked month by month and cost per active user, and they'll ask what happens if model prices change. Model prices have fallen for many uses, but the business should show it can cope if prices or usage patterns move against it.

### How dependent is it on one provider?

A product that relies on a single provider is exposed to that provider's pricing, rate limits, terms of service and model changes. Products that can switch between providers, or run their own models, carry less of this risk.

### Does usage last?

Many AI products attract strong early sign-ups followed by high churn. Retention by monthly cohort, three and six months after sign-up, shows whether customers keep finding value.

## How the valuation is calculated

1. **ARR** = MRR × 12.
2. **Base multiple:** {{BRAND}} starts AI businesses at 1.5× to 4.5× ARR, slightly below its SaaS default of 2× to 5×. The difference is an editorial assumption reflecting shorter histories and margin uncertainty; see [data sources](/data-sources/).
3. **Adjustments** for growth, churn, gross margin, provider dependence, customer concentration, age and owner time, published in the [methodology](/methodology/#adjustments).
4. **Range** = ARR × adjusted multiples, with the implied profit multiple as a cross-check.

## Worked example

A hypothetical AI writing tool is 18 months old with $12,000 MRR ($144,000 ARR), growing 60% a year. It keeps $4,000 a month as profit, loses 6% of customers a month, has a 62% gross margin after model costs, relies on one model provider, and the founder works 30 hours a week on it.

Fast growth lifts the multiple by 15%. Against that, the short history (−10%), high churn (−10%), below-software gross margin (−7%), single-provider dependence (−10%) and heavy owner involvement (−5%) pull it down. The combined adjustment is roughly −26%, giving about 1.1× to 3.3× ARR: roughly $160,000 to $480,000. The same revenue in a mature SaaS business with low churn and high margins would support a noticeably higher range. The [AI Business Valuation Tool](/tools/ai-business-valuation/) opens with this example.

## The metrics buyers ask for

| Metric | How to work it out | Why a buyer asks |
|---|---|---|
| Gross margin after model costs | (revenue − model, API, hosting and payment costs) ÷ revenue | Shows how much of each dollar is kept |
| Cost to serve one customer | Monthly model and hosting cost ÷ active customers | Reveals whether heavy users lose money |
| Provider dependence | Share of usage on each model provider | Measures exposure to one supplier's price or terms |
| Churn by cohort | Customers lost each month, grouped by sign-up month | Separates early curiosity from lasting use |
| Data and integrations | What a competitor could not copy quickly | Supports a higher multiple |

Example: a product with $12,000 of MRR spends $4,560 a month on model usage and hosting. Gross margin = ($12,000 − $4,560) ÷ $12,000 = 62%. With 400 paying customers, the cost to serve is $4,560 ÷ 400 = $11.40 per customer per month.

## Why venture-scale multiples do not apply to a small AI business

Valuations reported for very large AI companies reflect funding rounds, big teams and expected growth over many years. A small AI tool bought by an individual or a small company is priced mostly on the income it produces and the risk of losing it. That is why {{BRAND}}'s default for AI businesses is 1.5x to 4.5x ARR, below its SaaS default of 2x to 5x. A multiple quoted for a large AI company says something about that company. It does not set a target for yours.

## Step by step

1. **Gather twelve months** of revenue, model costs and profit, month by month.
2. **Calculate ARR** (MRR × 12) and annual profit.
3. **Measure gross margin** after all model, hosting and payment costs.
4. **Find churn by cohort** and the largest customer's share of revenue.
5. **List the dependencies:** the model providers, the data and the platforms the product runs on.
6. **Run the tool** and read the adjustments one by one.
7. **Cross-check** the ARR range against the profit multiple and an estimate of the rebuild cost. See [AI business valuation methods](/guides/ai-business-valuation-methods/).

## Evidence that raises an AI business's value

- Cohort retention showing customers stay beyond the first few months.
- Stable or improving gross margin over at least six months.
- A tested fallback to a second model provider.
- Proprietary data or integrations competitors can't easily copy.
- Clear rights to all training data and compliance with the providers' terms.
- Documented prompts, evaluation tests and deployment steps, so a new owner can maintain quality.

## Limitations

AI markets change quickly: new models can make a product obsolete or much cheaper to run. No valuation model can predict that. Technical defensibility and data rights need expert review that a calculator can't provide. {{BRAND}}'s estimates are starting points, not appraisals.

## Frequently asked questions

### Are AI businesses valued higher than SaaS?

Not by default. Rapid growth can justify a high price, but short histories, thin margins and provider dependence often offset it. Compare on the same metrics.

### Is a "wrapper" business worth buying?

It can be, if it has customers who stay, a distribution advantage, or workflow integrations that make switching costly. Price in the risk that a general-purpose tool could replace it.

### How should I report model costs?

Include all model and API usage, GPU or hosting costs, and any data costs in cost of revenue. Report gross margin monthly so buyers can see the trend.

### What documents should I prepare to sell an AI business?

Billing records for twelve months, a monthly cost breakdown by model provider, cohort retention, the terms of each provider you use, and a note of who owns the training data and prompts. See [the documents buyers ask for](/guides/what-documents-do-buyers-ask-for/).

### How much does the owner's time matter?

In {{BRAND}}'s tool, more than 40 hours a week lowers the range by 10%, and under 10 hours raises it by 5%. A product that depends on its builder is harder to hand over.

### Can an AI business be valued with no profit?

Yes, on ARR, but expect the buyer to focus on margin and churn. Loss-making products are often priced toward the low end of the range. See [how to value a business with no profit](/guides/how-to-value-a-business-with-no-profit/).
