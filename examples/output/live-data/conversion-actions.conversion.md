# Conversion actions, converted from live data

**File:** conversion-actions-summary.csv, in the layout of a Google Ads download.
**Date range:** October 14, 2026 - November 12, 2026, 30 days.
**Rows:** 4.
**Totals:** Conversions 230.00, Conv. value 31,000.00, All conv. 302.00, All conv. value 35,800.00.
**Check:** the file reads back with the pack's own reader: 4 rows, the date range, and every total row figure equal to the sum of its rows.

## Hand it to

- The conversion tracking: python3 scripts/audit_actions.py FILE --out OUTPUT (run from that skill's folder, FILE is conversion-actions-summary.csv)
- The account audit: python3 scripts/audit.py --work WORK --campaigns CAMPAIGNS --conversions FILE (run from that skill's folder, FILE is conversion-actions-summary.csv)

## How the numbers were made

- Money fields arrive in micros, millionths of the account currency, and are divided by 1,000,000. Money is written with two decimals and no currency symbol.
- Rates and shares arrive as ratios and are written as percentages. An impression share Google reports as 0.0999 is written < 10%, and a lost share of 0.9001 is written > 90%, as the interface shows them.
- API values such as ENABLED or EXACT are written as the interface's words, such as Enabled or Exact match.
- A metric missing from a row is read as 0, because results written as JSON leave out zero values.
- The total row is the sum of the rows in this file.

## What this did not cover

- The tracking status (such as Recording conversions) is not in this file. Checks that need it show as not run.
- Conversions are matched to actions by name.
- Not enabled, but still recorded conversions in the range, so not in this file: Old call tracking. Together: 18.00 All conv.
- One search reads one account and one date range. Rows Google does not return are not here.
