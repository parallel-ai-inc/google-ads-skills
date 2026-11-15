# The order fixes are made in

Written by hand. To be re-read against the source before release.

The audit ranks findings by money within each kind. The fix plan runs in a different order: the order that keeps one fix from spoiling the next. The order is a **Practitioner rule**. The Google facts it rests on are **Official** and are listed with their pages.

## The order

1. **Measurement.** Conversion actions, primary and secondary, counting (CT checks).
2. **Serving and policy.** Ad groups with no active ad, disapproved or limited ads, campaigns not eligible to serve (AD-01, AD-02, AD-03, SE-01).
3. **Waste.** Search terms, keywords and networks that spend with no result, brand searches in the wrong campaign (SQ-01, SQ-02, KW-05, BB-04, SE-02).
4. **Structure, keywords and ads.** Single keyword ad groups, duplicates, idle keywords, Quality Score components, ad strength (ST, KW-01 to KW-03, AD-04).
5. **Bidding.** Bid strategy type, shared budgets, value bidding, targets, broad match without conversion based bidding (BB-01, BB-02, BB-05, BB-06, KW-04).
6. **Budget.** More budget for campaigns that convert well (BB-03).

## Why this order

- **Measurement first.** Primary actions are the ones used for bidding, and Google calls the primary or secondary setting critical: a wrong setting can stop Smart Bidding from optimizing well. Every later judgment in the audit also reads conversions. **Official:** [About primary and secondary conversion actions](https://support.google.com/google-ads/answer/11461796), restated in `audit-check-sources.md`.
- **Change bidding once, on clean data.** A bid strategy can enter Learning after a new strategy, a strategy setting change, a budget change or a conversion setting change. Fixing measurement and bidding in separate rounds can mean two learning periods. **Official:** [About bid strategy statuses](https://support.google.com/google-ads/answer/6263057), restated in `reporting-and-diagnostics.md`.
- **Budget last.** Maximize conversions and Maximize conversion value are built to spend the full daily budget, so more budget scales whatever the campaign does now, waste and miscounted conversions included. **Official:** [About Maximize conversions bidding](https://support.google.com/google-ads/answer/7381968), restated in `audit-check-sources.md`.
- **Before scaling,** tracking and conversion semantics should be stable, and search terms, landing pages, creative and budget headroom inspected. **Practitioner rule:** `checklists.md`, Before Scaling.
- **Serving before waste and structure.** An ad group that cannot show an ad, or a campaign that is not eligible, produces no data to judge, so it is fixed before the work that reads that data. **Practitioner rule.** It follows the investigation order in `reporting-and-diagnostics.md`, which starts with serving and policy eligibility, then measurement.

## When to break the order

An urgent stop, such as a disapproved ad on the main service or a campaign spending with no conversions at all, can be handled the same day whatever its stage. Say so when you do.
