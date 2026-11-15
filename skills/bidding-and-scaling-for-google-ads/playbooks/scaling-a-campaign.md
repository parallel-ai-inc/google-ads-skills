# Playbook: Scale a campaign: budget or target, and how big a step

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: for a campaign the review calls a scale candidate, choose the least disruptive lever, size the step from printed evidence, and set the check and the roll back line. It covers Target CPA, Target ROAS and other value based campaigns. It reads each scale candidate's section in `bidding-review.md` and the notes `scripts/plan.py` writes for the step.

## When to use it

- The person asks how to scale a campaign, where there is room to grow, or how big a budget or target step to take.
- A campaign that misses its target: `pause-tighten-or-investigate.md`. A campaign just changed: `learning-and-recent-changes.md`.

## What to read in the output

- "Limit" and "Lever".
- "Budget evidence": "it spent X a day", "implies at most about Y a day more", "A first step of up to Z a day" and "Google may bill up to ... in a month".
- "Step size": for a target, and when a goal applies, "Your goal of G is the furthest a looser target may go. Halfway from today's target to your goal is H", or "Its target is already at your goal".
- "Fragile: the later half of the read period ...", and the August 17, 2026 note.
- From `plan.py`: "This step adds ... a day", "So plan for spend near ... a day", and every warning.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Limit "Budget", "Budget and rank" or "Rank and budget" | Budget binds | Raise the budget first. Keep the target as it is in that step | Practitioner rule |
| Budget limited Target CPA or Target ROAS | Since August 17, 2026 it bids toward its target rather than beating it | Say added budget buys conversions at about the target. Set the target the business wants before adding budget | Official (references/smart-bidding.md) |
| Target equal to the goal, and budget limited | Added budget will land near the goal, and the roll back line is the goal itself | Say the margin is gone. Ask whether to tighten the target first or accept results near the goal | Practitioner rule |
| "Budget, by design" | Maximize conversions or Maximize conversion value | Size the budget with the budget simulator, not lost impression share | Official (references/smart-bidding.md) |
| Limit "Rank or target", Lever "A looser target" | Bids, not budget, hold it back | Loosen the target toward the goal, never past it | Official for the mechanics (references/smart-bidding.md) |
| Limit "Neither: demand or reach" | More budget or a looser target buys little | Widen reach instead: AI Max search term matching or broad match where tracking is stable; Smart Bidding Exploration only on Search with Target ROAS | Practitioner rule (references/scaling.md); Official for Exploration's scope (references/smart-bidding.md) |
| "Fragile" | The later half misses its reference by more than chance | No scale step until the later half is explained | Practitioner rule |
| Target ROAS, below 15 conversions in 30 days, or values in doubt | Value bidding needs volume and trustworthy values | Fix the value signal before scaling | Official (references/smart-bidding.md) |
| No goal given for a target you would loosen | Nothing limits how far it may go | Ask for the floor or ceiling. Without one, plan no loosening | Practitioner rule |

## How big a step

**Budget.**

- **The first step is at most the printed "A first step of up to Z a day".** That is half the room lost impression share to budget implies. **Practitioner rule:** we cover the room in at least two steps and read each before the next. `plan.py` warns above it.
- **Never above the room.** It is an upper bound at today's cost per click, and the top version overstates it. `plan.py` warns above it.
- **Never above what the business said it can add.** Use the smaller figure. Confirm the new monthly bill `plan.py` prints, 30.4 times the daily budget (**Official**, `references/scaling.md`).
- **The second step** follows only once the first step's check is due, within the room left, which `plan.py` prints.

**Target.**

- **The step's percent is the spend change to plan for.** **Official** (`references/smart-bidding.md`): on Search and Shopping a target change moves bids at once, does not start learning, and a large move changes spend or volume by a similar amount. `plan.py` turns it into "plan for spend near ... a day". Size the step so that figure fits what the business can spend.
- **With a goal looser than the target, the first step is the printed halfway figure, the second is the goal.** **Practitioner rule:** two steps, each read before the next.
- **At the goal, no loosening** without the person's word.
- **Demand Gen: 5 to 10% a week, no more than 15%.** **Official** (`references/learning-phase.md`). `plan.py` refuses more.
- **Performance Max:** judge a change after 1 to 2 weeks or one conversion cycle (**Official**, `references/learning-phase.md`).

## Failure modes

- **Sizing by feel.** A round 25% is not evidence. Quote the first step or the halfway figure.
- **Loosening the target of a budget limited campaign.** Each conversion costs more with no more budget to spend. `plan.py` warns.
- **Budget and target in one step.** The result cannot be read. One change per step.
- **Reading reported return as profit.** Conv. value / cost is not margin. Ask for the return the business needs.
- **Scaling on aggregate return into weak segments.** **Practitioner rule:** tie each step to what the last one bought, not to the campaign average.

## Worked example

Northside Plumbing, goal 60.00 per conversion.

- Plumbing | Emergency: Budget and rank (top IS). It spent 231.90 a day against 240.00; room at most 103.79 a day, overstated by the top read; first step up to 51.90 a day. Its target equals the goal, so results will drift toward 60.00 and the roll back line is 60.00.
- The call: 240.00 to 280.00, adding 40.00 a day (+16.7%), inside the first step. Google may bill up to 8,512.00 a month. Check after about 14 days and 30 conversions. A raise to 300.00 (+25%) would draw the warning that it adds more than half the room.
- Plumbing | Water Heaters: Rank or target (top IS), 5.12 against 4.00. The sample gave no return goal, so its plan lowers the target to 3.60 (-10.0%), with spend near 126.52 a day against 115.02. Had the person set a floor of 4.00, the target is already at it: no loosening, and the rank loss gets investigated instead.

## What to tell the client

"Emergency brings leads below your 60.00 and runs out of budget, so I would add 40.00 a day now and look again in about two weeks before adding more. Expect its cost per lead to rise toward 60.00: Google now bids up to the target when budget is the limit. Water Heaters is held back by its bids, not its budget, so the only way to grow it is to accept a lower return, and that is your call."
