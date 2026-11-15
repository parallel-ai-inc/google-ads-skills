# Conversions by action and day, converted from live data

**File:** conversions-by-action-and-day.csv, in the layout of a Google Ads download.
**Date range:** September 14, 2026 - November 12, 2026, 60 days.
**Rows:** 342.
**Totals:** Conversions 447.23, All conv. 447.23, Conv. value 67,084.50, All conv. value 67,084.50.
**Check:** the file reads back with the pack's own reader: 342 rows, the date range, and every total row figure equal to the sum of its rows.

## Hand it to

- The conversion tracking: python3 scripts/find_breaks.py FILE --out OUTPUT [--actions SUMMARY] [--clicks CAMPAIGNS_BY_DAY] [--changes CHANGE_HISTORY] (run from that skill's folder, FILE is conversions-by-action-and-day.csv)

## How the numbers were made

- Money fields arrive in micros, millionths of the account currency, and are divided by 1,000,000. Money is written with two decimals and no currency symbol.
- Rates and shares arrive as ratios and are written as percentages. An impression share Google reports as 0.0999 is written < 10%, and a lost share of 0.9001 is written > 90%, as the interface shows them.
- API values such as ENABLED or EXACT are written as the interface's words, such as Enabled or Exact match.
- A metric missing from a row is read as 0, because results written as JSON leave out zero values.
- The total row is the sum of the rows in this file.

## What this did not cover

- Cost and clicks cannot be read in the same query as conversion actions. Use the campaigns by day report for them.
- One search reads one account and one date range. Rows Google does not return are not here.
