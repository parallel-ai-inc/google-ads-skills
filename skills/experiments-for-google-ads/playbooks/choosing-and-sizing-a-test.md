# Playbook: Choose a test design and size it

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-14.

The job: turn "does this work?" into a test that can answer it, or say plainly that none can at this volume. The script sizes; you choose the design and explain it. It reads the summary `scripts/design.py` prints.

## When to use it

- The person wants to test a change, asks whether the ads are incremental, whether brand is worth paying for, or whether more budget would add more.
- A test has run and needs reading: `reading-a-test-result.md`. Whether campaigns make money now: `return-on-investment.md`.

## First, name the question

| The question | What answers it | Label |
|---|---|---|
| What might happen at another budget | A forecast, such as Performance Planner. Scenario guidance, not proof of lift | Official (references/experiments-and-planning.md) |
| How credit was shared between campaigns | Attribution reports | Official (references/attribution.md) |
| Which of two setups of one campaign does better | A custom experiment, read from Google's report | Official (references/experiments-and-planning.md) |
| What the ads caused that would not have happened anyway | A geo test, an on and off test or a lift study | Official (references/incrementality.md) |

Say which it is in the reply. Only the last two are tests.

## What to read in the output

- "The answer": "Readable" or "Too little volume", the days needed for the lift asked, and the smallest lift it can detect at the longest plan (56 days unless `--max-days` says otherwise).
- "The outcome, day by day": average, spread, the weekday pattern and its p value, and for a geo test the fit against the control regions (R squared).
- "What lift it can detect": the smallest lift at 14, 21, 28, 42 and 56 days.
- "The plan": start, days left out at the start, reading dates, stop, the pre-period, "Stays fixed", the decision rule and the weekly checks.
- "Eligibility for a custom experiment" and "Lift studies run by Google".

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| One change inside one campaign, and the campaign is Search, Display, Demand Gen or Video, active, on its own daily budget and a standard bid strategy | Eligible for a custom experiment | Design `experiment`. Ask the person to confirm the bid strategy is not a portfolio | Official (references/experiments-and-planning.md) |
| App or Shopping, a shared budget or a portfolio strategy | No custom experiment | Geo test, or on and off | Official (references/experiments-and-planning.md) |
| "Are the ads incremental?" or "is brand worth it?", and the business counts leads or sales by region | A causal question with a regional outcome | Geo test, go dark or holdback | Practitioner rule |
| The same question, no regional count | No geo outcome | On and off by whole weeks, on the business's own count | Practitioner rule |
| "Would more budget add more?" | A heavy up question | Geo test, heavy up | Practitioner rule |
| The person gave no lift | Nothing to size against | Read "What lift it can detect" to them and ask whether a change that size would change their decision | Practitioner rule |
| "Readable" | The lift asked can be seen in the planned days | Write the plan as printed | Practitioner rule |
| "Too little volume" | The lift asked needs longer than the longest plan | Offer, in order: a larger lift if the decision only needs that; a higher volume outcome (all leads rather than one action, or more regions); or no test. Never stretch the plan past what the business can hold still | Practitioner rule |
| The smallest lift at 56 days is larger than the change could bring | The test cannot answer the question | Recommend no test, and say what would let one answer | Practitioner rule |
| "Over the run ... below the 1,000 conversion floor" | User based Conversion Lift is out of reach | Do not offer it | Official (references/incrementality.md) |
| The outcome is Google Ads' Conversions in a go dark or on and off test | It stops when the ads stop | Use the business's own count instead | Practitioner rule |

## How big a change

- **Length:** the planned days, rounded to whole weeks, no longer than 56 days by default (`--max-days`). The script's choice.
- **Settling:** a custom experiment leaves out 7 days at the start; Google says to allow 7 to 14 days for the trial arm to settle. **Official (references/experiments-and-planning.md).** A heavy up leaves out 5: Google's guidance puts the typical 4 to 5 day learning period inside the test. **Official (references/incrementality.md).**
- **Pre-period for a geo test:** at least three times the test length. **Official (references/incrementality.md).**
- **During a geo test:** budgets move less than 20%, because the geo guidance says a larger change starts a new learning period. **Official (references/incrementality.md).**
- **Confidence:** the plan uses 95% and 80% power. Google's experiment report defaults to 80% confidence and the level can be changed (`references/test-math.md`), so tell the person to set it to the plan's level before reading.
- **Read once, on the stop date.** A look before the planned reading ends, before the settling days pass, or before the conversion lag has passed is an early warning, never a result. If a test must stop early, its smallest detectable lift is the table's row at the days actually measured, and the reply says so. **Practitioner rule.**

## Failure modes

- **Reported return treated as lift.** Conv. value / cost, data driven attribution or a Planner forecast presented as what the ads caused. Check: the question was named first.
- **A lift study or experiment type promised.** Check: the reply lists eligibility checks, never a promise. **Official (references/experiments-and-planning.md).**
- **A test that can only find a huge effect.** Check: the smallest detectable lift against the lift the change could bring.
- **Both arms edited mid test.** Check: the weekly checks, and Experiment sync off when trial edits must not be overwritten.
- **Location targeting left on interest.** Check: test and control regions use the Presence option. **Official (references/incrementality.md).**
- **The decision rule written after the result.** Check: it is in the plan before the start date.

## Worked example

Northside Plumbing (`examples/output/experiments/`).

- Plumbing | Emergency, switch to Target CPA, 15% lift in conversions: "Too little volume". It needs 359 measured days; at 56 days the smallest lift it can see is 42%. Ask whether the switch could bring 42% more conversions. If the person would not expect that, the call is no experiment at this volume: make the change on judgment, said as judgment, and watch it in the regular reports.
- Pausing all campaigns in Evanston, Skokie and Oak Park, 20% lift in leads: "Readable", 18 days planned as 21, with a 63 day pre-period. At 171 conversions over the run, Conversion Lift is out of reach, so the geo test is the design.

## What to tell the client

"We can test this properly. For three weeks we switch the ads off in three of your cities and compare their leads with five cities where nothing changes. We decide now what result would change the budget, and read it once at the end."
