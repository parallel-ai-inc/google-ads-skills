# Bid strategy review

Campaign report.
September 14, 2026 - November 12, 2026.

Read from 2026-09-14 to 2026-11-12 (60 days). The last 7 days are left out of every target comparison, because conversions are still arriving for them, so comparisons end on 2026-11-05. Money is in USD, as the report states.
**No conversion cycle was given, so 7 days was assumed.** It sets three things: the last 7 days left out of target comparisons, the hold after a change (2 conversion cycles, 14 days), and when a change can first be checked. Rerun with --cycle-days and the real figure to replace it.

## The short answer

- **Scale candidate:** Plumbing | Emergency, Plumbing | Water Heaters, 57.0% of the serving campaigns' cost.
- **Missing its target:** Sewer Line | Search, 18.6% of the serving campaigns' cost.
- **Pause candidate:** Gas Line | Demand Gen, 2.7% of the serving campaigns' cost.
- **Hold: learning:** Drain Cleaning | Search, 17.2% of the serving campaigns' cost.
- **Not judged on conversions:** Brand, 4.6% of the serving campaigns' cost.
- **Not serving:** Plumbing | Holiday Promo.

Shares are of 32,342.75, the cost of the 6 serving campaigns from 2026-09-14 to 2026-11-05.

## Campaigns

| Campaign | Bid strategy | Target | Your goal | Actual | Gap to target | Gap to goal | Conv. read | Learning | Latest change | Limit | Category |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Plumbing \| Emergency | Target CPA | 60.00 | 60.00 | 50.02 | -16.6% | -16.6% | 245.7 | No | none read | Budget and rank (top IS) | Scale candidate |
| Plumbing \| Water Heaters | Target ROAS | 4.00 (400%) | none | 5.12 (512%) | +27.9% | n/a | 76.3 | No | target, 43 days before | Rank or target (top IS) | Scale candidate |
| Sewer Line \| Search | Target CPA | 55.00 | 60.00 | 81.99 | +49.1% | +36.7% | 73.2 | No | none read | Rank or target (top IS) | Missing its target |
| Gas Line \| Demand Gen | Target CPA | 70.00 | 60.00 | n/a | n/a | n/a | 0.0 | No | campaign created, 30 days before | Unknown: no Search impression share | Pause candidate |
| Drain Cleaning \| Search | Target CPA | 50.00 | 60.00 | 69.02 (early) | +38.0% (early) | +15.0% (early) | 11.5 (early) | Yes | budget, 4 days before | Rank or target (top IS) | Hold: learning |
| Brand | Target impression share | none | none | 6.64 | n/a | n/a | 224.8 | No | none read | Neither: demand or reach (top IS) | Not judged on conversions |
| Plumbing \| Holiday Promo | Maximize conversions | none | 60.00 | 58.85 | n/a | -1.9% | 20.7 | No | none read | Not serving | Not serving |

Target is the campaign's own target. Your goal is the limit you gave: the most per conversion, or the least conv. value / cost. Actual is over each campaign's read period, which starts after its latest bid strategy or target change. (early) marks the days since a change that are too recent or too thin to judge.

## Each campaign

### Plumbing | Emergency: Scale candidate

