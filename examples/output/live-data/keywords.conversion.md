# Search keyword report, converted from live data

**File:** keyword-report.csv, in the layout of a Google Ads download.
**Date range:** October 14, 2026 - November 12, 2026, 30 days.
**Rows:** 8.
**Totals:** Impr. 20,085, Clicks 1,545, Cost 9,792.60, Conversions 229.00, Conv. value 68,700.00.
**Check:** the file reads back with the pack's own reader: 8 rows, the date range, and every total row figure equal to the sum of its rows.

## Hand it to

- The account audit: python3 scripts/audit.py --work WORK --campaigns CAMPAIGNS --keywords FILE (run from that skill's folder, FILE is keyword-report.csv)
- The search terms skill, to protect the account's own keywords: python3 scripts/check_negatives.py --work WORK --keywords FILE (run from that skill's folder, FILE is keyword-report.csv)

## How the numbers were made

- Money fields arrive in micros, millionths of the account currency, and are divided by 1,000,000. Money is written with two decimals and no currency symbol.
- Rates and shares arrive as ratios and are written as percentages. An impression share Google reports as 0.0999 is written < 10%, and a lost share of 0.9001 is written > 90%, as the interface shows them.
- API values such as ENABLED or EXACT are written as the interface's words, such as Enabled or Exact match.
- A metric missing from a row is read as 0, because results written as JSON leave out zero values.
- The total row is the sum of the rows in this file.

## What this did not cover

- Status shows only a paused or removed campaign or ad group. Google's other serving reasons are not in this file.
- One search reads one account and one date range. Rows Google does not return are not here.
