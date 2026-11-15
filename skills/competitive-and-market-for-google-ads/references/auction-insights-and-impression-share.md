# Auction insights and impression share

Written by hand. To be re-read against the source before release. The Google pages below were read on 2026-11-13 through a page summary, so the wording here is a close paraphrase, not a quotation. The generated references in this folder do not carry these facts.

## Official: the auction insights report

Source: Google Ads Help, "Use auction insights to compare performance", https://support.google.com/google-ads/answer/2579754

- The report compares your performance with other advertisers taking part in the same auctions. It is available for Search, Shopping and Performance Max campaigns. Performance Max auction insights cover Search and Shopping ads, at the account and campaign levels.
- Search campaigns get six statistics: impression share, overlap rate, outranking share, position above rate, top of page rate and absolute top of the page rate. Shopping campaigns get three: impression share, overlap rate and outranking share.
- **Impression share** is the impressions received divided by the estimated impressions that were eligible. On another advertiser's row it is their share over the auctions where they were eligible. A competitor's impression share in your report can differ from what they see in their own, because their eligible auctions only partly overlap with yours.
- **Overlap rate** is how often another advertiser's ad got an impression when your ad also got one.
- **Position above rate** is how often the other advertiser's ad showed in a higher position than yours when both showed.
- **Top of page rate** is how often an ad (yours or theirs, by row) showed at the top of the page, above the unpaid search results.
- **Absolute top of the page rate** is how often an ad showed as the very first ad above the unpaid search results.
- **Outranking share** is how often your ad ranked higher in the auction than the other advertiser's ad, or showed when theirs did not.
- The report can be segmented by time and by device.
- The report does not show insights when impression share is less than 10%. Only keywords and ad groups that meet a minimum threshold of activity have a report. Search partners are not included.
- "google.com" can appear as a domain when advertisers use Google hosted domains or a Google Business Profile, or when a landing page is a Google Site.
- The page lists only these statistics. It has no statistic for another advertiser's spend, bids, budget or settings.

## Official: impression share

Source: Google Ads Help, "About impression share", https://support.google.com/google-ads/answer/2497703

- Impression share is the impressions your ads received divided by the total impressions they were eligible to get.
- Eligible impressions are estimated from many factors, including targeting settings, approval statuses and quality.
- Impression share can show whether ads might reach more people with a higher bid or budget. Changes to bids, quality or Google's systems can shift which auctions count, so a small change over time does not always need action.
- Search partner traffic is not included in impression share.

Source: Google Ads Help, "Get impression share data", https://support.google.com/google-ads/answer/7103314

- **Search impr. share** is the impressions received on the Search Network divided by the estimated impressions the ads were eligible to receive.
- **Search lost IS (budget)** is the percentage of time ads were not shown on the Search Network because of insufficient budget. It is reported at the campaign level only.
- **Search lost IS (rank)** is the percentage of time ads were not shown on the Search Network because of poor Ad Rank in the auction.
- Impression share metrics are updated within 1 to 2 days.

## Not documented on these pages

- How a download writes small or large shares. This pack's brief says Google writes "< 10%" for small values; "> 90%" is assumed by analogy. The skill keeps both as bands.
- Whether Search impr. share, Search lost IS (rank) and Search lost IS (budget) always add up to 100%. The skill does not rely on it.
- The column names and the period format of an auction insights download, and how a Month or Week value is written. The loader accepts several forms.
- Whether combining campaigns by estimated eligible impressions matches Google's own account level figure. The skill labels its account lines as estimates and checks them against the You row.
