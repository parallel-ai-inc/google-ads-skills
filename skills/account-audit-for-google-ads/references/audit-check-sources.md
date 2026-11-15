# What Google documents behind the audit checks

Written by hand. To be re-read against the source before release.

Each section restates one Google Ads Help page, read on 2026-11-13. Everything on this page is **Official**. The audit's checks point here when they rest on one of these pages. Where a check adds a judgment of its own, the check says **Practitioner rule**.

## Quality Score

Source: [About Quality Score for Search campaigns](https://support.google.com/google-ads/answer/6167118)

- Quality Score is a diagnostic tool, on a scale from 1 to 10, shown for each keyword.
- It has three components: Expected clickthrough rate (Exp. CTR), Ad relevance and Landing page experience (Landing page exp.). Each one is rated "Above average", "Average" or "Below average", against other advertisers whose ads showed for the exact same search over the last 90 days.
- A component rated "Average" or "Below average" may indicate an opportunity to improve.
- Quality Score is not an input in the ad auction.
- Google says Quality Score is not a key performance indicator and should not be optimized or aggregated with the rest of your data. So the audit never averages it. It adds up the cost that sits on keywords with a "Below average" component.
- A dash in the Quality Score column means there are not enough searches that exactly match the keyword to rate it.
- Quality Score is based on exact searches of the keyword, so changing a keyword's match type does not change it.

## Ad strength

Source: [About Ad Strength for responsive search ads](https://support.google.com/google-ads/answer/9921843)

- Ad strength rates a responsive search ad as Incomplete, Poor, Average, Good or Excellent.
- Google's best practice: at least 2 responsive search ads with Good or Excellent Ad strength in each ad group, each with a unique final URL.
- Ad strength is feedback on the variety and relevance of the assets. It is not used to calculate Ad Rank, Quality Score or auction wins, and it does not decide whether an ad is eligible to serve.
- The limit of 3 enabled responsive search ads per ad group is in `ad-specs-limits.md`.

## Primary and secondary conversion actions

Source: [About primary and secondary conversion actions](https://support.google.com/google-ads/answer/11461796)

- Primary actions are reported in the Conversions column and are used for bidding, as long as the standard goal they are part of is used for bidding.
- Secondary actions are for observation only. They are reported in the All conv. column and are not used for bidding. The one exception: a secondary action that is part of a custom goal is used for bidding.
- Actions in a custom goal are used for reporting and bidding whether they are set as primary or secondary.
- Conversions created from Google Analytics are secondary by default.
- Google calls this setting critical: a wrong primary or secondary setting can stop Smart Bidding from optimizing well.
- Where it is set: Goals menu, Summary, Edit goal, "Conversion action optimization".

What this page does not say: anything about two primary actions that record the same event. Treating that as double counting is a **Practitioner rule**.

## Conversion counting: Every or One

Source: [About conversion counting options](https://support.google.com/google-ads/answer/3438531)

- "Every" counts every conversion after an ad interaction. Google calls it a good choice for sales, because every sale likely adds value.
- "One" counts only one conversion per ad click. Google calls it a good choice for leads, because usually only one unique lead per ad click adds value.
- "Every" is the default for website actions, in app actions, Analytics transactions, clicks on a number on a mobile website and imported actions. "One" is the default for calls from ads, Analytics goals, calls to a number on a website and app installs.
- A change to the Count setting applies to future conversions only.

## Impression share lost to budget and to rank

Sources: [Get impression share data](https://support.google.com/google-ads/answer/7103314), [About impression share](https://support.google.com/google-ads/answer/2497703), [About Maximize conversions bidding](https://support.google.com/google-ads/answer/7381968)

- Search impr. share: the impressions received on the Search Network divided by the estimated impressions the ads were eligible to receive.
- Search lost IS (budget): the percentage of time the ads were not shown on the Search Network because the budget was too low. Campaign level only.
- Search lost IS (rank): the percentage of time the ads were not shown on the Search Network because of poor Ad Rank.
- Impression share is an estimate. Small moves over time do not by themselves call for action. Search partners are not included in it.
- **Maximize conversions and Maximize conversion value are "limited by budget" by design.** They are built to spend the full daily budget. Google does not recommend reading Search lost IS (budget) for them, says the column is incompatible with the bid strategy, and points to the budget simulator. So the audit leaves these campaigns out of the budget check and says so.

## Networks in a Search campaign

Source: [About the Google Search Network](https://support.google.com/google-ads/answer/1722047)

- Search partners are included by default when a Search campaign is created. They can be removed at any time in the campaign's settings, under Networks.
- Google's own note: clicks from search partner sites that display products for sale may not always reflect highly targeted traffic, and advertisers should consider carefully whether these networks fit their goals.
- To show ads only on Google Search, only the Google Search Network box is selected. The same page tells advertisers with performance issues to check their Display Network settings as well.
- Google Ads does not report which search partner site showed an ad, except in Performance Max.

Judging whether a Search campaign should keep search partners or the Display Network is a **Practitioner rule**. The numbers decide it, and the split by network is in the campaign report segmented by "Network (with search partners)".

## Where each report is in Google Ads

Read from the instructions on the pages above.

| Report | Path |
|---|---|
| Campaign report | Campaigns menu, Campaigns, Campaigns |
| Ad group report | Campaigns menu, Campaigns, Ad groups |
| Keyword report | Campaigns menu, Audiences, keywords, and content, Search keywords |
| Ads report | Campaigns menu, Campaigns, Ads |
| Conversions summary | Goals menu, Conversions, All conversions |

Columns are added with the columns icon above the table. Quality Score, Exp. CTR, Ad relevance and Landing page exp. are in the Quality score section. Search impr. share is under Competitive metrics. Ad strength is under Attributes. The download icon is above the table.

Not on these pages, so not confirmed here: a Networks column in the campaign table, and the column names of the downloaded ad group report, ads report and conversions summary. The audit accepts the names Google documents and says which columns it could not find.
