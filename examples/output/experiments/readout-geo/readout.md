# Test readout


**The test regions and dates were found from the data, not given by the person.** Confirm them before acting on this.

## The answer

**Verdict: Strong.** In the test group (Evanston; Skokie; Oak Park), with ads switched off, from 2026-10-22 to 2026-11-04: Leads came in at 310.0 against 438.1 predicted from the control group: a difference of -128.1 (-29.2%), range -189.4 to -66.7 at 95% confidence. That is distinguishable from zero.

Why that verdict: a gap this large appeared in 0% of 69 placebo windows in the pre-period. Fit before the test: R squared 0.38.

- The ads caused about 128.1 leads over the 14 days (9.1 a day), range 66.7 to 189.4.
- Spend removed: 1,934.34 over the 14 days.
- Cost per incremental lead: 15.11 (range 10.21 to 28.98).
- Google Ads attributed 13.89 conversions a day to the test group before the test. The ads caused 9.1 leads a day: 66% of the attributed figure (range 34% to 97%). Attributed is not incremental.
- Incremental revenue per unit of spend: 15.83 (range 7.96 to 23.70).
- **Profit:** at this margin, each unit of spend returns 5.33 of profit after paying for itself (range 2.18 to 8.48); 10,315.90 in total. Break even is 2.50 of revenue per unit of spend. The ads make money.

**The stated test and the data differ: cost stayed off until 2026-11-11 (when the cost file ends), after the stated end of 2026-11-04.**

Over the full off period, 2026-10-22 to 2026-11-11 (21 days): **Verdict: Strong.** Leads came in at 474.0 against 658.0 predicted from the control group: a difference of -184.0 (-28.0%), range -262.0 to -106.0 at 95% confidence. That is distinguishable from zero.
- The ads caused about 184.0 leads over the 21 days (8.8 a day), range 106.0 to 262.0.
- Spend removed: 2,898.91 over the 21 days.
- Cost per incremental lead: 15.75 (range 11.06 to 27.34).
- Google Ads attributed 13.89 conversions a day to the test group before the test. The ads caused 8.8 leads a day: 63% of the attributed figure (range 36% to 90%). Attributed is not incremental.
- Incremental revenue per unit of spend: 15.55 (range 8.86 to 22.23).
- **Profit:** at this margin, each unit of spend returns 5.22 of profit after paying for itself (range 2.55 to 7.89); 15,128.10 in total. Break even is 2.50 of revenue per unit of spend. The ads make money.

**Control regions that moved on their own:** Niles, +42.3% against the other controls (range +23.7% to +60.9%).

Without Niles: **Verdict: Strong.** Leads came in at 310.0 against 412.1 predicted from the control group: a difference of -102.1 (-24.8%), range -165.0 to -39.1 at 95% confidence. That is distinguishable from zero.
- The ads caused about 102.1 leads over the 14 days (7.3 a day), range 39.1 to 165.0.
- Spend removed: 1,932.86 over the 14 days.
- Cost per incremental lead: 18.94 (range 11.71 to 49.40).
- Google Ads attributed 13.89 conversions a day to the test group before the test. The ads caused 7.3 leads a day: 52% of the attributed figure (range 20% to 85%). Attributed is not incremental.
- Incremental revenue per unit of spend: 12.57 (range 4.47 to 20.67).
- **Profit:** at this margin, each unit of spend returns 4.03 of profit after paying for itself (range 0.79 to 7.27); 7,786.84 in total. Break even is 2.50 of revenue per unit of spend. The ads make money.

## To confirm with the person

1. The test regions (Evanston; Skokie; Oak Park) and the dates (2026-10-22 to 2026-11-04): are they the test?
2. Which dates the test really ran: the stated window, or the full time cost was off.
3. What happened in Niles during the test (an event, a branch, a promotion).
4. Whether every campaign was off in the test regions, or only some. A geo test reads all campaigns in a region together; it cannot say which campaign caused the result.
5. Whether anything else changed in the test regions during the test.

## Checks on the result

- Pre-period: 2026-08-01 to 2026-10-21, 82 days, at least three times the test's 14 days. **Official** (`references/incrementality.md`): keep at least 3x the test length in pre-test data.
- Placebo check: the same model on 69 pseudo test windows of 14 days inside the pre-period. The typical gap was 5.1%, the largest 21.0%; the real gap is 29.2%.
- Verdict rule: **Strong** when the range excludes zero, a gap this large appeared in 5% or fewer of the placebo windows, and the pre-period is at least three times the test. **Directional only** when the range excludes zero and the share is 20% or less, or the range includes zero but the share is 10% or less. **Not readable** otherwise. Written in `references/test-math.md` and `references/reading-a-result.md`.
- Test length against the data: a day counts as off when the test group's cost is under 13.71, which is 10% of its usual spending day (137.05) before the test. Cost was off from 2026-10-22 to 2026-11-11.
- Control regions checked one by one against the others: Berwyn -15.5%; Cicero -10.9%; Des Plaines -2.7%; Niles +42.3% (moved); Park Ridge -2.2%. A region counts as moved when its range excludes zero and a gap that large appeared in 5% or fewer of its own placebo windows.

## How the numbers were made

- Time-based regression (Google Research, `references/incrementality.md`): test = a + b x control, fitted on the pre-period (a = 8.72, b = 0.469). The range uses the fit's leftover spread and the uncertainty in a and b, with a t value for 80 degrees of freedom. Formulas in `references/test-math.md`.
- Days with no row count as zero.
- The outcome file has no account total row, so the rows could not be checked against one.
- The rows add up to the cost report's own total (Total: Account (added up over 103 days)): Cost 32,144.68.
- Spend is treated as known when the cost per incremental result is worked out, as the method's authors do.
- Profit after ad cost = incremental value x margin, minus the spend. Break even is 1 / margin of value per unit of spend.

## What this did not cover

- A geo test reads every campaign in the test regions together. It cannot split the result by campaign.
- Anything that hit the test group and not the control group during the test (a local event, a competitor, the weather) shows up as an effect. The control check catches it only in the control regions.
- Results that arrive after the test ends, such as jobs booked later from leads in the test.
