# Campaign report, converted from live data

**File:** campaign-report.csv, in the layout of a Google Ads download.
**Date range:** October 14, 2026 - November 12, 2026, 30 days.
**Rows:** 4.
**Totals:** Impr. 30,242, Clicks 2,089, Cost 13,370.49, Conversions 407.18, Conv. value 132,427.80.
**Check:** the file reads back with the pack's own reader: 4 rows, the date range, and every total row figure equal to the sum of its rows.

## Hand it to

- The account audit: python3 scripts/audit.py --work WORK --campaigns FILE (run from that skill's folder, FILE is campaign-report.csv)
- The bidding and scaling, and client reporting, where they ask for a campaign report (run from that skill's folder, FILE is campaign-report.csv)

## How the numbers were made

- Money fields arrive in micros, millionths of the account currency, and are divided by 1,000,000. Money is written with two decimals and no currency symbol.
- Rates and shares arrive as ratios and are written as percentages. An impression share Google reports as 0.0999 is written < 10%, and a lost share of 0.9001 is written > 90%, as the interface shows them.
- API values such as ENABLED or EXACT are written as the interface's words, such as Enabled or Exact match.
- A metric missing from a row is read as 0, because results written as JSON leave out zero values.
- The total row is the sum of the rows in this file.

## What this did not cover

- Status and Status reasons (the serving status, such as Limited by budget) are not in this file. Checks that need them show as not run.
- Budget is the budget today.
- One search reads one account and one date range. Rows Google does not return are not here.
