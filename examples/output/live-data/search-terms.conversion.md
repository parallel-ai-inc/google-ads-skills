# Search terms report, converted from live data

**File:** search-terms-report.csv, in the layout of a Google Ads download.
**Date range:** October 14, 2026 - November 12, 2026, 30 days.
**Rows:** 13.
**Totals:** Impr. 15,273, Clicks 797, Cost 5,362.20, Conversions 117.00, Conv. value 35,100.00.
**Check:** the file reads back with the pack's own reader: 13 rows, the date range, and every total row figure equal to the sum of its rows.

## Hand it to

- The search terms skill: python3 scripts/measure.py FILE --work WORK --brand "..." (run from that skill's folder, FILE is search-terms-report.csv)
- The account audit: python3 scripts/audit.py --work WORK --campaigns CAMPAIGNS --search-terms FILE (run from that skill's folder, FILE is search-terms-report.csv)

## How the numbers were made

- Money fields arrive in micros, millionths of the account currency, and are divided by 1,000,000. Money is written with two decimals and no currency symbol.
- Rates and shares arrive as ratios and are written as percentages. An impression share Google reports as 0.0999 is written < 10%, and a lost share of 0.9001 is written > 90%, as the interface shows them.
- API values such as ENABLED or EXACT are written as the interface's words, such as Enabled or Exact match.
- A metric missing from a row is read as 0, because results written as JSON leave out zero values.
- The total row is the sum of the rows in this file.

## What this did not cover

- The Keyword column is left out, so no search is split or dropped by keyword.
- Google leaves low volume searches out of search results, as it does in the interface.
- One search reads one account and one date range. Rows Google does not return are not here.
