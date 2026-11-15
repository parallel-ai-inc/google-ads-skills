# Bid strategy plan

Based on the campaign report from 2026-09-14 to 2026-11-12. Results are read through 2026-11-05, leaving out the most recent days while their conversions are still arriving. Nothing has been changed in the account.

## Where things stand

| Campaign | Bid strategy | Target | Your goal | Actual | Limit | Finding |
|---|---|---|---|---|---|---|
| Plumbing \| Emergency | Target CPA | 60.00 | 60.00 | 50.02 | Budget and rank (top IS) | Scale candidate |
| Plumbing \| Water Heaters | Target ROAS | 4.00 (400%) | none | 5.12 (512%) | Rank or target (top IS) | Scale candidate |
| Sewer Line \| Search | Target CPA | 55.00 | 60.00 | 81.99 | Rank or target (top IS) | Missing its target |
| Gas Line \| Demand Gen | Target CPA | 70.00 | 60.00 | n/a | Unknown: no Search impression share | Pause candidate |
| Drain Cleaning \| Search | Target CPA | 50.00 | 60.00 | 69.02 (early) | Rank or target (top IS) | Hold: learning |
| Brand | Target impression share | none | none | 6.64 | Neither: demand or reach (top IS) | Not judged on conversions |
| Plumbing \| Holiday Promo | Maximize conversions | none | 60.00 | 58.85 | Not serving | Not serving |

Target is the campaign's own target. Your goal is the limit you gave: the most per conversion, or the least conv. value / cost. Actual is cost per conversion, or conv. value / cost for value bidding, over each campaign's read period. (early) marks the days since a recent change: shown, not yet judged. Impression share was read from Search lost top IS (budget), which counts only impressions lost among top ads.

## The plan

Each step starts only when the checks of the step before are due. Change one thing per campaign per step, so each result can be read on its own.

### Step 1: now

| Campaign | Change | From | To | Change, % | Why |
|---|---|---|---|---|---|
| Plumbing \| Emergency | Daily budget | 240.00 | 280.00 | +16.7% | Beats its Target CPA of 60.00 and is limited by budget. Since August 17, 2026 more budget buys conversions at about the target, which the business accepts. |
| Plumbing \| Water Heaters | Target ROAS | 4.00 (400%) | 3.60 (360%) | -10.0% | Beats its Target ROAS of 4.00 and loses impressions to rank, so a lower target lets it enter more auctions. |
| Gas Line \| Demand Gen | Pause | Enabled | Paused |  | No conversions since it was created. |
| Sewer Line \| Search | Investigate |  |  |  | Misses its Target CPA of 55.00. Check search terms, the landing page and call tracking before changing the target. |
| Drain Cleaning \| Search | Hold |  |  |  | Learning after a switch to Target CPA and a budget change three days later. |

**Plumbing | Emergency: Daily budget.** Check: Cost / conv. against 60.00 and conversions a day against 4.64 in the review's read period, after about 14 days, once 30 conversions have come in. Roll back if cost / conv. is above 60.00, your goal, at that point. Your goal is the line: without it, the chance margin at 30 conversions would put it at 70.95.
- This step adds 40.00 a day (+16.7%). The review's Search lost top IS (budget) implies at most about 103.79 a day more at the same cost per click, an upper bound. After this step about 63.79 a day of that room is left for a next step, once this step's check is read. Google may bill up to 8,512.00 in a month at the new budget, against 7,296.00 now, 1,216.00 more, 30.4 times the daily budget (**Official**, references/scaling.md).
- The reference files set no limit on the size of a budget change: there is no universal rule that budget changes stay under 20% (references/scaling.md). The step is a judgment.
- **Official** (references/smart-bidding.md): since August 17, 2026 a budget limited Target CPA campaign bids toward its target, so the added budget buys conversions at about the target, not at today's figure. Confirm the target is the one the business wants.

