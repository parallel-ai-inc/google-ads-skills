# Playbook: Review bid strategies and decide what to change first

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: the bid strategy review a senior paid search person does by hand. Each campaign against its own target and the person's goal, whether the data can judge it, what holds it back, whether its strategy still fits, and the order of changes. It reads `bidding-review.md` from `scripts/review.py`, then the plan that `scripts/plan.py` checks.

## When to use it

- The person asks for a bid strategy review, a strategy review, or which campaigns to push or rein in.
- One campaign to scale, and how big a step: `scaling-a-campaign.md`. Learning or a recent change: `learning-and-recent-changes.md`. What to pause or tighten: `pause-tighten-or-investigate.md`.

## What to read in the output

- The header: the days left out of target comparisons, and "No conversion cycle was given, so 7 days was assumed" when it appears.
- "The short answer": each category with its share of the serving campaigns' cost.
- The Campaigns table: Target, Your goal, Actual, Gap to target, Gap to goal, Conv. read, Learning, Latest change, Limit, Category.
- Each campaign's section: the line ending "Chance alone moves a figure built on N conversions by about X%", "Lever", "Budget evidence", "Step size", "First fair check after a change", and every note.
- "Account": the lines "All campaigns" and "Without Brand", and "Check against the file's own Total".

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| "7 days was assumed" | Every hold, check date and left out day rests on a guess | Ask for the real conversion cycle and run the review again before writing dates into a plan | Practitioner rule |
| The Total check does not match | Rows are missing or the file was cut | Stop and say which figures differ before judging anything | Practitioner rule |
| Several categories at once | The plan needs an order | Step 1 in this order: pause candidates once tracking is confirmed, budget for scale candidates limited by budget, target changes, then investigations. Holds stay holds | Practitioner rule |
| "Hold: learning", "Hold: recent change", "Hold: too few conversions to judge" | No fair read yet | Plan "hold" with the printed date. `plan.py` refuses an edit without an override | Practitioner rule; Official 1 to 2 conversion cycles (references/smart-bidding.md) |
| "On target: hold steady" | The gap is within chance | No change. It is doing what its target asks | Practitioner rule |
| "Not judged on conversions" | Target impression share buys visibility | Leave it out of the comparison and the plan | Practitioner rule |
| "No target to judge against" | No target and no goal for it | Ask for the goal and run again with `--goal-cpa` or `--goal-roas` | Practitioner rule |
| A target looser than "Your goal", or "beats its own target but misses your goal" | The goal is the person's limit | Ask which rules before planning a change | Practitioner rule |
| "(top IS)" beside a Limit | Read from the top versions of lost impression share | Say "among top ads" whenever you quote it | Official (references/impression-share-and-editor.md) |
| "Moved the unexpected way" | A target change went the other way from what it should do | Name it. Within chance it is noise; beyond chance, check conversion values, the search mix and competition before the next change | Practitioner rule |

## Does the strategy still fit

The Account table shows cost and results by bid strategy. Check each strategy against what it needs:

- **Target ROAS** needs at least 15 conversions in the past 30 days on most campaign types, and conversion values that reflect the business. **Official** (`references/smart-bidding.md`). The review prints the count for every value campaign.
- **Enhanced CPC** is gone for Search and Display since March 31, 2025; such a campaign runs on Manual CPC. **Official** (same file).
- **Maximize conversions** with a goal and enough conversions: the lever "Add a Target CPA at the cost per conversion the business accepts" applies.
- **Thin conversion data**: Maximize conversions or Maximize conversion value builds signal before a target. **Practitioner rule** (`references/tcpa-framework.md`, `references/troas-framework.md`).
- **Conv. value / cost is not profit.** Ask for margin before calling a return good or bad.

## How big a change

- **One change per campaign per step.** `plan.py` refuses two. **Official** (`references/learning-phase.md`): avoid stacking edits inside one conversion cycle when you need a clean read.
- **A step starts when the checks of the step before are due.** The check waits for the longest of 2 conversion cycles, the days to 30 conversions (50 for Target ROAS) at the campaign's pace, and Google's window for Performance Max or Demand Gen. The review prints it as "First fair check after a change".
- **Step sizes** come from `scaling-a-campaign.md`. Never pick one by feel.

## Failure modes

- **Judging inside the conversion delay.** An "Early read" is a direction, never a verdict.
- **Calling a gap a result.** Only a gap wider than the printed chance figure counts.
- **Letting Brand set the average.** Use the "Without Brand" line for the account comparison.
- **A "why" with numbers the review does not hold.** `plan.py` refuses it. Quote the review.
- **Portfolio bid strategies.** A portfolio's target is set on the portfolio, not on the campaign row (`references/impression-share-and-editor.md`).

## Worked example

Northside Plumbing, goal 60.00 per conversion, cycle assumed at 7 days.

- Scale candidates: Plumbing | Emergency (50.02 against 60.00, Budget and rank (top IS)) and Plumbing | Water Heaters (5.12 against 4.00, Rank or target (top IS)).
- Missing its target: Sewer Line | Search, 81.99 against 55.00, a target already stricter than the goal.
- Pause candidate: Gas Line | Demand Gen, 820.22 with no conversion, 11.7 times its reference.
- Hold: learning: Drain Cleaning | Search, early read 69.02, proper read around 2026-12-01.
- The call: first ask for the real conversion cycle. Then step 1: pause Gas Line once tracking is confirmed, raise Emergency's budget within its first step, ask for a return floor before touching Water Heaters' target, investigate Sewer Line, hold Drain Cleaning.

## What to tell the client

"Emergency is your clearest chance to grow: it brings leads at 50.02 against your 60.00 and runs out of budget, so it gets more budget first, in steps. Gas Line has spent 820.22 without a single lead; once we confirm its tracking works, I would pause it. Sewer Line costs too much per lead, and its target is already strict, so the fix is in the searches and the landing page, not the target. Drain Cleaning just changed, so we leave it alone until early December."
