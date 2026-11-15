# Reading a finished test

Written by hand. To be re-read against the source before release.

How far to trust a readout, and what to check before telling the person what it means. The checks are **Practitioner rules** unless a line says **Official**. The numbers behind them are in `references/test-math.md`.

## Google's experiment report comes first

When Google's experiment report gives a difference, a range, significance or a p-value, show Google's figure as given. **Official** (`references/experiments-and-planning.md`): read significance from Google's figures rather than recomputing it from campaign totals. Our own range is for files that have the arms by day and no Google figure.

## Finding the test when the person does not remember it

People often forget which regions were in a test and when it ran. The `find` step looks for regions whose cost stopped for 7 days or more, groups the ones that stopped together, lists the regions that kept spending as candidate controls, and gives a first look at the outcome against them.

- A stop in the cost data is a candidate, not a fact: a budget can run out, a campaign can be paused for another reason.
- Put the candidate to the person before reading it. A readout on a window found this way says so at the top (`--inferred`).

## The stated length against the data

The person's memory of the dates and the cost data can differ. The readout checks the days the test group's cost was actually off.

- **Cost stayed off longer than stated:** the readout shows the stated window and the full off period. The full period has more days and a narrower range; use it unless the person says the extra days were something else.
- **Cost came back early:** days with ads on are inside the window and pull the effect toward zero. Shorten the window to the off days.
- **Cost was off before the stated start:** the pre-period holds test days. Move the start.

## The pre-period fit

- **Official** (`references/incrementality.md`): keep at least 3x the test length in pre-test data.
- R squared says how closely the control group tracked the test group before the test. A low value widens the range; it does not bias the result on its own. The placebo check is the better guide to whether the fit is good enough.

## The placebo check and the verdict

The same model is run on every window of the test's length inside the pre-period, where nothing was tested. If gaps as large as the real one turn up often there, the real gap could be ordinary noise, whatever the range says. The verdict:

| Verdict | Rule |
|---|---|
| **Strong** | The range excludes zero, a gap this large appeared in 5% or fewer of the placebo windows, and the pre-period is at least 3x the test |
| **Directional only** | The range excludes zero and the share is 20% or less; or the range includes zero but the share is 10% or less; or the pre-period has room for fewer than 10 placebo windows and the range excludes zero |
| **Not readable** | Anything else |

Say "Directional only" plainly: the direction is likely, the size is not settled, and no budget decision should rest on the number alone.

## Control regions that moved on their own

A control region with its own event (a flood, a new branch, a local promotion) moves the prediction for the test group. Each control is read against the others with the same model. It is flagged when its range excludes zero and a gap that large appeared in 5% or fewer of its own placebo windows. The readout then shows the result without it. Ask the person what happened there; if they confirm an event, lead with the result without that region.

## What a geo test can say

- It reads every campaign in the test regions together. It cannot say which campaign caused the leads, and it cannot be split by campaign afterwards.
- It measures the outcome the business counts, not Google Ads' Conversions, which stop when the ads stop.
- The share of attributed conversions that were incremental compares the ads' effect per day with what Google Ads attributed per day in the same regions before the test. Below 100% means Google Ads credits the ads with some conversions that would have happened anyway.
- Profit per unit of spend is incremental value x margin, divided by the spend removed or added, minus 1. Above zero, the ads in those regions make money at that margin; break even is 1 / margin of value per unit of spend.
