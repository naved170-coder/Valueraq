---
title: How to Value a Membership Site
meta_title: How to Value a Membership Site (Worked Examples)
meta_description: A membership site is valued on profit and how long members stay. See the formulas, a churn-adjusted worked example and a value table. Free tool, no sign-up.
h1: How to Value a Membership Site
section: Valuation
cluster: valuation
order: 60
page_type: article
answer: A membership site is usually valued as a multiple of its yearly profit, then adjusted for how long members stay. Recurring revenue and low churn raise the range; high churn, owner-made content and dependence on one platform lower it. Work out annual profit, pick the method that fits, and test the result at a few churn rates.
keywords: membership site valuation, how to value a membership site, subscription business valuation, membership website worth, membership site churn
published: 2026-11-07
updated: 2026-11-07
publish_at: 2026-11-07T01:00Z
image: /static/img/articles/how-to-value-a-membership-site.png
image_alt: How to Value a Membership Site (VALUERAQ guide)
score: 8.6
related: /guides/saas-valuation/, /guides/saas-metrics-buyers-check/, /guides/revenue-vs-profit-multiples/, /guides/how-to-calculate-sde/, /guides/how-to-value-an-email-list/, /guides/website-vs-saas-valuation/
cta: /tools/saas-valuation/
cta_text: To see how churn and margin move a range, enter your own figures in the free SaaS valuation tool. It takes about a minute and needs no sign-up.
---

## Key takeaway

A membership site sells ongoing access: members pay every month or year for content, a community, courses, tools or support. That recurring payment is what buyers like. It makes income more predictable than one-off sales, so a membership site can earn a better multiple than a business that has to find every customer again each month.

But recurring revenue is only worth what stays. Members leave, and the pace at which they leave (churn) decides how long the income lasts. In practice a buyer looks at five things: annual profit, how many members cancel each month, how much of the work the owner does, how members find the site, and how clean the records are.

Every dollar figure below is an invented illustration of the arithmetic, run through VALUERAQ's published default assumptions. None of it is market data or a prediction of a sale price.

## Step 1: Work out what the site really earns

Start with the last twelve months, month by month. Stripe defines monthly recurring revenue as "the total amount of money a company can expect to receive from its existing customers each month". For a membership site, that is members multiplied by their fee, with annual plans spread across twelve months and one-off fees left out. See [MRR](/glossary/mrr/) and [recurring revenue](/glossary/recurring-revenue/).

Then separate revenue from profit. Subtract everything it costs to run the site:

- Payment processing and platform fees.
- Hosting, community software, email and course tools.
- Content costs: writers, guest experts, video editing.
- Support, moderation and any contractors.
- Advertising used to find new members.

What is left, before the owner pays themselves, is the owner's earnings. Buyers of small online businesses call it seller's discretionary earnings, or [SDE](/glossary/sde/). [How to calculate SDE](/guides/how-to-calculate-sde/) walks through the add-backs. Be careful with them: BizBuySell warns that "some add-backs can unrealistically overvalue the company", so keep proof for each one.

## Step 2: Choose the method

Two approaches fit a membership site, and they can give quite different answers.

| Method | Formula | Best when |
|---|---|---|
| Multiple of annual profit | Monthly profit × 12 × multiple | The site is owner-run, content-led, with modest costs and a small team |
| Multiple of annual recurring revenue (ARR) | MRR × 12 × multiple | The product is closer to software, with high margins and a team behind it |

VALUERAQ's default range for the profit-based tools (website, newsletter, app, ecommerce) is 2.5x to 4.0x annual profit, with a midpoint of 3.2x. For the SaaS tool the default range is 2.0x to 5.0x ARR, midpoint 3.5x. These are defaults set by VALUERAQ and described in the [methodology](/methodology/), not market data. Corporate Finance Institute notes that a multiples approach "only considers the company's position for a certain time period", which is why the adjustments below matter.

VALUERAQ has no tool built only for memberships. The closest are the newsletter tool, which treats paid subscriptions as slightly better than sponsorship income, and the [SaaS valuation tool](/tools/saas-valuation/), which asks for churn and gross margin. Choose by looking at how the site really works. A community run by one person who writes everything looks like a paid newsletter. A members-only software tool with a team looks like SaaS. The page on [website vs SaaS valuation](/guides/website-vs-saas-valuation/) explains the difference.

## Worked example: one membership site, two methods

Take a hypothetical membership site.

| Item | Figure |
|---|---|
| Members | 400 paying $25 a month |
| Monthly recurring revenue | 400 × $25 = $10,000 |
| Monthly costs (fees, tools, contractors, hosting) | $4,500 |
| Monthly profit before the owner's pay | $5,500 |
| Annual profit (SDE) | $5,500 × 12 = $66,000 |
| Annual recurring revenue | $10,000 × 12 = $120,000 |
| Age | 3 years |
| Revenue change over 12 months | +5% |
| Owner hours per week | 15 |
| Gross margin | 88% |
| Monthly churn | 4% |

