# Playbook: Yesterday, the last two weeks, anything unusual, and the write up after

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: give a fast, trustworthy read of a recent period, separate what is routine from what needs a check today, and write up an incident once its cause is known. It reads the summary that `scripts/compare.py` prints for the period chosen with `--days`.

## When to use it

- "How did yesterday go?", "How were the last two weeks?", "Is anything unusual?"
- A post mortem: a write up after something went wrong.
- For each campaign the run lists, open the lever playbook too: `cost-and-delivery.md` for cost per click, how often ads showed or click through rate, and `conversions-and-value.md` for conversion rate or value.

## Pick the periods

| The question | Run | What it compares |
|---|---|---|
| Yesterday | `--days 1`, then `--days 7` | Yesterday against the day before, then the last 7 days against the 7 before, which hold the same weekdays |
| The last two weeks | `--days 14` | The last 14 days against the 14 before. The report needs at least 28 days |
| Anything unusual | `--days 10`, the default | The last 10 days against the 10 before |
| A write up | `--current` and `--previous` with the incident's dates | The days of the incident against the same number of days before it |

The script refuses a report that does not cover the earlier period, and says which day it starts. A one day run has too few days for a shift day, so none is printed.

## What to read in the output

- The first line under the title: "Now: ... Before: ... Each period is N days."
- The account table, and "Where the change is", with each campaign's lever, traffic line, value line, status line, shift day and changes.
- "Steady, within 20%".
- "What this did not cover".

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| "No campaign moved 20% or more" | Routine | Say so in one line. Name nothing as a problem | Practitioner rule |
| A campaign listed on a one day run only | An early read. One day is noisy at small volume | Run `--days 7`. Act only when the 7 day run lists the same campaign with the same lever | Practitioner rule |
| A campaign listed with a change before the shift that fits its lever | Needs a check today | Lead with it. Give the first check from the lever playbook | Practitioner rule |
| Cost per click or cost up, conversions not up with it | Money is going out now | Needs a check today | Practitioner rule |
| Conversion rate down with clicks within 20% | A possible tracking break that bidding is learning from | Needs a check today, tracking first | Practitioner rule |
| A conversion drop whose shift starts in the last days of the report | May be late conversions | Watch. Check the bid strategy report before calling it | **Official** (references/troubleshooting.md): conversions arrive up to 90 days after the click |
| A campaign listed whose status line reads Paused or Removed | Not a performance problem | Ask whether the pause was intended | Practitioner rule |
| Steady, within 20% | Not where the change is | Say it. It narrows the search | Practitioner rule |

End every routine read with three short parts: what looks routine, what needs a check today, and what to watch.

## The write up after an incident

Use these headings. Every number comes from the summary.

1. **What happened.** The campaign, the lever before and now, the shift day ("around"), and the account's change, from the account table.
2. **Impact.** "That is X in cost, against Y for the whole account", or the conversions version of that line. Use these totals. Never multiply a daily figure by a number of days.
3. **Trigger and root cause.** The trigger is what moved first: often the change listed before the shift. The root cause is what let it happen or go unnoticed: a change made without a check, a tracking test that was never done, an alert nobody owned. Keep the two apart.
4. **Detection.** The shift day and the day the person noticed, side by side. Ask for the second if it was not given.
5. **Corrective action.** What was done or is proposed, with its owner and its waiting period from the lever playbook.
6. **Prevention.** One step per root cause, with an owner.

**Practitioner rules for the write up:** take each claim from the source that owns it. The change history shows an edit and its date, not the setting today. The business owns the offer, the price and the stock. Google's pages own how the platform works. Call a proposal a proposal until someone has made it and checked it. A budget alert or a saved script is not protection until it has run and someone received its notice: say which.

## How big a change

A routine read changes nothing. Waiting periods come from the lever playbooks. **Official** (references/learning-phase.md): judge a bid strategy or target change after 1 to 2 conversion cycles; Performance Max asks for 1 to 2 weeks or one conversion cycle after a significant change, and at least 6 weeks for a new campaign.

## Failure modes

- **A one day swing treated as a trend.** It shows on `--days 1` only. Run `--days 7`.
- **Yesterday's conversions read as final.** They keep filling in. Say so.
- **A weekly pattern read as a change.** Use periods of whole weeks: `--days 7` or `--days 14`.
- **A late starting report.** The script refuses a report that does not cover the earlier period; download a longer range rather than shortening the comparison.
- **A post mortem that names only the trigger.** Ask why the change went in unchecked, or why nobody saw the shift for days.

## Worked example

On the sample account, the default 10 day run lists two campaigns and calls Brand and Plumbing | Emergency steady. Needs a check today: Drain Cleaning | Search, cost +80.7% with cost per click from 5.24 to 7.54 from around 2026-11-05, and Plumbing | Water Heaters, conversions -53.9% with clicks at 172 in both periods from around 2026-11-03. Watch: nothing else. A write up for Water Heaters would give "-11.56 conversions, against -2.32 for the whole account" as the impact, the 2026-11-02 bid strategy change as a weak fit, and the open question as tracking.

## What to tell the client

Most of the account was steady. Two campaigns need a look today: Drain Cleaning, where clicks got dearer after new broad match keywords, and Water Heaters, where the same number of clicks brought fewer than half the leads. We will check both before changing anything.
