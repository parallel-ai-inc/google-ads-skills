# Playbook: Devices, audiences, locations and ad schedule

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

Whether a device, an audience segment, a place or a time of day costs more than it should, and which lever can act on it under the campaign's bid strategy. It reads the DEVICES, AUDIENCES, LOCATIONS and AD SCHEDULE sections that `scripts/review.py` prints. All four splits work the same way, so one playbook covers them.

## When to use it

- "Should I bid down mobile", "is Sunday worth it", "are we wasting money in that town", "which audiences work".
- The review judges each split twice: against the account, and inside each campaign against that campaign's own baseline. Decisions are made at the inside campaigns level.
- Placements on the Display Network and YouTube are in `placements-and-video.md`.

## What to read in the output

- "Baseline, all ... judged" and "Enough to judge: ... spent".
- "Account level" and "Inside campaigns" lines for Wasted and Less efficient. Never add the two levels, and never add across splits: one click has a device, an hour and a place.
- The table "... inside campaigns, judged against their own campaign", with Verdict, "Compared with" (the campaign and its cost per conversion), and **What can act on it**, which names the bid strategy and the levers it supports.
- "Worth watching" tables.
- Devices: the "Mix" line, each device's share of cost and of conversions, with its base.
- Audiences: the Targeting setting column when the file has it, and the line that segments overlap.
- Ad schedule: the day of the week and hour of day splits, and "The same spend is in each split".
- FILES READ: "Bid strategy by campaign".

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| A segment judged at account level only | It spans campaigns with different strategies | Act campaign by campaign, from the inside campaigns table | Practitioner rule (references/bid-adjustments.md) |
| Worse inside a Manual CPC campaign | A bid adjustment can act on it | Device -100% to +900%; location, ad schedule and audience -90% to +900% | Official (references/bid-adjustments.md) |
| Worse or No conversions on a device inside a Smart Bidding campaign | Only -100% acts on it, or a device target adjustment under Target CPA | Stop the device only when the business does not want it. Smart Bidding already uses device as a signal, so the finding may need no action | Official (references/bid-adjustments.md) |
| A location, hour or audience Worse inside a Smart Bidding campaign | No bid adjustment is supported | Use an exclusion, the ad schedule itself or the targeting setting, or leave it to the strategy | Official (references/bid-adjustments.md) |
| A location with No conversions | Spend in a place that books nothing | Ask whether the business serves it. If not, exclude it; an exclusion works whatever the bid strategy | Practitioner rule (references/bid-adjustments.md) |
| A day Worse in every campaign | Something about that day, not the bids | Ask whether the business answers calls and forms that day before changing the schedule | Practitioner rule |
| An ad schedule bid adjustment wanted | It needs a custom ad schedule first | Set the schedule, then the adjustment | Official (references/bid-adjustments.md) |
| An audience Worse under Observation | It does not limit reach | Manual CPC: an audience bid adjustment, or exclude the segment | Official (references/bid-adjustments.md: Targeting and Observation) |
| An audience with No conversions under Targeting | The campaign is limited to it | Check the Targeting setting before excluding; it may be the campaign's whole audience | Official (references/bid-adjustments.md) |
| Hours or places with "Too little data" | Not enough spend to judge | Leave them. Do not trim the schedule from them | Practitioner rule |
| Device Mix: a device's share of cost well above its share of conversions | The same story as a Worse verdict, shown as shares | Use the verdict, not the mix, to decide | Practitioner rule |

## How big a change

- **Ranges.** Device -100% to +900%. Location, ad schedule and audience -90% to +900%. Official (references/bid-adjustments.md).
- **Stacking.** Several adjustments on one auction are multiplied together. Combined they cannot raise a bid by more than 900%, and the lowest combined adjustment is -90%. Official (references/bid-adjustments.md). Check the campaign's existing adjustments before adding one.
- **Size of a single adjustment.** No source gives one. It is a judgment. The evidence that bounds it is the row's "Cost / conv. vs it" and "Conv. rate vs it": a cut larger than the gap overshoots it. Say it is a judgment.
- **One or two changes a week**, the clearest first. Practitioner rule (references/daily-optimization.md).

## Failure modes

- **An account level bid change.** There is none. Act inside the campaign.
- **A bid adjustment the strategy ignores.** Check What can act on it. Never recommend one it says is not supported.
- **Adding the money of two splits.** The same click is in each. Quote each split on its own.
- **Excluding a place the business serves.** Ask first; a slow town can still be a market.
- **Audience rows added up.** One person sits in several segments, so rows share clicks.
- **Cutting a day that books calls the export does not count.** If phone calls are not tracked, a quiet day can look like waste.

## Worked example

Northside Plumbing, reports 2026-10-14 to 2026-11-12.

- Devices: inside Plumbing | Emergency (Manual CPC), Computers cost 225.00 per conversion against the campaign's 98.78, Worse, 1,262.20 less efficient. What can act on it: a device bid adjustment. Call: a computer bid decrease in that campaign only, sized as a judgment within the +128% gap.
- Inside Plumbing | Water Heaters (Maximize Conversions), Tablets spent 350.00 with no conversions. Only -100% acts on it.
- Locations: Gary, Indiana spent 1,000.00 with no conversions (620.00 in Emergency, 380.00 in Water Heaters). Ask whether Northside serves Gary; exclude it if not.
- Ad schedule: Sunday is Worse in all three search campaigns. In Emergency (Manual CPC) a schedule bid adjustment can act; in Water Heaters and Drain Cleaning | Search only the schedule itself can. Ask first whether Sunday calls are answered.
- Audiences: Home Improvement is Worse inside Emergency (500.00 per conversion against 98.00) and spent 760.00 with no conversions inside Water Heaters. Check its Targeting setting in both.

## What to tell the client

"Phones bring your leads most cheaply. In the Emergency campaign, a lead from a desktop computer costs 225.00 against 98.78 for the campaign, so I would lower desktop bids there. Gary, Indiana took 1,000.00 with no leads; if you do not serve Gary, I will exclude it. Sundays convert poorly in every campaign, so before changing the schedule I want to check whether Sunday calls are being answered."
