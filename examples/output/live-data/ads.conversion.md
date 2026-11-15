# Ads report, converted from live data

**File:** ads-report.csv, in the layout of a Google Ads download.
**Date range:** October 14, 2026 - November 12, 2026, 30 days.
**Rows:** 6.
**Totals:** Impr. 18,130, Clicks 1,295, Cost 9,194.50, Conversions 209.00.
**Check:** the file reads back with the pack's own reader: 6 rows, the date range, and every total row figure equal to the sum of its rows.

## Warnings

- The search returned 6 rows, its limit, so the report may be cut off. Narrow the date range or raise the limit, then run it again.

## Hand it to

- The account audit: python3 scripts/audit.py --work WORK --campaigns CAMPAIGNS --ads FILE (run from that skill's folder, FILE is ads-report.csv)

## How the numbers were made

- Money fields arrive in micros, millionths of the account currency, and are divided by 1,000,000. Money is written with two decimals and no currency symbol.
- Rates and shares arrive as ratios and are written as percentages. An impression share Google reports as 0.0999 is written < 10%, and a lost share of 0.9001 is written > 90%, as the interface shows them.
- API values such as ENABLED or EXACT are written as the interface's words, such as Enabled or Exact match.
- A metric missing from a row is read as 0, because results written as JSON leave out zero values.
- The total row is the sum of the rows in this file.

## What this did not cover

- The Ad column shows the first headline of a responsive search ad, else the ad's name, else its ID.
- Policy details are not in this file. Approval status is.
- Empty in every row, so written as --: ad_group_ad.ad.name.
- One search reads one account and one date range. Rows Google does not return are not here.