**Profit method.** Entering this site into the newsletter tool as paid subscriptions, the multiple range becomes 2.62x to 4.2x (the default 2.5x to 4.0x, raised 5% for subscription revenue). Annual profit of $66,000 gives roughly **$173,000 to $277,000**, with a midpoint near $222,000.

**ARR method.** Entering the same figures into the SaaS tool, the 88% gross margin adds 5% and the 4% churn adds nothing (2% to 5% is the baseline), so the range becomes 2.1x to 5.25x ARR. On $120,000 that is roughly **$252,000 to $630,000**, with a midpoint of about $441,000.

The gap is large, and that is the lesson. The ARR range is nearly twice the profit range because ARR ignores costs. A buyer who sees a $66,000 profit on $120,000 of revenue will think about what they would earn, not just what comes in. If the owner writes the content and runs the community, the profit method is the safer starting point. If a team could run the site without the owner and margins are software-like, the ARR method deserves more weight. Present both to a buyer and explain your choice.

## Churn: the number that moves the price

Churn is the share of members who cancel in a month. Stripe defines it as "the percentage of total customers who discontinue using a product or service during a given period". See [churn](/glossary/churn/) and its mirror image, [retention rate](/glossary/retention-rate/).

Two simple calculations make churn concrete.

**Average member lifetime ≈ 1 ÷ monthly churn.** At 2% churn a member stays about 50 months. At 4% it is 25 months. At 7% it is about 14 months. This is a rough guide, since real members do not leave at an even pace.

**Members left after a year = starting members × (1 − churn)^12.** From 1,000 members, with no new sign-ups:

| Monthly churn | Members left after 12 months | Share kept |
|---|---|---|
| 2% | 785 | 78.5% |
| 5% | 540 | 54.0% |
| 7% | 419 | 41.9% |

![Members left after 12 months, of 1,000: 2% churn 785, 5% churn 540, 7% churn 419](/static/img/articles/how-to-value-a-membership-site-members-left.svg){: width="720" height="226" loading="lazy" }

At 5% monthly churn the site loses nearly half its members in a year, so it must find about 50 new members a month per 1,000 just to stand still. That is a marketing job, and a buyer will price it in.

### What VALUERAQ does with churn

In the SaaS tool, churn above 8% a month lowers the range by 20%, above 5% to 8% lowers it by 10%, 2% to 5% leaves it unchanged, and under 2% raises it by 10%. Run on the example site (everything else equal), the midpoint moves like this:

| Monthly churn | Adjustment | Multiple range | Midpoint value |
|---|---|---|---|
| 1.5% | +10% | 2.31x to 5.78x | about $485,000 |
| 4% | none | 2.1x to 5.25x | about $441,000 |
| 7% | −10% | 1.89x to 4.73x | about $397,000 |

![Midpoint value by monthly churn ($ thousand): 1.5% churn 485k, 4% churn 441k, 7% churn 397k](/static/img/articles/how-to-value-a-membership-site-value-by-churn.svg){: width="720" height="226" loading="lazy" }

The same site, with the same revenue, is worth about $88,000 more at 1.5% churn than at 7%. Cutting cancellations can be the most valuable thing an owner does before selling.

### Look at cohorts, not just the average

An average churn figure can hide a problem. Group members by the month they joined and see how many remain after one, three, six and twelve months. This is [cohort analysis](/glossary/cohort-analysis/). If most cancellations happen in the first month, the sales page may promise more than the site delivers. If cancellations climb after month six, the content may be running out of fresh material. Buyers who ask for cohort data are testing exactly this.

## Value by monthly profit

If you only want a quick idea, here are the default profit-method ranges for a range of monthly profits. Each row is monthly profit × 12 × the multiple.

| Monthly profit | Annual profit | Low (2.5x) | Midpoint (3.2x) | High (4.0x) |
|---|---|---|---|---|
| $1,000 | $12,000 | $30,000 | $38,400 | $48,000 |
| $2,500 | $30,000 | $75,000 | $96,000 | $120,000 |
| $5,000 | $60,000 | $150,000 | $192,000 | $240,000 |
| $10,000 | $120,000 | $300,000 | $384,000 | $480,000 |

These are starting points before adjustments. A site with rising revenue, low churn and little owner involvement could sit above the midpoint, and one with the opposite could sit below it.

## What lowers the value of a membership site

The adjustments buyers apply are the same ones VALUERAQ's tools use. The numbers below are default adjustments from the methodology, not market data.

