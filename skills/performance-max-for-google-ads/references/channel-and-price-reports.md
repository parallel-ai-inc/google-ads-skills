Written by hand. To be re-read against the source before release.

# The channel performance report and price benchmarks

Read on 2026-11-13 from the two Google Help pages linked below. Everything under "What Google documents" is **Official**.

## Channel performance report (Performance Max)

Source: [Google Ads Help - About the channel performance report for Performance Max](https://support.google.com/google-ads/answer/16260130)

### What Google documents

- The report covers Performance Max and Demand Gen campaigns. It has a performance summary, a chart from channels to goals, and a channel distribution table.
- The channels listed are Google Search, Google Display Network, YouTube, Discover, Maps, Gmail and Search partners.
- The table's metrics are Impressions, Clicks, Interactions, Conversions, Conversion value, Cost, Results and Results value. A Status column flags issues such as "Not eligible", "Eligible (Limited)", "Eligible" and "Missing required assets".
- The table can be downloaded from its toolbar. More segments can be added to the download.
- A Format choice shows "Ads using product data", "Ads using video" or all ads. Video ads with products on YouTube and Discover, and Merchant Center feed formats on Gmail, are not yet in the product data segment.
- Data is available from June 6, 2025 onwards.
- A channel with no ads and no listed issue most likely means the campaign is favouring channels with a higher return, not that something is broken.
- Store visit conversions are not split by channel.
- "Conversions" shows only the conversions the campaign optimises for. "Results" includes all goals.

## Price benchmarks (Merchant Center)

Source: [Google Merchant Center Help - Pricing insights: price benchmarks and sale price suggestions](https://support.google.com/merchants/answer/9626903)

### What Google documents

- Price benchmarks sit in Merchant Center under Analytics, on the Pricing tab.
- The benchmark is "the average price that typically leads to more successful ad auctions, impressions, clicks, or conversions". It comes from retailers selling the same GTIN across Shopping ads and free listings.
- A product needs a valid GTIN to get a benchmark.
- The view shows Your price, Benchmark, Price gap, Clicks and a price distribution (higher, similar or lower than the benchmark). Clicks cover the last 28 days.
- The page does not list the column names of a download.

## What this skill assumes, not documented

- The download of the channel table has a column headed `Channel`. The skill also accepts `Ad network type` and `Network (with search partners)`.
- A price gap is your price against the benchmark, positive when your price is higher. When both prices are present, the skill works the gap out itself as price divided by benchmark, minus one.
