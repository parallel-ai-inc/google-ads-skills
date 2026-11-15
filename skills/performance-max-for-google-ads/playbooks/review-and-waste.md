# Playbook: Performance Max review and waste audit

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

What Performance Max buys, whether each campaign meets its own goal, and where money goes without return. It reads `pmax-review.md` and the FOR YOUR JUDGMENT block that `scripts/audit.py` prints.

## When to use it

Auditing Performance Max, finding waste, or "is it just brand". Products, feed and prices: `playbooks/products-feed-and-price.md`. A launch or a copy: `playbooks/launch-or-clone.md`.

## What to read in the output

Evidence check; Campaigns (Status, Judged by, Target, Against target); Channels by campaign with Status; Asset groups (Ad strength, each campaign's line); Searches (Brand and Non brand rows, the non brand searches with no conversions, the "Held back" line); Findings and the judgment block's "Actions allowed".

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| An Evidence check difference other than 0.00, or a report covering only part of the campaign cost | Different campaigns or dates, or rows Google leaves out | Resolve it before any cut. Give every share with its base ("of the listed search cost") | Practitioner rule |
| Status shows Learning | The numbers are early | No fix on that campaign or its asset groups. Every action on it is kind investigate | Official (references/pmax.md) |
| Judged by shows "cost / conv." on one campaign and "conv. value / cost" on another | A lead campaign beside a retail one | Judge each on its own Against target. Never rank them on one number or quote a blended cost per conversion | Practitioner rule |
| Against target: "no target given" | Nothing to judge efficiency against | Ask for the target once. Meanwhile compare only inside the campaign: its asset groups and channels against its own number | Practitioner rule |
| Against target: "worse than target by" | Below the business's goal | Lead campaign: confirm what a conversion is (call, form, qualified lead), then asset groups past the line, channel status, searches. Retail campaign: products and listing groups before bids | Practitioner rule |
| The Brand row's share of listed conversions is above its share of listed cost | Brand flatters the blend | Judge Performance Max on the Non brand row. The search line already leaves brand out | Practitioner rule |
| The brand finding names a Search campaign whose brand keyword is phrase or broad | Only an exact match keyword identical to the search is preferred over Performance Max, and a budget limited Search campaign lets it serve on exact terms | Investigate: an exact match brand keyword in that Search campaign, and its budget. Only then brand exclusions | Official (references/pmax.md) |
| Brand searches, and no Search campaign carries the brand | Performance Max is the brand coverage | Never exclude brand without a Search campaign to take it | Practitioner rule |
| The business wants Search to own brand | | Brand exclusions, not negatives. A retail campaign can leave Shopping serving | Official (references/pmax.md) |
| A non brand search with no conversions that names what the account sells | A buyer who did not buy | No negative. Look at price, feed and landing page | Practitioner rule |
| A search the business can never convert (job seekers, "free"), whatever it cost | Irrelevant traffic | List it under negatives in actions.json, copied exactly | Official (references/pmax.md) |
| A search with "jobs", "careers", "hiring" or "salary", even beside a service word ("water heater repair jobs") | A job seeker, unless the business recruits through its ads | A negative. Ask first only if the business is hiring | Practitioner rule |
| A "diy", "how to" or "install it yourself" search | Depends on what the campaign sells: a shop sells the tools for the job, a lead campaign sells the job done for them | Shop campaign: no negative, judge it like any product search. Lead campaign: a negative candidate, tested like a held back word | Practitioner rule |
| "Holds a word that never converted", or a word in the "Held back" line | A candidate only; a held back word names what the account sells | Test a candidate after checking every search that holds it. Never a negative from a held back word | Practitioner rule |
| A channel question | Performance Max buys for marginal return, so a channel average can mislead | Investigate only: Status column and the assets that channel uses | Official (references/pmax.md) |
| A channel with no cost and no listed issue | Most likely the campaign favours channels with a higher return | Nothing to fix | Official (references/channel-and-price-reports.md) |
| Channel Status "Eligible (Limited)" or "Missing required assets" | A setup gap | Check that format's assets | Official (references/channel-and-price-reports.md) |
| An asset group rated Average or Poor carries spend | Thin asset coverage, not an auction penalty | Add assets within `references/creative.md` limits | Official (references/creative.md) |
| An asset group spent past its line with no conversions | Not working, or there on purpose | Ask whether it is deliberate. Check products, assets and final URL before pausing | Practitioner rule |

## How big a change

- **Waiting.** A new campaign runs at least 6 weeks. After a significant change allow 1 to 2 weeks or one conversion cycle (up to 6 weeks for lead generation). Official (references/pmax.md).
- **Date range.** Only about half of Performance Max conversions land inside the 30 day click and 3 day engaged view windows, so a recent window understates results. Official (references/pmax.md). A small gap in Against target over a short window is not a verdict.
- **Target changes.** No source gives a step size. It is a judgment bounded by the printed gap, the Status column and the days the reports cover. Change one thing at a time.
- **Negatives.** One exact match negative per judged search; at most 10,000 per campaign and 1,000 at account level; no close variants. Official (references/pmax.md).
- **Assets.** 2 to 3 weeks before replacing low performers. Official (references/creative.md).
- **Mixed goals.** If conversions mix actions of different worth, fix goals or values before scaling anything. Practitioner rule.

## Failure modes

- **Brand called waste.** Check for a business answer and a Search campaign to take brand over.
- **Lead and retail ranked together.** Every efficiency claim names its campaign and its Judged by.
- **A channel cut on averages.** The script refuses a fix on a channel finding.
- **A negative that blocks the account's own products.** Check the Held back line.
- **A learning or paused campaign judged.** Check Status and "paused, not judged".
- **Settings the exports cannot show.** Search themes, audience signals and exclusions are not in these files. Say what would show them.

## Worked example

Northside Plumbing. PMax | Plumbing Supplies is judged by conv. value / cost: 3.79 against a target of 4.00, "worse than target by 5.3%". PMax | Water Heater Leads is judged by cost / conv., 171.43, "no target given", and is learning: no verdict, ask for the target. Brand is 16.4% of listed search cost and 48.4% of listed conversions, and the Brand Search campaign carries "northside plumbing" in phrase match, so the first step is an exact match brand keyword there. Of 11 non brand searches with no conversions (1,155.00), four job seeker and "free" searches (335.00) become negatives. "drain snake 25 ft" (260.00) and "toilet auger" (190.00) stay, because the account sells both. Display in Plumbing Supplies returns 0.95 against 3.79 for the campaign: a question, not a cut.

## What to tell the client

Performance Max is not mainly buying your brand, but brand searches bring in a large part of its conversions, so I judged it on everything else. Your shop campaign is 5.3% below its return target; the lead campaign is still learning, so I have not judged it. The clearest waste is a few job seeker searches, listed to block. What is your target cost per lead, and should brand searches stay in Performance Max?