| Factor | Default adjustment | Why a buyer cares |
|---|---|---|
| Owner works over 40 hours a week | −10% | The buyer must replace that labor |
| Owner works over 20 to 40 hours | −5% | Heavy dependence on one person |
| Over 80% of sign-ups from one channel | −12% | One algorithm or policy change could cut new members |
| Largest customer over 30% of revenue | −12% | Matters for team or corporate memberships |
| Under 1 year of history | −20% | Little evidence the income lasts |
| Revenue falling more than 20% | −25% | Shrinking membership |

Three risks deserve a closer look.

**Owner-made content.** If members join to hear one person, the business may not survive a handover. This is [key person risk](/glossary/key-person-risk/). Recorded content libraries, a trained moderator and documented processes make a sale easier. A [transition period](/glossary/transition-period/) where the seller stays for a few weeks also helps.

**Platform dependence.** Many membership sites run on a platform they do not control: a social network group, a payment processor, a video host or a community app. A change in terms can take away the audience or the billing. Read about [platform risk](/glossary/platform-risk/) and make sure the member list and billing records can be exported and transferred.

**Reliance on one acquisition channel.** If most new members arrive from one social account or one search ranking, a buyer will ask what happens if it fades.

## What raises the value

- **Annual plans** that give cash up front and lower the monthly cancellation rate.
- **Low churn that has been steady**, shown month by month.
- **Revenue that has grown** over the last year, even modestly.
- **Content and systems written down**, so a new owner can keep delivering.
- **Several ways to bring members in**, not just one.
- **Clean records** that match the payment processor's reports. [How to verify website revenue](/guides/how-to-verify-website-revenue/) shows what buyers check.

## Common mistakes

1. **Using revenue as if it were profit.** A $10,000 monthly MRR does not mean a $10,000 monthly profit.
2. **Counting annual plans as monthly income at the time of sale.** Spread them across the year they cover.
3. **Ignoring refunds and failed payments.** They reduce real income.
4. **Quoting a single churn number.** Show cohorts.
5. **Forgetting the owner's pay.** If the owner takes no salary, profit looks higher than a buyer will earn.
6. **Treating the output as a price.** A range is a starting point for a conversation, not a guarantee.

## A short checklist before you value your site

1. Pull twelve months of revenue and costs, month by month.
2. Calculate MRR from active members, not from total sign-ups.
3. Work out monthly churn and, if possible, cohorts.
4. Calculate annual profit before the owner's pay.
5. Write down owner hours per week and what only you can do.
6. Note your largest sign-up channel and its share.
7. Run the value with both methods and at three churn rates.
8. Ask an accountant to check the figures before you share them with a buyer.

The [SBA's guide to closing or selling a business](https://www.sba.gov/business-guide/manage-your-business/close-or-sell-your-business) lists the three common approaches (income, market and assets) and says to "use business valuation to set a monetary value". For a membership site the income approach, based on earnings, does most of the work.

## Frequently asked questions

### How much is a membership site worth?

It depends on profit, churn, owner involvement and how members arrive. A rough starting range is annual profit multiplied by 2.5 to 4.0, which is VALUERAQ's default for profit-based businesses. A site with software-like margins and a team may be valued on annual recurring revenue instead. Test both and see the gap.

### Is a membership site valued on revenue or profit?

Most owner-run sites are valued on profit, because the buyer is buying the earnings. Revenue-based valuation is more common for software products where margins are high and growth is the main story. See [revenue vs profit multiples](/guides/revenue-vs-profit-multiples/).

### What is a good churn rate for a membership site?

There is no single answer, and this guide does not quote an industry average because no published source is on file. Compare with your own history and similar sites you can see records for. In VALUERAQ's SaaS tool, monthly churn between 2% and 5% is the baseline, under 2% raises the range and over 5% lowers it.

### Do annual memberships make the site worth more?

They can. Annual plans bring cash earlier and reduce how often members choose to cancel. A buyer will still ask how many renew at the end of the year, so show renewal history.

### Can I sell a membership site that depends on me?

Yes, but expect a lower price and more questions. Document how the site runs, train others to deliver the content or moderate, and offer a handover period. See [key person risk](/glossary/key-person-risk/).

## Sources

- Stripe, [Essential SaaS metrics](https://stripe.com/resources/more/essential-saas-metrics): the definitions of monthly recurring revenue and churn.
- Corporate Finance Institute, [Multiples analysis](https://corporatefinanceinstitute.com/resources/valuation/multiples-analysis): the note that multiples consider a certain period only.
- BizBuySell Learning Center, [Add-Backs for Seller's Discretionary Earnings](https://www.bizbuysell.com/learning-center/article/add-backs-sde/): the definition of add-backs and the warning about overvaluation.
- U.S. Small Business Administration, [Close or sell your business](https://www.sba.gov/business-guide/manage-your-business/close-or-sell-your-business): the three valuation approaches.
- {{BRAND}}, [Valuation methodology](/methodology/): the default multiple ranges and every adjustment used in the examples.