**Plumbing | Water Heaters: Target ROAS.** Check: Conv. value / cost against 3.60 (360%) and conversions a day against 2.12 in the review's read period, after about 24 days, once 50 conversions have come in. Roll back if conv. value / cost is below 3.09 (309%) at that point.
- On Search and Shopping a target change moves bids at once and does not start learning, and a large move changes spend or volume by a similar amount (**Official**, references/smart-bidding.md). The reference files give no step size: this one is a judgment. Actual 5.12 (512%) against 4.00 (400%) (+27.9%).
- So plan for spend near 126.52 a day after this step, against 115.02 a day in the review's read period, if the budget allows it.
- Moved the unexpected way: its target was loosened from 4.50 (450%) to 4.00 (400%) on 2026-09-30, yet conv. value / cost went from 4.73 (473%) to 5.12 (512%) (+8.2%), and conversions a day from 1.95 to 2.12. A looser target usually trades efficiency for volume. The move is within what chance alone explains (about 17.9% on 31.2 conversions). Something else may have moved too: demand, competition, conversion values or the mix of searches.

**Gas Line | Demand Gen: Pause.** Check: The next day: the campaign shows Paused and spent nothing. Then watch the other campaigns' conversions for a conversion cycle.
- Which wins here: the case for pausing, once tracking is confirmed. **Practitioner rule.** Google's caution protects a campaign that is gathering conversions to learn from. This one has recorded none after spending 11.7 times its reference cost per conversion, so the learning period has nothing to learn from, and Smart Bidding is a measurement system first (references/smart-bidding.md).
- Confirm first that conversions are being recorded for it: the conversion actions it bids toward record conversions in other campaigns over the same days, and its goals include them. If tracking is broken, fix tracking instead of pausing.

**Sewer Line | Search: Investigate.** Check: Fix what the investigation finds, then run the review again before changing the target or budget.

**Drain Cleaning | Search: Hold.** Check: Run the review again around 2026-12-01, when a proper read of its latest change is possible.
- Moved the unexpected way: a target of 50.00 was set on 2026-11-05, stricter than its earlier 56.41, yet cost / conv. went from 56.41 to 69.02 (+22.4%) in the early read, and conversions a day from 1.86 to 1.65. A stricter target usually trades volume for efficiency. The move is within what chance alone explains (about 29.5% on 11.5 conversions). Something else may have moved too: demand, competition, conversion values or the mix of searches.

Google Ads Editor file for this step: step-1-for-google-ads-editor.csv. Import it with Account, Import, From file, review the proposed changes, then post. Blank cells change nothing.

### Step 2: about day 24, once step 1's checks are done

| Campaign | Change | From | To | Change, % | Why |
|---|---|---|---|---|---|
| Plumbing \| Water Heaters | Target ROAS | 3.60 (360%) | 3.30 (330%) | -8.3% | A second step toward more volume, only if the first held its return. |

**Plumbing | Water Heaters: Target ROAS.** Check: Conv. value / cost against 3.30 (330%) and conversions a day against 2.12 in the review's read period, after about 24 days, once 50 conversions have come in. Roll back if conv. value / cost is below 2.83 (283%) at that point.
- Follows the change in step 1. Values start from that step.
- On Search and Shopping a target change moves bids at once and does not start learning, and a large move changes spend or volume by a similar amount (**Official**, references/smart-bidding.md). The reference files give no step size: this one is a judgment.

Google Ads Editor file for this step: step-2-for-google-ads-editor.csv. Import it with Account, Import, From file, review the proposed changes, then post. Blank cells change nothing.

## How the numbers were made

- Cost per conversion is cost divided by conversions. Conv. value / cost is written as a ratio: 4.00 is 400%.
- Better or worse than target counts only a gap wider than chance: about 1 / square root of the conversions behind the figure.
- A check waits for the longest of: 2 conversion cycles, the days the campaign needs to bring in 30 conversions (50 for Target ROAS) at its recent pace, and Google's own window for Performance Max or Demand Gen.
- The roll back line allows the same chance margin at that number of conversions: about 18% at 30 and 14% at 50.
- A month bills at most about 30.4 times the daily budget.

## What this plan does not cover

- Profit and margin. Conv. value / cost is not profit.
- Conversion tracking, search terms and landing pages. Check them before tightening a target.
- What Google's own simulators forecast. Look at the bid strategy report and the budget simulator before each step.
- Campaigns that use a portfolio bid strategy take their target on the portfolio, not the campaign.
