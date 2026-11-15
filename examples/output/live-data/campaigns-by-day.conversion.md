# Campaign report, converted from live data

**File:** campaigns-by-day.csv, in the layout of a Google Ads download.
**Date range:** September 14, 2026 - November 12, 2026, 60 days.
**Rows:** 232.
**Totals:** Impr. 61,907, Clicks 4,308, Cost 27,454.73, Conversions 815.21, Conv. value 264,320.70.
**Check:** the file reads back with the pack's own reader: 232 rows, the date range, and every total row figure equal to the sum of its rows.

## Hand it to

- The budgets and forecasts: python3 scripts/pacing.py FILE --out OUTPUT (run from that skill's folder, FILE is campaigns-by-day.csv)
- The conversion tracking, as the clicks file: python3 scripts/find_breaks.py REPORT --out OUTPUT --clicks FILE (run from that skill's folder, FILE is campaigns-by-day.csv)

## How the numbers were made

- Money fields arrive in micros, millionths of the account currency, and are divided by 1,000,000. Money is written with two decimals and no currency symbol.
- Rates and shares arrive as ratios and are written as percentages. An impression share Google reports as 0.0999 is written < 10%, and a lost share of 0.9001 is written > 90%, as the interface shows them.
- API values such as ENABLED or EXACT are written as the interface's words, such as Enabled or Exact match.
- A metric missing from a row is read as 0, because results written as JSON leave out zero values.
- The total row is the sum of the rows in this file.

## What this did not cover

- Budget is the budget today, written on every day. A budget changed during the range shows its new amount on the earlier days too.
- One search reads one account and one date range. Rows Google does not return are not here.