Target CPA, Search. Read period 2026-09-14 to 2026-11-05 (53 days): cost 12,290.86, conversions 245.7, conv. value 71,339.60, cost / conv. 50.02, conv. value / cost 5.80, conv. rate 15.54%, avg. CPC 7.77.
Latest changes read: "Ad schedule changed" on 2026-11-13 (after the report's last day).
Daily budget 240.00. Search lost top IS (budget) 30.9%, Search lost top IS (rank) 13.8%. Limit: Budget and rank (top IS).
- Cost / conv. 50.02 against its Target CPA of 60.00: 16.6% apart, better than it. Chance alone moves a figure built on 245.7 conversions by about 6.4%.
- Against your goal of 60.00: 16.6% apart, better than it.
- Lever: Budget first, then a looser target.
- Budget evidence: it spent 231.90 a day on average in the read period against a daily budget of 240.00. Its Search lost top IS (budget) of 30.9% implies at most about 103.79 a day more at the same cost per click. That is an upper bound: the next click usually costs more, and the top version counts only impressions lost among top ads, so it overstates the room. A first step of up to 51.90 a day, half of it, leaves room for a second step once the first is read (**Practitioner rule**). Google may bill up to 7,296.00 in a month at today's budget, 30.4 times the daily budget.
- Step size (references/smart-bidding.md): The reference files give no step size for this campaign type. Google says Smart Bidding reacts at once to a target change of any size on Search and Shopping, without resetting learning, and that a large move changes spend or volume by a similar amount. The step is a judgment. The evidence is the gap between actual and target. Its target is already at your goal, so any looser target goes past your limit. Ask before loosening it.
- First fair check after a change: about 14 days, the longest of: 2 conversion cycles, 14 days, time to 30 conversions at its pace, 7 days.
- **Official** (references/smart-bidding.md): since August 17, 2026 a Target CPA campaign that is limited by budget bids toward its target rather than beating it, so added budget buys conversions at about the target, not at today's figure. Set the target you want before adding budget.

### Plumbing | Water Heaters: Scale candidate

Target ROAS, Search. Read period 2026-10-01 to 2026-11-05 (36 days): cost 4,140.78, conversions 76.3, conv. value 21,192.13, cost / conv. 54.26, conv. value / cost 5.12, conv. rate 11.74%, avg. CPC 6.37.
Before its latest target change on 2026-09-30: cost 1,873.92, conversions 31.2, cost / conv. 60.08, conv. value / cost 4.73.
Latest changes read: target on 2026-09-30 (43 days before the report's last day).
Daily budget 160.00. Search lost top IS (budget) 0.0% (43 days written < 10%), Search lost top IS (rank) 38.1%. Limit: Rank or target (top IS).
- Conv. value / cost 5.12 (512%) against its Target ROAS of 4.00 (400%): 27.9% apart, better than it. Chance alone moves a figure built on 76.3 conversions by about 11.4%.
- Moved the unexpected way: its target was loosened from 4.50 (450%) to 4.00 (400%) on 2026-09-30, yet conv. value / cost went from 4.73 (473%) to 5.12 (512%) (+8.2%), and conversions a day from 1.95 to 2.12. A looser target usually trades efficiency for volume. The move is within what chance alone explains (about 17.9% on 31.2 conversions). Something else may have moved too: demand, competition, conversion values or the mix of searches.
- Lever: A looser target.
- Step size (references/smart-bidding.md): The reference files give no step size for this campaign type. Google says Smart Bidding reacts at once to a target change of any size on Search and Shopping, without resetting learning, and that a large move changes spend or volume by a similar amount. The step is a judgment. The evidence is the gap between actual and target.
- First fair check after a change: about 24 days, the longest of: 2 conversion cycles, 14 days, time to 50 conversions at its pace, 24 days.
- 63.8 conversions in the 30 days to 2026-11-05, meeting the 15 Google asks for before Target ROAS on most campaign types (**Official**, references/smart-bidding.md).

### Sewer Line | Search: Missing its target

Target CPA, Search. Read period 2026-09-14 to 2026-11-05 (53 days): cost 6,002.72, conversions 73.2, conv. value 32,858.49, cost / conv. 81.99, conv. value / cost 5.47, conv. rate 10.89%, avg. CPC 8.93.
Latest changes read: "Keywords added: 6" on 2026-09-22 (51 days before the report's last day).
Daily budget 150.00. Search lost top IS (budget) 0.0% (60 days written < 10%), Search lost top IS (rank) 47.4%. Limit: Rank or target (top IS).
- Cost / conv. 81.99 against its Target CPA of 55.00: 49.1% apart, worse than it. Chance alone moves a figure built on 73.2 conversions by about 11.7%.
- Against your goal of 60.00: 36.7% apart, worse than it.
- Lever: Its target is already at or stricter than your goal, so lowering it further is unlikely to help on its own. Check search terms, conversion rate and the landing page first.
- First fair check after a change: about 22 days, the longest of: 2 conversion cycles, 14 days, time to 30 conversions at its pace, 22 days.
- Its target of 55.00 is stricter than your goal of 60.00.

### Gas Line | Demand Gen: Pause candidate

Target CPA, Demand Gen. Read period 2026-10-14 to 2026-11-05 (23 days): cost 820.22, conversions 0.0, conv. value 0.00, cost / conv. n/a, conv. value / cost 0.00, conv. rate 0.00%, avg. CPC 0.91.
Latest changes read: campaign created on 2026-10-13 (30 days before the report's last day).
Daily budget 40.00. Search lost top IS (budget) n/a, Search lost top IS (rank) n/a. Limit: Unknown: no Search impression share.
- Spent 820.22 with no conversion between 2026-10-14 and 2026-11-05: 11.7 times the reference cost per conversion of 70.00, where the test needs 3.
- Lever: Pause, or fix tracking if conversions should be there.
- First fair check after a change: about 14 days, the longest of: 2 conversion cycles, 14 days, one Demand Gen weekly step, 7 days.
- Its target of 70.00 is looser than your goal of 60.00. Your goal is your limit: ask whether to bring the target to it.
- Created 30 days before the report's last day. Google's Demand Gen guide asks for no changes during the initial learning period, and its learning page speaks of up to around 50 conversion events or 3 conversion cycles (**Official**, references/learning-phase.md).
- Which wins here: the case for pausing, once tracking is confirmed. **Practitioner rule.** Google's caution protects a campaign that is gathering conversions to learn from. This one has recorded none after spending 11.7 times its reference cost per conversion, so the learning period has nothing to learn from, and Smart Bidding is a measurement system first (references/smart-bidding.md).
- Confirm first that conversions are being recorded for it: the conversion actions it bids toward record conversions in other campaigns over the same days, and its goals include them. If tracking is broken, fix tracking instead of pausing.

### Drain Cleaning | Search: Hold: learning

Target CPA, Search. No read period yet: every day since its latest bid strategy change falls inside the 7 day conversion cycle.
Before its latest bid strategy change on 2026-11-05: cost 5,462.06, conversions 96.8, cost / conv. 56.41, conv. value / cost 3.76.
Latest changes read: bid strategy on 2026-11-05 (7 days before the report's last day), target on 2026-11-05 (7 days before the report's last day), budget on 2026-11-08 (4 days before the report's last day).
Daily budget 150.00. Search lost top IS (budget) 9.7% (1 day written < 10%), Search lost top IS (rank) 25.2%. Limit: Rank or target (top IS).
- Google shows it as learning: status Eligible (Learning), reason bidding strategy learning.
- Early read, not yet judgeable: in the 7 days since its latest bid strategy change (2026-11-06 to 2026-11-12), cost 795.16, conversions 11.5, cost / conv. 69.02 against its Target CPA of 50.00 (+38.0%). Recent days still gain conversions, and 11.5 conversions is fewer than the 30 needed. A proper read is possible around 2026-12-01, at its pace since the change.
- No day after the change is outside the 7 day conversion cycle yet, so there is no read period.
- Moved the unexpected way: a target of 50.00 was set on 2026-11-05, stricter than its earlier 56.41, yet cost / conv. went from 56.41 to 69.02 (+22.4%) in the early read, and conversions a day from 1.86 to 1.65. A stricter target usually trades volume for efficiency. The move is within what chance alone explains (about 29.5% on 11.5 conversions). Something else may have moved too: demand, competition, conversion values or the mix of searches.
- Its target of 50.00 is stricter than your goal of 60.00.
- Stacked changes close together: bid strategy and target on 2026-11-05, budget on 2026-11-08. Their effects cannot be told apart in this data (references/learning-phase.md).

### Brand: Not judged on conversions

Target impression share, Search. Read period 2026-09-14 to 2026-11-05 (53 days): cost 1,493.66, conversions 224.8, conv. value 65,264.67, cost / conv. 6.64, conv. value / cost 43.69, conv. rate 21.03%, avg. CPC 1.40.
Daily budget 50.00. Search lost top IS (budget) 0.0% (60 days written < 10%), Search lost top IS (rank) 0.0% (60 days written < 10%). Limit: Neither: demand or reach (top IS).
- Target impression share bids for visibility, not conversions, so it is not judged against a cost per conversion.

### Plumbing | Holiday Promo: Not serving

Maximize conversions, Search. Read period 2026-09-14 to 2026-11-05 (53 days): cost 1,215.77, conversions 20.7, conv. value 4,604.44, cost / conv. 58.85, conv. value / cost 3.79, conv. rate 7.12%, avg. CPC 4.19.
Latest changes read: "Status changed from Enabled to Paused" on 2026-10-06 (37 days before the report's last day).
Daily budget 60.00. Search lost top IS (budget) 0.0% (22 days written < 10%), Search lost top IS (rank) 20.2%. Limit: Not serving.
- Campaign status is Paused, so it is left out of every comparison and every move.

## Account

| Bid strategy | Campaigns | Cost | Conversions | Conv. value | Cost / conv. | Conv. value / cost |
|---|---|---|---|---|---|---|
| Target CPA | 4 | 24,714.73 | 417.1 | 125,016.16 | 59.26 | 5.06 |
| Target ROAS | 1 | 6,134.36 | 109.6 | 30,608.35 | 55.98 | 4.99 |
| Target impression share | 1 | 1,493.66 | 224.8 | 65,264.67 | 6.64 | 43.69 |
| Maximize conversions | 1 | 1,215.77 | 20.7 | 4,604.44 | 58.85 | 3.79 |

Two account lines, 2026-09-14 to 2026-11-05:

| Line | What it includes | Cost | Conversions | Conv. value | Cost / conv. | Conv. value / cost |
|---|---|---|---|---|---|---|
| All campaigns | All 7 campaigns in the report, paused ones included | 33,558.52 | 772.1 | 225,493.62 | 43.46 | 6.72 |
| Without Brand | The 5 serving campaigns other than Brand. This is the account comparison | 30,849.09 | 526.6 | 155,624.51 | 58.58 | 5.04 |

Check against the file's own Total: Filtered campaigns rows: cost 38,007.59 against 38,007.59, conversions 865.54 against 865.54. They match.

## Change history

7 changes read, 4 of them to a bid strategy, target, budget, conversion setting or a new campaign.

| Date | Campaign | What changed | Days before the report's last day |
|---|---|---|---|
| 2026-11-08 | Drain Cleaning \| Search | Budget changed from 120.00 to 150.00 | 4 |
| 2026-11-05 | Drain Cleaning \| Search | Bid strategy changed from Maximize conversions to Target CPA Target CPA set to 50.00 | 7 |
| 2026-10-13 | Gas Line \| Demand Gen | Campaign created | 30 |
| 2026-09-30 | Plumbing \| Water Heaters | Target ROAS changed from 450% to 400% | 43 |

## Thresholds

- Enough conversions to judge a bid strategy: 30 in the period read, 50 for Target ROAS. **Official**, references/smart-bidding.md.
- Target ROAS readiness: 15 conversions in the last 30 days for most campaign types. **Official**, references/smart-bidding.md.
- Better or worse than target: only a gap wider than chance counts. A figure built on n conversions moves by about 1 / square root of n by chance alone: 18% at 30 conversions, 10% at 100. Statistics from the campaign's own count.
- Limited by budget: Google's status says so, or the lost impression share to budget averages 10% or more. Limited by rank: the lost share to rank averages 10% or more. **Practitioner rule.** Each day is weighted by the impressions it was eligible for.
- Pause candidate: no conversion after spending 3 times the reference cost per conversion (its Target CPA, else your goal, else the account comparison). If it converted at that cost, a run of zero this long would happen about 5% of the time by chance.
- Recent change: a bid strategy, target, budget or conversion change less than 2 conversion cycles ago, or with fewer conversions since than the number needed to judge. **Practitioner rule**, references/tcpa-framework.md, and **Official** 1 to 2 conversion cycles, references/smart-bidding.md.
- Demand Gen steps: 5 to 10% a week, no more than 15%. **Official**, Google's Demand Gen guide, references/learning-phase.md.
- First budget step: at most half the room that lost impression share to budget implies, so budget moves in at least two steps, each read before the next. **Practitioner rule.**
- Performance Max check window: 1 to 2 weeks or one conversion cycle after a significant change. **Official**, references/learning-phase.md.

## How the numbers were made

- The conversion cycle is 7 days, assumed because none was given. The last 7 days are left out of target comparisons, a change is held for 2 cycles, and checks wait at least that long.
- An early read covers the days since a change, up to the report's last day, when the read period after it is empty or has too few conversions. It is shown, never judged.
- Each campaign's read period runs from the day after its latest bid strategy, target or campaign creation change in the report to 2026-11-05. Without a change history it is the whole report.
- Cost / conv. is cost divided by conversions. Conv. value / cost is conv. value divided by cost, written as a ratio: 4.00 is 400%.
- The target is the latest value in the report's target column, or the latest set in the change history.
- Impression share columns read: Search lost top IS (budget) and Search lost top IS (rank). These are the top of page versions: they count impressions lost among top ads, not impressions lost altogether, and run higher. Add Search lost IS (budget) and Search lost IS (rank) for the plain read (references/impression-share-and-editor.md).
- Status, Status reasons and Campaign status are read from each campaign's latest day.
- Days to the needed conversions use the campaign's average conversions per day in its read period.

## What this did not cover

- Conversion tracking quality, conversion values, search terms, landing pages, auction insights and the bid strategy report's own simulators. A target can only be as good as the conversions behind it.
- Profit. Conv. value / cost is not margin.
- Portfolio bid strategies and shared budgets are noted where the report shows them, not modelled.
- Nothing was changed in any account.
