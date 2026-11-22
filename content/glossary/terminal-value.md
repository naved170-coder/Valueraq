---
title: What Is Terminal Value?
term: Terminal Value
aliases: terminal value, TV, continuing value, terminal value in DCF
meta_title: What Is Terminal Value? Formula & Worked Example
meta_description: Terminal value is the worth of a business beyond the years you forecast. See the growth formula, a worked example and why it can dominate a DCF result.
h1: Terminal Value
definition: Terminal value is the estimated value today of all the cash a business is expected to produce after the last year of a forecast.
cluster: analysis
page_type: reference
keywords: terminal value, terminal value formula, terminal value in dcf, what is terminal value
publish_at: 2026-11-16T07:00Z
image: /static/img/articles/terminal-value.png
image_alt: Featured image for the glossary entry What Is Terminal Value
score: 8.6
related: /glossary/discounted-cash-flow/, /glossary/net-present-value/, /glossary/discount-rate/, /glossary/free-cash-flow-to-firm/, /glossary/capitalization-rate/, /glossary/cash-flow/
updated: 2026-11-16
---

## How it works

No one forecasts a business forever. A DCF forecasts a few years, then needs one number for everything after. That number is the terminal value. The Corporate Finance Institute describes DCF as a method "used to value investments by discounting the estimated future cash flows," and the terminal value is the last, largest piece of those cash flows.

A common way to set it assumes the cash flow grows at a small steady rate forever:

**Terminal value = last forecast year's cash flow × (1 + growth rate) ÷ (discount rate − growth rate)**

The result sits at the end of the forecast, so it must be discounted back to today like any other year. The growth rate must be lower than the [discount rate](/glossary/discount-rate/), and kept small, or the formula gives a very large or meaningless answer.

## Example

A buyer forecasts $40,000 of cash in year 3, the last forecast year. They use a 25% discount rate and assume 3% growth after that. The figures are made up.

| Step | Calculation | Result |
|---|---|---|
| Cash in year 4 | $40,000 × 1.03 | $41,200 |
| Terminal value at end of year 3 | $41,200 ÷ (0.25 − 0.03) | $187,273 |
| Discount back 3 years | $187,273 ÷ 1.25³ (1.953) | $95,883 |

If the three forecast years are worth $78,080 today (see [net present value](/glossary/net-present-value/)), the total is about $173,963, and terminal value makes up about 55% of it. Change the growth to 5% and terminal value becomes $42,000 ÷ 0.20 = $210,000, or $107,520 today.

## Why it matters in a valuation

Terminal value often accounts for more than half of a DCF result, so a small change in the growth rate or discount rate moves the price a lot. For a small website, app or store, the long-run assumptions are hard to defend, which is why many small deals use a [profit multiple](/glossary/profit-multiple/) instead. A multiple is a shortcut for the same idea: the [capitalization rate](/glossary/capitalization-rate/) is the flat-income version, where growth is zero. {{BRAND}} uses published default multiple ranges, as the [methodology](/methodology/) explains, and does not forecast a terminal value.

## Related terms

[Discounted cash flow](/glossary/discounted-cash-flow/), [net present value](/glossary/net-present-value/), [discount rate](/glossary/discount-rate/), [capitalization rate](/glossary/capitalization-rate/), [free cash flow to firm](/glossary/free-cash-flow-to-firm/).

Sources: Corporate Finance Institute, [DCF Formula](https://corporatefinanceinstitute.com/resources/valuation/dcf-formula-guide/).
