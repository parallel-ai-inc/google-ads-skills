# Playbook: Shopping products, feed and price competitiveness

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

Which products spend without return, whether the cause is price, the feed or the page, and what to change first. It reads the Products and "Prices against the benchmark" sections of `pmax-review.md` and the products list in the FOR YOUR JUDGMENT block.

## When to use it

A products report or a price benchmark file was given, or the person asks about the feed, product performance or price. Campaign goals, brand, searches and channels belong to `playbooks/review-and-waste.md`.

These two reports show prices, benchmarks, clicks, cost and conversions per product. They show no competitor, no competitor's price or bid, no auction share and no demand trend. Never say a competitor undercut the account or won its auctions. Say only that the account's price sits above or below the benchmark.

## What to read in the output

- **Products:** the products and cost totals, the top 10 share, "5 products make half of it", products with no impressions, the "spent enough to judge" line and the two counts beside it.
- **By Product type (1st level)** and **By Brand:** Cost, Cost / conv., Share of products report conv. value, Cost with no conversions.
- **Blank attributes:** Products blank and Cost on them.
- **Prices against the benchmark:** the Position table (Above, At, Below, No benchmark) with Conv. rate and Conv. value / cost, "The middle product above benchmark is priced X% over it", and the table of products above benchmark with Gap, Cost and Conversions.
- **Findings:** "Products with cost and no conversions", "Products priced above benchmark", "Products below the target ROAS", and blank attribute findings.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| A product spent past the line with no conversions and sits above its benchmark | Price is the first suspect | Ask whether the price is deliberate. If it can change, test a price nearer the benchmark. If it cannot, push the product less through its own listing group or a custom label | Practitioner rule |
| A product spent past the line with no conversions and sits at or below its benchmark | Price is not the cause | Check the feed against the landing page: title, image, availability, price match. Then the page itself | Practitioner rule |
| The Position table: Conv. rate above benchmark is lower than at or below | In this account, price is costing conversions | Lead with price for the products above benchmark that carry cost | Practitioner rule |
| Conv. rate above benchmark is the same or higher | Price is not what holds these products back | Do not recommend price cuts. Look at feed, page and assets | Practitioner rule |
| A product above benchmark that converts | Buyers accept the price, perhaps for brand, stock or delivery | Leave it | Practitioner rule |
| Products with "No benchmark" | No benchmark came back; a valid GTIN is needed for one | Check the GTIN. Do not judge price without a benchmark | Official (references/channel-and-price-reports.md) |
| Products in the report with no impressions | They are not serving | Check Merchant Center product status and issues before anything else | Official (references/feeds.md) |
| Brand or Product type blank on products that spend | Weak product data | Fill required and high signal attributes before any title test | Practitioner rule |
| Custom label 0 blank on most products | Labels are not in use | Matters only if the person wants to split products by margin, stock or price. Labels do not raise rank | Practitioner rule |
| One Product type carries most of the Cost with no conversions | The waste is product led | Act on price, feed or listing groups before any bid change | Practitioner rule |
| Products below the target ROAS | Spend past the line at a return under target | Split them into their own listing group or label. Do not pause on a short window | Practitioner rule |
| The top products carry most of the cost | Spend is concentrated | Not a problem in itself. Ask whether these are the products the business wants to sell | Practitioner rule |

## How big a change

- **The line.** "Spent enough to judge" is the target cost per conversion when given, otherwise the products report's own cost per conversion. It sorts; it is not a verdict.
- **Price gap.** No source says how large a gap matters. The table of products above benchmark is printed by Cost: take it in that order, and use the printed "middle product above benchmark" figure to describe the account's usual gap. The price decision belongs to the business.
- **Time.** The benchmark view counts clicks over the last 28 days. Official (references/channel-and-price-reports.md). If the products report covers a different range, say both ranges. After a price or feed change, give it at least 1 to 2 weeks, or one conversion cycle, before judging. Official (references/pmax.md).
- **Coverage.** The products report may cover less cost than the campaign report (the Evidence check prints the share). Every product share is of the products report's cost.

## Failure modes

- **Claiming competitor behaviour.** Shows as "a rival undercut you". Check: the files hold no competitor data.
- **Excluding a product that buyers search for.** Shows as an exclusion on a product whose searches the review kept. Check price and feed first.
- **Two counts of no conversion products that disagree.** One counts all with cost, one only those past the line. Check: quote the line beside each count.
- **Price advice on a product with no benchmark.** Check the Position column.
- **Feed fixes ranked by count, not cost.** Check Cost on them in Blank attributes.
- **Promising a lift.** Neither feeds.md nor shopping-mastery.md supports a fixed lift from titles, GTINs or labels. Say "expected to help", never a number.

## Worked example

Northside Plumbing. The products report holds 22 products, 7,775.00 cost, 92.00 conversions. The line is 84.51. 5 products passed it with no conversions, 1,410.00 in all. The products list shows all five as Drain Tools, and the finding says all five sit above their benchmark. Conv. rate is 1.10% above benchmark and 2.83% at or below it. The call: price first for Drain Tools. Ask whether those prices are deliberate before any listing group change. Brand and Product type are blank on 2 products carrying 115.00, which is a small feed fix. The Rheem 40 Gallon at 2.5% over benchmark converts 14 times: leave it.

## What to tell the client

Five drain tools took 1,410.00 without a sale, and all five are priced above Google's benchmark price for the same item. Across the shop, products priced above that level convert at 1.10%, against 2.83% for the rest. Before we push them less, can you tell me whether those prices are set on purpose? Two products are missing their brand and type, which is a quick fix in Merchant Center.
