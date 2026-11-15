# Impression share columns and the Google Ads Editor change file

Written by hand. To be re-read against the source before release. The Google pages below were read on 2026-11-13, except where a line says otherwise. The generated references in this folder do not carry these facts.

## Official: the impression share columns

Source: Google Ads Help, "About impression share", https://support.google.com/google-ads/answer/7103314

- **Search impr. share** is the impressions received on the Search Network divided by the estimated number of impressions the campaign was eligible to receive.
- **Search lost IS (budget)** is the percentage of time ads were not shown on the Search Network because of insufficient budget.
- **Search lost IS (rank)** is the percentage of time ads were not shown on the Search Network because of poor Ad Rank in the auction.

Source: Google Ads Help, "About top and absolute top metrics", https://support.google.com/google-ads/answer/7501826

- **Search top IS** is the impressions received among top ads divided by the estimated number of impressions the campaign was eligible to receive among top ads.
- **Search lost top IS (budget)** shows how often an ad did not show anywhere among top ads because of a low budget.
- **Search lost top IS (rank)** shows how often an ad did not show anywhere among top ads because of poor Ad Rank.

So the two budget columns answer different questions. Search lost IS (budget) is about showing at all. Search lost top IS (budget) is about showing among top ads only. The skill reads Search lost IS (budget) and Search lost IS (rank) when the report has them, and otherwise the top versions, and it says which it read.

Not stated on these pages: how Google writes very small or very large shares. Real downloads show `< 10%` for small shares. The skill counts a day written `< 10%` as 0 in its averages, so an average built from such days is a floor.

## Official: changing a campaign through a Google Ads Editor file

Source: Google Ads Editor Help, "CSV file columns", https://support.google.com/google-ads/editor/answer/57747

- The headers `Campaign`, `Campaign daily budget`, `Bid strategy type`, `Target CPA`, `Target ROAS` and `Campaign status` are Editor columns. The daily budget must be greater than zero. Campaign status takes Enabled, Paused or Removed.
- A blank cell tells Editor to make no change to that field.
- For each imported row, Editor decides whether to edit an item that exists or create a new one, from the columns that identify it. A row whose identifying values match an existing item is processed as an edit.

Read for this pack on 2026-11-13 by the campaign build skill, and not re-read for this one: Google's example in "Prepare a CSV file" (https://support.google.com/google-ads/editor/answer/56368) writes Target CPA as 12.34 and Target ROAS as 12.34%. Imported rows arrive in Editor as proposed changes, and nothing reaches the account until they are posted.

## Not documented on these pages

- Whether a campaign that uses a portfolio bid strategy takes a target from a campaign row. A portfolio's target is set on the portfolio. Change it there.
- Whether Editor needs `Bid strategy type` filled in when only the target changes. The skill leaves it blank in that case, which means no change.
