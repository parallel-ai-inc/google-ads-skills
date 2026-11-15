# Test plan

Campaign report.
August 15, 2026 - November 12, 2026.

The data covers 43 days, 2026-10-01 to 2026-11-12, for Plumbing | Emergency.
Only the days from 2026-10-01 on are used, as asked, so an earlier change does not count as noise.
Amounts are in USD.

## The answer

Too little volume. A lift of 15% in conversions needs 359 measured days, longer than the 56 day limit. In 56 days the smallest lift this test could detect is 42%.

Design: a Google Ads custom experiment (a split of one campaign). Run 2026-11-16 to 2027-01-17, reading from 2026-11-23.

## The outcome, day by day

- Conversions a day: 4.53 on average, with a spread (standard deviation) of 2.14.
- No clear weekday pattern (p = 0.941). The plan still runs whole weeks.
- The noise used: the daily spread of the campaigns' conversions.

## What lift it can detect

At 95% confidence and 80% power:

| Measured days | Smallest lift it can detect |
|---|---|
| 14 | 102.9% |
| 21 | 78.2% |
| 28 | 64.9% |
| 42 | 50.4% |
| 56 | 42.4% |

## The plan

- **What changes:** Switch the bid strategy to Target CPA
- **Start:** 2026-11-16. **Left out at the start:** 7 days (the trial arm settling). **Reading:** 2026-11-23 to 2027-01-17, 56 days. **Stop:** 2027-01-17.
- **Stays fixed:**
  - The 50% split. It sets which auctions each arm can enter, not equal impressions or spend. **Official**, `references/experiments-and-planning.md`.
  - Experiment sync is turned off if edits made to the trial arm must not be overwritten. **Official**, `references/experiments-and-planning.md`.
  - The base campaign's budget, bid strategy, targets, keywords, ads and audiences, other than the change under test. **Practitioner rule.**
  - The conversion actions and their settings, in both arms. **Practitioner rule.**
- **Decision rule, written before the test starts:** On 2027-01-17, read Google's experiment report for conversions at 95% confidence. If the trial is higher and Google marks it statistically significant, apply the trial. If it is lower and significant, end the experiment and keep the original. If it is not significant, keep the original: the test found no lift of 42% or more.
- **Each week** (2026-11-22, 2026-11-29, 2026-12-06, 2026-12-13, 2026-12-20, 2026-12-27, 2027-01-03, 2027-01-10, 2027-01-17), check:
  - Both arms served all week. The trial's share of impressions is near the split; a gap is normal, a collapse is not.
  - No edits were made to either arm other than the planned change.
  - Conversions recorded every day in both arms. A day at zero is a tracking problem, not a result.
  - Neither arm is limited by budget more than the other (Search lost IS (budget)).
  - Do not call the result from a weekly look. Read it once, on the stop date.

## Eligibility for a custom experiment

**Official** (`references/experiments-and-planning.md`): custom experiments run on Search, Display, Demand Gen and Video campaigns whose base campaign is active, on its own daily budget and a standard (not portfolio) bid strategy. App and Shopping campaigns can't use them.

- **Plumbing | Emergency** (Search, Enabled): bid strategy: check it is not a portfolio strategy.

## Lift studies run by Google

**Official** (`references/incrementality.md`): user based Conversion Lift needs at least 1,000 observed conversions, a 5,000 US dollar minimum campaign budget and a compatible conversion action, runs at least 7 days (14 recommended), and goes through a Google account representative. It is not available to every account.
- Over the 63 day run, these campaigns would record about 286 conversions and spend about 17,995.86 in the account's currency, at their daily average.
- That is below the 1,000 conversion floor.

## How the numbers were made

- The rows add up to the file's own total (Total: Account (added up over 90 days)): Cost 38,947.52, Conversions 760.00.
- Days with no row in the report count as zero between the first and last day.
- The lift sizes use the normal approximation written out in `references/test-math.md`: confidence 95% two sided, power 80%.
- For an experiment the spread is treated as noise in each arm, scaled to its share. This is cautious: both arms run on the same days, so swings they share cancel. Counts are never treated as less noisy than a Poisson count.
- Measured days are rounded up to whole weeks. The longest plan allowed is 56 days (`--max-days`).

## What this did not cover

- The report shows what Google Ads attributed, not what the ads caused. That is the question the test answers.
- Whether the account can run Google's own lift studies: only Google can confirm that.
- Late conversions: the readout should wait until the conversion lag has passed.
