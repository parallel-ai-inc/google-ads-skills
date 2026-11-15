# Playbook: Pause, tighten or investigate a campaign that misses

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: find the clearest waste without over pruning, and for each weak campaign choose between pausing it, tightening its target, or investigating before any change. It reads the "Pause candidate" and "Missing its target" sections of `bidding-review.md`, and the warnings `scripts/plan.py` writes.

## When to use it

- The person asks what to pause, what to cut, what to rein in, or why a campaign misses its target.
- A campaign beating its target: `scaling-a-campaign.md`. A campaign just changed or learning: `learning-and-recent-changes.md`.

## What to read in the output

- Pause candidates: "Spent X with no conversion between ... : N times the reference cost per conversion of Y, where the test needs 3", "Which wins here", and "Confirm first that conversions are being recorded".
- Missing its target: "worse than it", the chance figure, "Against your goal of", the Lever, and "Its target of X is stricter (or looser) than your goal of G".
- The Limit, and "Latest changes read".

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| "Pause candidate" | No conversion after spending 3 times the reference cost per conversion. If it converted at that cost, a run of zero this long happens about 5% of the time | Confirm tracking first: its conversion actions record conversions in other campaigns over the same days, and its goals include them. Then pause. If tracking is broken, fix tracking instead | The review's test; Practitioner rule for the order |
| "Which wins here: the case for pausing" on a new Demand Gen campaign | Google asks for no changes in the learning period, but there is nothing to learn from | Pause once tracking is confirmed | Practitioner rule, as printed |
| "Missing its target", target looser than the goal | The target allows more than the business accepts | After the checks in the Lever, bring the target to the goal in one move | Practitioner rule (references/tcpa-framework.md) |
| "Missing its target", target at or stricter than the goal | Tightening again is unlikely to help on its own | Plan "investigate": search terms, conversion rate and the landing page. No target change | Practitioner rule (references/tcpa-framework.md, references/troas-framework.md) |
| "Missing its target" on Target ROAS | Return below target | Check value tracking, search terms and pricing first | Practitioner rule (references/troas-framework.md) |
| "Missing its target" on Maximize conversions or Maximize conversion value | No target to tighten | Add a target at the cost per conversion or return the business accepts | Practitioner rule, as the Lever prints |
| "On target: hold steady" or any "Hold" | Within chance, or not yet judgeable | Neither pause nor tighten | Practitioner rule |

**Pause or tighten.** A campaign with no conversions past the test is a pause case. A campaign that converts, but too expensively, is a tighten or investigate case. **Practitioner rule:** start with the clearest waste, not the borderline cases.

## How big a change

- **Tightening to the goal is one move.** **Official** (`references/smart-bidding.md`): on Search and Shopping a target change moves bids at once without starting learning, and a large move changes spend or volume by a similar amount. Say the volume will fall by about the share the target tightens. If the business cannot take that drop at once, use two steps, each read before the next. **Practitioner rule.**
- **Demand Gen tightens in weekly steps** of 5 to 10%, never more than 15%. **Official** (`references/learning-phase.md`). `plan.py` refuses more.
- **A pause is checked the next day**, then the other campaigns' conversions are watched for a conversion cycle, as `plan.py` prints.
- **The roll back line** is printed for every target step, and never looser than the goal.

## Failure modes

- **Pausing on broken tracking.** Zero conversions everywhere on the same days points to tracking, not the campaign.
- **Tightening a strict target again and again.** The Lever says when the target is already at or stricter than the goal. `plan.py` warns.
- **Loosening a target that already misses.** `plan.py` warns.
- **Judging Brand on cost per conversion.** Target impression share is "Not judged on conversions".
- **Blaming the target for a market change.** A change in search demand, competition or prices can move results with no account change.

## Worked example

Northside Plumbing, goal 60.00 per conversion.

- Gas Line | Demand Gen: 820.22 with no conversion between 2026-10-14 and 2026-11-05, 11.7 times its reference of 70.00. Created 30 days before the report's last day; the review says the case for pausing wins once tracking is confirmed. Its target of 70.00 is also looser than the goal. The call: confirm tracking, then pause.
- Sewer Line | Search: 81.99 against 55.00, 49.1% worse, beyond the 11.7% chance explains, and 36.7% worse than the goal. Its target is already stricter than the goal; the only change read is 6 keywords added on 2026-09-22. The call: investigate the search terms those keywords brought, the conversion rate and the landing page. No target change.

## What to tell the client

"Gas Line has spent 820.22 in three weeks without a single lead. Before pausing it I will make sure its lead tracking works, because a tracking fault would look the same. Sewer Line does bring leads, but at 81.99 each against your 60.00, and its target is already strict, so lowering the target further will not fix it. The cause is more likely the searches it shows on or the page people land on, and that is where I would look first."
