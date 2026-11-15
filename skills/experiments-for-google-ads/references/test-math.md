# Test math: the formulas behind the scripts

Written by hand. To be re-read against the source before release.

This file says how every number in `design.py`, `readout.py` and `roi.py` is made, and where the method comes from. The Google Ads facts on this page are **Official** only where a Google page is linked. The statistics are standard methods, not Google Ads rules.

## Notation

- z(c) is the normal quantile for a two sided confidence c: 1.96 at 95%, 1.64 at 90%. z(p) for power p: 0.84 at 80%.
- Z = z(confidence) + z(power).
- mu is the outcome's average per day, s2 its variance per day, n the measured days, d the relative lift.

## Sizing a test (`design.py`): the normal approximation

**Weekday pattern.** A one way analysis of variance of the daily values by weekday. F = (between weekday mean square) / (within weekday mean square), with 6 and n - 7 degrees of freedom. Its p value uses Paulson's normal approximation: z = ((1 - 2/(9 d2)) F^(1/3) - (1 - 2/(9 d1))) / sqrt(2/(9 d2) F^(2/3) + 2/(9 d1)). When p < 0.05 the noise used is the within weekday variance, and the plan runs whole weeks. Source: Paulson (1942), Annals of Mathematical Statistics 13; Abramowitz and Stegun, Handbook of Mathematical Functions, chapter 26.

**Experiment (a split of one campaign, trial share s).** Each arm's daily outcome is treated as having mean s mu and variance s s2 (variance scales with share, as for a sum of many independent events). The log of trial over control then has variance CV2 (1/s + 1/(1 - s)) / n, where CV2 = s2 / mu^2, and never less than 1 / mu for a count (the Poisson floor).

- Days needed: n = Z^2 CV2 (1/s + 1/(1 - s)) / ln(1 + d)^2.
- Smallest lift in n days: d = exp(Z sqrt(CV2 (1/s + 1/(1 - s)) / n)) - 1.
- This is cautious: both arms run on the same days, so swings they share cancel, and the real noise is lower.

**Geo test.** The readout predicts the test regions from the control regions (time-based regression, below). With a pre-period of 3 n days, the variance of the summed prediction error over n days is about r2 n (1 + 1/3), where r2 is the residual variance of the test regions on the control regions.

- Days needed: n = Z^2 r2 (4/3) / (d mu_t)^2, where mu_t is the test regions' daily average.
- Without a geographic report, r2 is taken as the test share times s2 (the control regions explain none of the day to day spread): the cautious end.

**On and off test (share f of days off).** The effect is the off days' average minus the on days' average after the weekday pattern. Its variance is s2 / (n f (1 - f)).

- Days needed: n = Z^2 s2 / (f (1 - f) (d mu)^2).

Source for this form of sample size: NIST/SEMATECH e-Handbook of Statistical Methods, section on sample sizes for comparing means, https://www.itl.nist.gov/div898/handbook/.

## Reading a test (`readout.py`)

**Google's own figures come first.** **Official:** Google's experiment scorecard shows, under each metric, the difference between the trial and the original campaign and a range for that difference; a statistically significant result carries a blue asterisk, and the confidence level can be changed (the page says 80% is the default). The Results column reads Control campaign, Treatment campaign, or No clear winner or In progress. The page does not describe a download of these figures. Source: Google Ads Help, Monitor your experiments, https://support.google.com/google-ads/answer/6318747 (read 2026-11-13). `references/experiments-and-planning.md` adds that Google reports per arm results with a margin of error and a p-value, and to read significance from those.

**Two arms by day (our own range).** For a metric that is a ratio of sums in each arm, such as Cost / conv. = sum(cost) / sum(conversions), the lift is L = (A/B) / (C/D) - 1, with A, B the trial's sums and C, D the control's. By the delta method, Var(ln(L + 1)) = n g' S g, where g = (1/A, -1/B, -1/C, 1/D) and S is the covariance of the daily values (a, b, c, d) across the n days. For a plain sum (Conversions) only A and C are used, and the ratio is scaled by (1 - s)/s for an uneven split. The range is ln(L + 1) plus or minus t(n - 1) times the standard error, turned back with exp. Source: the ratio estimator in Cochran, Sampling Techniques (1977), chapter 6.

