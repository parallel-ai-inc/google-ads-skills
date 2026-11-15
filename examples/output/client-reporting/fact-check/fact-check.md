# Fact check: draft-report-to-check.md

Checked against the numbers for 2026-10-01 to 2026-10-31, compared with 2026-09-01 to 2026-09-30 and the same period last year.

- 9 numbers found, dates not counted.
- Verified: 4.
- Contradicted by the data: 3.
- Unclear or overclaimed: 1.
- Needs data: 1.
- Dates, counted apart: 4 found, 4 match the period and the data.

## Contradicted by the data

- Contradicted by the data: wrong direction: "5.2%" in: Cost per conversion rose 5.2% to 34.88, under the 40.00 target.
  Account: Cost / conv., change vs previous period is -5.2%, so it went down, but the sentence says it went up. (Line 4)
- Contradicted by the data: "18%" in: Drain Cleaning | Search declined sharply, with cost down 18% on September.
  The data says Drain Cleaning | Search: Cost, change vs previous period is -37.8%. (Line 7)
- Contradicted by the data: "9.4x" in: Return on ad spend reached 9.4x for the month.
  The data says Account: Conv. value / cost, current period is 9.09. (Line 8)

## Unclear or overclaimed

- Matches a different comparison: "26.4%" in: Plumbing | Water Heaters conversions fell 26.4% month over month after the move to Target CPA.
  This value matches Plumbing | Water Heaters: Conversions, change vs same period last year (-26.4%, id c2.conv.chg_ly). That is a different comparison from the one the sentence names. (Line 6)

## Needs data

- No figure in the data supports it: "40.00" in: Cost per conversion rose 5.2% to 34.88, under the 40.00 target.
  No number in the data has this value for this measure, campaign and comparison. (Line 4)

## Verified

| Number | Matched to | Value in the data |
|---|---|---|
| 1.5% | Account: Conversions, change vs previous period | +1.5% |
| 14,423.32 | Account: Cost, current period | 14,423.32 |
| 34.88 | Account: Cost / conv., current period | 34.88 |
| 58.1% | Plumbing \| Emergency: Cost, share of the account total, current period | 58.1% |

## Caveats

| Check | Present |
|---|---|
| States the reporting period (2026-10-01 to 2026-10-31) | Yes |
| Says what it compares against | Yes |
| Says what the numbers cannot show (late conversions, attribution, what is not included) | No |

## How the check works

- Every number is matched to the numbers of the period within the rounding it was written with: 12% matches 11.5% to 12.5%.
- The words around it are read too: the measure, the campaign, the comparison and whether it rose or fell. A value that matches only a different one is flagged.
- A number that matches by coincidence passes. The Verified table shows what each was matched to, so check it reads right.
- The caveat checks look for words only. Read the report to judge them.

## What this did not cover

- Claims without numbers, such as causes and recommendations. Judge those against the summary from measure.py.
- Numbers written in words, other than doubled, halved and the like, which are flagged.
- Numbers from outside Google Ads, such as CRM leads or revenue, unless they were given to measure.py with --given.
