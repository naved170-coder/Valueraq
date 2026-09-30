---
title: App Valuation Tool
h1: App Valuation Tool
answer: The App Valuation Tool estimates what an iOS or Android app is worth as a multiple of its annual net profit, adjusted for age, growth, revenue model, platforms, acquisition-channel concentration and owner workload. It suits profitable consumer and utility apps earning from subscriptions, in-app purchases, ads or paid downloads.
updated: 2026-09-30
related: /guides/business-valuation/, /glossary/sde/, /glossary/churn/, /glossary/profit-multiple/
---

## What this tool does

App valuation is the process of estimating the value of a mobile application business from its earnings, user base and the risks attached to both. Small profitable apps usually change hands on a multiple of annual profit, so that is the method used here. The tool shows the base multiple, each adjustment and the resulting range.

Use it to price an app before listing it, to test a seller's asking price, or to see how switching revenue model or reducing ad dependence might affect value.

## Inputs you need

| Input | Why it matters | Required |
|---|---|---|
| Average monthly revenue | Checks the margin after store fees and costs | Yes |
| Average monthly net profit (SDE) | The base the multiple applies to | Yes |
| Business age and 12-month revenue trend | Durability and direction | No |
| Platforms | Presence on both stores reduces single-store risk | No |
| Revenue model | Subscriptions are more predictable than ads or one-off sales | No |
| Share of installs or revenue from the largest channel | Reliance on one ad network, one store feature or one keyword | No |
| Owner hours per week | Updates, support and store compliance take time | No |
| Monthly active users | Shown for context in your report | No |

Report revenue after app store commissions if that's how you receive it, and be consistent: profit should be revenue minus every cost, including paid user acquisition.

## How the valuation is calculated

1. **Annual profit** = average monthly profit × 12.
2. **Base multiple.** Apps start from [[ex:base_low]] to [[ex:base_high]] annual profit (midpoint [[ex:base_mid]]), a {{BRAND}} platform assumption. See [data sources](/data-sources/).
3. **Adjustments** for age, growth, platforms, revenue model, channel concentration and owner hours, listed in the [methodology](/methodology/#adjustments).
4. **Value range** = annual profit × adjusted multiples.

## Worked example

The hypothetical app in the form earns $9,000 a month and keeps $5,500 as profit. It is three years old, grows 5% a year, runs on iOS and Android, earns from subscriptions, gets 65% of installs from one channel and needs 12 owner hours a week.

- Annual profit: [[ex:metric]]
- Combined adjustment: × [[ex:factor]]
- Adjusted multiple: [[ex:mlow]] to [[ex:mhigh]]
- Estimated value: **[[ex:low]] to [[ex:high]]**, midpoint [[ex:mid]]

[[ex:adjustments]]

## What affects an app's value

**Platform risk.** Apps live inside Apple's and Google's stores and must follow their rules, fees and review processes. A policy change or a lost store feature can cut downloads quickly. Being on both platforms spreads that risk.

**Retention.** Monthly active users matter less than how many stay. Buyers ask for retention by install cohort, for example day 30 and day 90, and for subscription renewal rates.

**Acquisition cost.** If growth comes from paid ads, the buyer will compare cost per install with lifetime revenue per user. Profitable growth from organic search in the store, referrals or a brand is valued more highly.

**Technical condition.** An outdated codebase, deprecated SDKs or a single developer who wrote everything add work for a buyer. Clear documentation and a current build pipeline reduce it.

## Limitations

- The tool doesn't value apps with no profit or apps whose value lies in their technology or user base rather than earnings.
- It can't assess code quality, store account standing or intellectual property; those need due diligence.
- The base multiple is an editorial assumption, and results depend entirely on your inputs. It is not an appraisal.

## Frequently asked questions

### How much is my app worth?

Profitable small apps are commonly valued as a multiple of annual profit. With {{BRAND}}'s defaults that is about 2× to 3.5× before adjustments. Subscription apps with steady growth and low owner time sit higher in the range than ad-funded apps with falling downloads.

### Do downloads or active users set the value?

Not directly. They matter because they produce revenue and indicate how durable it is, but two apps with the same users can have very different profits. The tool records active users for context and values the earnings.

### Is an app with only iOS or only Android worth less?

Slightly, under this model: being on both platforms earns a small positive adjustment. The bigger factors are profit, growth, retention and how revenue is earned.

### What happens to my App Store account in a sale?

Transferring apps between developer accounts is handled through each store's app transfer process, and each store sets its own requirements. Check the current rules for both stores early, because they affect how the sale is structured.