**Two arms in total only.** Counts are treated as Poisson: Var(ln total) = 1 / total in each arm. A rate x out of m (Conv. rate, CTR) is binomial: Var(ln rate) = (1 - x/m) / x. Cost, Cost / conv. and Conv. value / cost get no range without the days.

**Time-based regression (geo test, or two campaigns).** Fit test_t = a + b control_t on the pre-period (n days). Predict each test day from that day's control value. The effect is sum(actual - predicted) over the m test days. Its variance is r2 (m + m^2/n + (sum(x_test) - m mean(x_pre))^2 / Sxx), where r2 is the fit's residual variance and Sxx the pre-period sum of squares of the control around its mean. The range uses t with n - 2 degrees of freedom. Cost per incremental result divides the change in spend (the same regression run on Cost) by the effect, treating spend as known, as the method's authors do for incremental return on ad spend. Source: Kerman, Wang and Vaver (2017), Estimating Ad Effectiveness using Geo Experiments in a Time-Based Regression Framework, Google Research, https://research.google/pubs/estimating-ad-effectiveness-using-geo-experiments-in-a-time-based-regression-framework/. **Official** (`references/incrementality.md`): keep at least 3x the test length in pre-test data.

**Placebo check and verdict (geo test, or two campaigns).** For every window of m days inside the pre-period (step one day), fit the same regression on the other pre-period days and predict the window. Its gap is |effect| / predicted. The placebo share is the share of windows whose gap is at least the real gap. Verdict: **Strong** when the range excludes zero, the share is 0.05 or less, and the pre-period is at least 3m; **Directional only** when the range excludes zero and the share is 0.20 or less, or the range includes zero and the share is 0.10 or less, or fewer than 10 windows fit and the range excludes zero; **Not readable** otherwise. These cut-offs are this skill's rules, chosen to match the usual 5% and to say plainly when a result is weaker; they are not Google's. A control region is flagged as moved on its own when the same regression of it on the other controls has a range that excludes zero and a placebo share of 0.05 or less.

**Test length against the data.** A day is off when the test group's cost is under 10% of its median spending day in the pre-period. The off run is every consecutive off day around the stated start.

**Profit.** Incremental profit per unit of spend = incremental value x margin / spend change - 1. Break even incremental value per unit of spend = 1 / margin. Incremental share of attributed = incremental outcome per day / Google Ads' attributed conversions per day in the test group before the test.

**On and off.** Least squares of the daily outcome on seven weekday indicators plus one indicator for the off days. The off coefficient is the change per off day; its range uses t with n - 8 degrees of freedom.

**t values.** The t quantile uses the Cornish-Fisher expansion of the normal quantile (Abramowitz and Stegun 26.7.5; Hill 1970, Communications of the ACM 13). Two sided p values for t use Abramowitz and Stegun 26.7.8.

## Return on investment (`roi.py`)

Business arithmetic, not Google Ads rules:

- Profit after ad cost = Conv. value x gross margin - Cost.
- Break even Conv. value / cost = 1 / margin. At a 40% margin it is 2.50: each unit of cost must bring 2.50 of value for the margin on it to pay the cost back.
- Break even Cost / conv. = (Conv. value / Conversions) x margin.
- A campaign's call: a Poisson range on its conversion count, conversions plus or minus z(c) sqrt(conversions), scales its Conv. value / cost with value per conversion held fixed. Profitable when the whole range is above break even, loses money when it is below, too few conversions to call otherwise.
- How value grows with spend: least squares of ln(daily value) on ln(daily cost), with weekday indicators when there are 28 days or more. The slope b is the percent change in value for a 1% change in spend. The next dollar's Conv. value / cost is b times the recent Conv. value / cost (the marginal return of a constant elasticity curve). It pays when that is above 1 / margin. It is an estimate from observed days, not an experiment: days with more spend often had more demand too. When more than 25% of days with spend had no value, or fewer than 21 days had both, it uses full Monday to Sunday weeks and needs 12. When the spread of log spend is under 0.10, spend hardly varied and the curve is not read.
