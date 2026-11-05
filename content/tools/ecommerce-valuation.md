---
title: Ecommerce Valuation Tool
h1: Ecommerce Valuation Tool
answer: The Ecommerce Valuation Tool estimates what an online store is worth as a multiple of its annual net profit, adjusted for fulfillment model, sales-channel concentration, growth, age and owner workload, and then shows inventory at cost separately, because stock is usually paid for on top of the earnings-based price.
updated: 2026-11-05
related: /guides/business-valuation/, /glossary/sde/, /glossary/conversion-rate/, /glossary/customer-concentration/
---

## What this tool does

Ecommerce valuation is the process of estimating the value of an online store, whether a direct-to-consumer brand, a marketplace seller such as an Amazon FBA business, a dropshipping store or a print-on-demand shop, from its profit and the risks behind it. The tool applies a profit multiple, shows each adjustment and lists inventory as a separate figure.

It's built for store owners pricing a sale, buyers checking a listing and operators comparing stores with different fulfillment models.

## Inputs you need

| Input | Why it matters | Required |
|---|---|---|
| Average monthly revenue and net profit | Profit is the base; revenue shows margin | Yes |
| Inventory value at cost | Usually added to the price at closing | No |
| Fulfillment model | Own warehouse, third-party logistics or dropshipping | No |
| Share of sales from the largest channel | For example, one marketplace or one ad platform | No |
| Growth, age and owner hours | Direction, durability and workload | No |

Profit should be after cost of goods, shipping, platform and payment fees, advertising, returns and software, but before your own pay. Buyers will rebuild it from your statements, so use the same figures you would show them.

## How the valuation is calculated

1. **Annual profit** = average monthly profit × 12.
2. **Base multiple.** Ecommerce starts from [[ex:base_low]] to [[ex:base_high]] annual profit (midpoint [[ex:base_mid]]), a {{BRAND}} platform assumption. See [data sources](/data-sources/).
3. **Adjustments** for fulfillment, channel concentration, growth, age and owner hours, listed in the [methodology](/methodology/#adjustments).
4. **Value range** = annual profit × adjusted multiples.
5. **Inventory** at cost is shown separately and added to a second "including inventory" range.

## Worked example

The hypothetical store in the form turns over $40,000 a month and keeps $7,000 as profit. It holds $35,000 of stock at cost, uses a third-party logistics provider, makes 55% of sales through one channel, is five years old, grows 8% a year and needs 25 owner hours a week.

- Annual profit: [[ex:metric]]
- Combined adjustment: × [[ex:factor]]
- Adjusted multiple: [[ex:mlow]] to [[ex:mhigh]]
- Business value: **[[ex:low]] to [[ex:high]]**, midpoint [[ex:mid]]
- Including inventory at cost: [[ex:incl_low]] to [[ex:incl_high]]

[[ex:adjustments]]

## What affects an online store's value

**Margins and ad dependence.** Stores that need heavy advertising to generate each sale are exposed to rising ad costs. Buyers look at contribution margin after ad spend and at the share of repeat customers.

**Channel concentration.** A store that sells mostly through one marketplace depends on that marketplace's fees, rules and account health. Selling across your own site, marketplaces and wholesale reduces the risk.

**Supply chain.** Reliable suppliers, written agreements, reasonable lead times and more than one source for key products make a business easier to take over. Dropshipping stores depend on suppliers the buyer doesn't control, so the tool adjusts for it.

**Brand and product defensibility.** Trademarks, product designs, reviews on your own site and an email list are assets a buyer can build on. Easily copied products sold on price alone are worth less.

**Inventory condition.** Buyers pay for sellable stock, not slow-moving or obsolete items. Expect a stock count before closing.

## Quick value table

Default range for profitable online stores, before stock. Stock is added on top at cost.

| Monthly profit | Yearly profit | Low (2.0×) | Midpoint (2.7×) | High (3.5×) |
|---|---|---|---|---|
| $500 | $6,000 | $12,000 | $16,200 | $21,000 |
| $1,000 | $12,000 | $24,000 | $32,400 | $42,000 |
| $2,500 | $30,000 | $60,000 | $81,000 | $105,000 |
| $5,000 | $60,000 | $120,000 | $162,000 | $210,000 |
| $10,000 | $120,000 | $240,000 | $324,000 | $420,000 |

## How stock is handled

A store's price normally has two parts: the business, valued on its profit, and the stock, paid for separately at cost after a count at closing. Example: a store with $5,000 monthly profit at the 2.7× midpoint is worth $162,000; with $30,000 of saleable stock, the buyer pays about $192,000 in total. Old or slow-moving stock is usually excluded or discounted.

## Shopify, Amazon FBA and dropshipping compared

| Model | What buyers like | What buyers worry about | Effect in this tool |
|---|---|---|---|
| Own store (Shopify or similar) | Owns customer data and email list | Paid-ad dependence | Channel concentration rule applies |
| Amazon FBA | Built-in demand | Account health, Amazon fees and policy, stock held at Amazon | Channel concentration usually high (−6% to −12%) |
| Dropshipping | Low capital needed | Supplier control, thin margins, ad dependence | −8% |
| Outsourced fulfillment (3PL) | Easy to hand over | Contract terms | +3% |

## Limitations

- Inventory is taken at the cost you enter. Obsolete stock, and working-capital needs such as supplier deposits, need separate negotiation.
- The tool doesn't value loss-making stores, stores valued mainly for their brand, or wholesale businesses with large contracts.
- The base multiple is an editorial assumption. Results depend on your inputs and aren't an appraisal.

## Frequently asked questions

### How much is my ecommerce business worth?

Small profitable online stores are usually valued as a multiple of annual profit. With {{BRAND}}'s defaults that is about 2× to 3.5× before adjustments, plus inventory at cost. Enter your own figures to see the range and what drives it.

### Is inventory included in the price?

Usually not in the headline multiple. Most sales price the business on earnings and add inventory at cost, adjusted after a stock count at closing. The tool shows both figures so you can compare.

### Why is dropshipping valued lower?

Because the business depends on suppliers' stock, pricing and shipping times, which the buyer can't control. The tool applies a small negative adjustment. A dropshipping store with a strong brand and loyal customers can still be valuable.

### Does selling on Amazon reduce value?

Not in itself. Heavy reliance on any single channel adds risk, and Amazon accounts can be suspended or restricted, so buyers look closely at account health and at sales outside Amazon.

### Should I include stock in my profit figures?

No. Use profit after the cost of goods you sold. Enter the value of the stock you hold separately; the tool adds it on top of the business value at cost.

### Do buyers pay more for stores with their own brand?

Generally yes, because a brand they own can't be copied as easily as a reseller listing. The tool doesn't score branding directly; it shows through steadier growth and less channel dependence.
