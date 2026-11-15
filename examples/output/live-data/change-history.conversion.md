# Change history report, converted from live data

**File:** change-history.csv, in the layout of a Google Ads download.
**Date range:** October 15, 2026 - November 13, 2026, 30 days.
**Rows:** 5.
**Check:** the file reads back with the pack's own reader: 5 rows, the date range, and every total row figure equal to the sum of its rows.

## Hand it to

- The conversion tracking: python3 scripts/find_breaks.py REPORT --out OUTPUT --changes FILE (run from that skill's folder, FILE is change-history.csv)

## How the numbers were made

- Money fields arrive in micros, millionths of the account currency, and are divided by 1,000,000. Money is written with two decimals and no currency symbol.
- Rates and shares arrive as ratios and are written as percentages. An impression share Google reports as 0.0999 is written < 10%, and a lost share of 0.9001 is written > 90%, as the interface shows them.
- API values such as ENABLED or EXACT are written as the interface's words, such as Enabled or Exact match.
- A metric missing from a row is read as 0, because results written as JSON leave out zero values.
- The total row is the sum of the rows in this file.

## What this did not cover

- Google keeps change events for 30 days, returns at most 10,000 rows and only the latest change to each item in the range.
- Change events cover campaigns, ad groups, ads, keywords and other criteria, budgets, bid adjustments and assets. Changes to conversion actions are not among them.
- Changes is written from the item type, what happened and the fields changed. It does not show old and new values.
- One search reads one account and one date range. Rows Google does not return are not here.
