# Playbook: Launch or clone a Performance Max campaign

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

Whether to launch or copy now or fix first, and what the new campaign needs before it goes live. It reads `pmax-launch-checklist.md` from `scripts/launch_checklist.py`, and the review it was built from.

## When to use it

The person wants a new Performance Max campaign, or a copy of one for a product line, a region or a service. Run the review first (`playbooks/review-and-waste.md`): the checklist takes its numbers from it.

## What to read in the output

- **Go or no go,** and every reason under "Fix these before cloning".
- The notes on what the clone copies: "Asset groups taken as copied", "Product groups taken as copied", or "copies every asset group".
- **Section 3:** bid strategy, budget, "it pays for N conversions a day", and the source's average daily spend.
- **Section 5:** the brand line and the words "Held back, never to be added as negatives here".
- **Section 6:** the dated checks.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| "Go or no go: go" | Nothing copied is the weakest by the goal, rated below Good, or still learning | Build it paused, work through sections 1 to 5, enable on the start date | Practitioner rule |
| Fix first: the source "is still learning" | The source's numbers are early, so the copy's plan rests on them | Wait until the source's Status leaves Learning, then run the review and checklist again | Official (references/pmax.md) |
| Fix first: a copied asset group "is rated Average" or "Poor" | The copy starts with thin assets | Add assets to the source group first, within `references/creative.md` limits, then copy | Official (references/creative.md) |
| Fix first: a copied asset group "is the weakest" or "spent ... with no conversions" | The copy carries the source's worst performer | Leave that group out, or find its cause first in the review | Practitioner rule |
| Fix first: a copied product group "is the weakest" | The products themselves do not sell at this price or with this data | Price and feed first (`playbooks/products-feed-and-price.md`). A new campaign does not fix price | Practitioner rule |
| The person wants a copy to give weak products their own budget | That spends more on what already fails | Clone only when the new campaign needs a different goal, target, budget the business wants protected, or control. Otherwise fix inside the source | Practitioner rule |
| The new campaign's goal differs from the source's (leads against sales) | The source's numbers do not transfer | Set its target from campaigns that share its goal; the checklist says so when goals are mixed | Practitioner rule |
| Section 3: "it pays for" under 1.00 conversion a day | The budget buys less than one conversion a day at the source's cost per conversion | Say so plainly: the 6 week read will rest on few conversions. Let the person choose the budget | Practitioner rule |
| Held back words in section 5 | They name what the new campaign sells | Never add them as negatives, even if they wasted money elsewhere | Practitioner rule |
| The brand line in section 5 | Brand searches carry part of the source's conversions | Decide brand ownership with the review playbook before launch, not after | Practitioner rule |
| Audience signals planned from saved segments | A segment's name does not define its logic | Read each segment's type, AND or OR logic and members. A website address seed means people with similar browsing, not known visitors. Uploaded customer rows are not matched members | Practitioner rule |
| New customers only is the aim | Audience signals are suggestions, not targeting | Use the new customer acquisition goal | Official (references/pmax.md) |
| A retail campaign | It depends on Merchant Center | Confirm the link and product issues first. Merchant Center campaigns generate the minimum assets automatically | Official (references/feeds.md, references/creative.md) |
| The campaign is saved with every section ticked | A saved structure is not a working ad journey | Before calling it ready, check creative coverage, policy review, the landing page, the offer and that the business can deliver it. Name each missing piece separately | Practitioner rule |

## How big a change

- **Run time.** At least 6 weeks before a full judgment, with 1 to 2 weeks or one conversion cycle after any significant change. Official (references/pmax.md). The checklist prints the dates: serving checks on days 1 to 3, a first read on day 14, the earliest full judgment on day 42.
- **Early changes.** Avoid frequent budget, bid strategy or status changes in the first weeks. Official (references/pmax.md).
- **Budget.** No source sets a minimum. The bound is the printed "conversions a day" and the source's average daily spend beside it.
- **Assets.** Up to 15 headlines, 5 long headlines, 5 descriptions, 20 of each image shape and 15 videos per asset group, with the minimums in `references/creative.md`. Google recommends Good or Excellent Ad strength and every asset type in every group. Official (references/creative.md).

## Failure modes

- **A clone of the weakest group.** Shows as "fix first" ignored. Check the go line before anything else.
- **A negative that blocks the new campaign's own products.** Check the held back words.
- **Brand left to chance.** Two campaigns serve brand searches with no decision. Check the brand line.
- **Launch ready claimed from structure.** Assets missing, policy review pending or the page not matching the offer. Check each separately.
- **Judged in week two.** Check the dated steps in section 6.
- **A lead clone set from a retail source's numbers.** Check Judged by in the review.

## Worked example

Northside Plumbing wants PMax | Drain Tools, cloned from PMax | Plumbing Supplies. The checklist says **fix first**: the Drain Tools asset group is rated Average, with 2,100.00 cost and 0.10 conv. value / cost against 3.79 for the campaign, and product group Drain Tools is the weakest of 5, 0.01 against 4.29 for all products. A daily budget of 60.00 pays for 0.66 conversions a day at 90.87. "drain" and "snake" are held back. The call: do not clone yet. Settle the drain tool prices and fill the Drain Tools assets, run the review again, and clone only if the business wants drain tools on their own budget. If it launches on 2026-11-20, the first read is 2026-12-03 and the earliest judgment 2026-12-31.

## What to tell the client

I would not copy the campaign for drain tools yet. The drain tool products and their ads are the weakest part of the current campaign, and a copy would start with the same problems. Once their prices and ads are fixed, a separate campaign makes sense if you want drain tools on a budget of their own. Whenever it launches, give it six weeks before judging it.
