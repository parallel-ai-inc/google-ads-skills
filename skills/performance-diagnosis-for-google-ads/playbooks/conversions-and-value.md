# Playbook: Conversions, leads or value fell

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: find whether fewer conversions or less value came from the traffic, the website, the tracking or the bidding, and in what order to check. It reads the summary from `scripts/compare.py`.

## When to use it

- A campaign under "Where the change is" has a main lever of conversion rate.
- Conversions, leads, Conv. value or Conv. value / cost fell, or lead quality got worse.
- For any other main lever, open `cost-and-delivery.md`: the traffic moved first.

## What to read in the output

The account table rows Conversions, Cost / conv., Conv. rate, and with values, Conv. value, Value / conv. and Conv. value / cost. For each campaign listed: the lever line, the traffic line ("Clicks: 172 before, 172 now (+0.0%)"), the value line, "Conversions per day" before and from the shift, and the changed lines.

## Split the drop first

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Main lever conversion rate, and the traffic line shows Impr. and Clicks each moved less than 20% | The clicks came. They converted less | Check in the order below: delay, tracking, website, searches, business, then bidding | Practitioner rule |
| Value / conv. held, Conv. value fell with conversions | A count problem, not a value problem | Treat it as a conversion drop | Practitioner rule |
| Value / conv. fell, conversions held | Mix or value tracking | Check which actions count, their values, value rules and the service mix | Practitioner rule |
| The account's Value / conv. fell, but each listed campaign's Value / conv. held | Mix between campaigns: fewer conversions where they are worth more | Name the campaign that lost conversions. Do not touch value settings | Practitioner rule |
| Conv. value / cost fell, Value / conv. and conversion rate held | Clicks got dearer | Open `cost-and-delivery.md` | Practitioner rule |

The 20% line is the script's own line for a campaign that moved.

## Which account change fits a conversion drop

| Change in the 3 days before | Conversion rate | Value / conv. | Label |
|---|---|---|---|
| Conversion action, goal, count or value changed | Strong: the Conversions column itself changed while clicks held | Strong | Practitioner rule. **Official** (references/learning-phase.md): goal and action changes need 1 to 2 conversion cycles |
| Landing page, final URL, form or site change | Strong | Medium, when the offer or price changed | Practitioner rule |
| Keywords added, or a looser match type | Medium: new searches can convert worse. Expect Impr. or cost per click to move too | Medium | Practitioner rule |
| Ads or assets edited | Medium: a new promise can bring clicks that convert worse | Weak | Practitioner rule |
| Location, schedule, audience or device settings | Medium | Medium | Practitioner rule |
| Bid strategy switched | Weak when Impr., Clicks and cost each moved less than 20%. Medium when one moved 20% or more | Weak, unless the switch was to value bidding | Practitioner rule. **Official** (references/learning-phase.md): a switch starts Learning |
| Target CPA or Target ROAS changed | Weak when traffic held, for the same reason | Weak | **Official** (references/learning-phase.md): bids react at once; a large change can bring short volatility when the campaign enters a new set of auctions |
| A new Target CPA below the campaign's Cost / conv. before, or a Target ROAS above its Conv. value / cost before (both printed) | A strict target shows as fewer Impr. and Clicks, not a lower conversion rate. Note it as a question for the bidding step, never as the cause while traffic held | | **Official** (references/troubleshooting.md): read Google's own recommendation on the target and lost impression share to rank before judging a target too strict |
| Budget changed | Weak | Weak | Practitioner rule |

Why bidding fits poorly: a strategy or target changes which auctions a campaign enters and what it pays, which shows first in Impr., Clicks and cost. When those held, put the bidding change last and call it a weak fit. Do not propose reversing it before the first check.

## What to check first, in order

1. **Delay.** A shift close to the last day of the report may be conversions still to come. **Official** (references/troubleshooting.md): conversions arrive up to 90 days after the click, and the bid strategy report marks the days where more are expected. Delay lowers the latest days most. When the shift day sits well before the last days and "Conversions per day" from the shift holds low across the whole period, delay does not explain it: say the latest days may still rise, and move to tracking. **Practitioner rule.**
2. **Tracking.** In Goals, Conversions, All conversions: each conversion action's Tracking status, and the change history for actions and goals. Confirm the Conversions column counts the outcome the person means. For a full check, use the conversion tracking skill in this pack.
3. **The website.** Submit the form or start the call yourself, on a phone and on a computer.
4. **The searches.** The Search terms report since the shift day.
5. **The business.** Price, stock, capacity, a competitor's offer.
6. **Bidding.** Only now the strategy or target change.

**Practitioner rule:** trace the outcome through what bidding uses: the action must be Primary and in a goal the campaign uses, and a custom goal can use Secondary actions. Bidding on conversion count does not become bidding on value because values are present.

**Lead quality.** The report cannot see who became a customer. **Practitioner rule:** compare leads of the same age, since recent leads have had less time to close, using the business's own records by lead date. Dividing two Google Ads totals does not give a customer rate.

## How big a change

- **Official** (references/troubleshooting.md): do not call the last few days a failure while they sit inside the conversion delay.
- **Official** (references/learning-phase.md): judge a goal, action or target change after 1 to 2 conversion cycles. Performance Max can take longer.
- **Official** (references/troubleshooting.md): after a tracking outage, apply a data exclusion as soon as it is found, covering the affected click dates plus the conversion delay and at least 90% of affected clicks. Never remove it, and wait at least 5 days before backfilling.
- **Official** (references/revenue-troubleshooting.md): since August 17, 2026, a budget limited Target CPA or Target ROAS campaign delivers toward its target; return falling toward the target is convergence, and Google says not to add data exclusions or bid limits for it.
- **Official** (references/revenue-troubleshooting.md): Smart Bidding ignores conversion adjustments made more than 7 days after the conversion.

## Failure modes

- **Targets changed, or the only change listed called the cause, before tracking is checked.**
- **Late conversions read as a drop.** Check the bid strategy report.
- **Mix read as value loss.** The account's Value / conv. fell, each campaign's held.
- **"Conversions" assumed to be leads.** The column can hold calls or page views. Ask.

## Worked example

Plumbing | Water Heaters: conversions -53.9%, cost -0.9%. The main lever is conversion rate, 12.48% before and 5.76% now, from around 2026-11-03. Clicks 172 before and now; Impr. +5.4%. Value / conv. held at 520.00. Changed on 2026-11-02: bid strategy from Maximize conversions to Target CPA, target 45.00. Traffic held, so the switch is a weak fit. The call: check the conversion action's status and test the form first, then the page and the searches, and leave the bid strategy last. The account's Value / conv. fell from 326.97 to 305.66 because this high value campaign lost conversions, not because values changed.

## What to tell the client

Water heater leads fell by 53.9% from around November 3, while clicks stayed exactly the same: the people came, fewer became leads. We are checking the water heater form and its tracking before touching the bidding change made the day before, which does not fit this pattern well.
