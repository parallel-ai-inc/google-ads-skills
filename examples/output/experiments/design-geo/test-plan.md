# Test plan

Campaign report.
August 15, 2026 - November 12, 2026.

The data covers 82 days, 2026-08-01 to 2026-10-21, for the test regions in leads-by-city-by-day.csv.
Amounts are in USD.

## The answer

Readable. A lift of 20% in leads needs 18 measured days, planned as 21 days so every weekday counts the same.

Design: a geo test (test regions against control regions). Run 2026-11-16 to 2026-12-06, reading from 2026-11-16.

## The outcome, day by day

- Leads a day: 29.62 on average, with a spread (standard deviation) of 9.59.
- There is a weekday pattern (p = 0.000): Monday runs at 135% of the daily average, Sunday at 72%. The plan runs whole weeks. The control regions share it, so the fit against them takes it out.
- The noise used: how far the test regions' daily leads stray from what the control regions predict (fit over 82 days, R squared 0.38).
- Test regions: Evanston; Skokie; Oak Park. Control regions: Berwyn; Cicero; Des Plaines; Niles; Park Ridge. The test regions carry 40% of the leads.

## What lift it can detect

At 95% confidence and 80% power:

| Measured days | Smallest lift it can detect |
|---|---|
| 14 | 22.1% |
| 21 | 18.0% |
| 28 | 15.6% |
| 42 | 12.8% |
| 56 | 11.0% |

## The plan

- **What changes:** Pause all campaigns in the test cities
- **Start:** 2026-11-16. **Left out at the start:** 0 days. **Reading:** 2026-11-16 to 2026-12-06, 21 days. **Stop:** 2026-12-06.
- **Pre-period for the readout:** 2026-09-14 to 2026-11-15, 63 days, three times the test length. The history read here holds 82 days.
- **Stays fixed:**
  - Test and control regions are targeted with the Presence location option. **Official**, `references/incrementality.md`.
  - Holdback and go dark campaigns each keep their own budget. No budget is shared across test and control. **Official**, `references/incrementality.md`.
  - Budgets move less than 20% during the test: the geo test guidance says a larger change starts a new learning period. **Official**, `references/incrementality.md`.
  - Ads, keywords and bids are the same in test and control regions. **Practitioner rule.**
  - The outcome is counted the same way in every region: the business's own leads or sales by region. **Practitioner rule.**
- **Decision rule, written before the test starts:** On 2026-12-06, run the readout with the pre-period 2026-09-14 to 2026-11-15. If the 95% interval for the change in leads in the test regions is entirely below zero, the ads cause leads at that size: compare the cost of each incremental one with what it is worth to the business. If the interval includes zero, the test found no effect of 18% or more.
- **Each week** (2026-11-22, 2026-11-29, 2026-12-06), check:
  - Cost in the go dark or holdback regions is zero, or the planned level for a heavy up.
  - The control regions spent at their usual level.
  - The business's leads or sales by region arrived for every day.
  - No campaign added or changed location targets during the test.
  - Do not call the result from a weekly look. Read it once, on the stop date.

## Lift studies run by Google

**Official** (`references/incrementality.md`): user based Conversion Lift needs at least 1,000 observed conversions, a 5,000 US dollar minimum campaign budget and a compatible conversion action, runs at least 7 days (14 recommended), and goes through a Google account representative. It is not available to every account.
- Over the 21 day run, these campaigns would record about 171 conversions and spend about 7,942.01 in the account's currency, at their daily average.
- That is below the 1,000 conversion floor.

## How the numbers were made

- The rows add up to the file's own total (Total: Account (added up over 90 days)): Cost 38,947.52, Conversions 760.00.
- Days with no row in the report count as zero between the first and last day.
- The lift sizes use the normal approximation written out in `references/test-math.md`: confidence 95% two sided, power 80%.
- For a geo test the noise is the test regions' daily stray from what the control regions predict, with a pre-period three times the test length.
- Measured days are rounded up to whole weeks. The longest plan allowed is 56 days (`--max-days`).

## What this did not cover

- The report shows what Google Ads attributed, not what the ads caused. That is the question the test answers.
- Whether the account can run Google's own lift studies: only Google can confirm that.
- Late conversions: the readout should wait until the conversion lag has passed.
