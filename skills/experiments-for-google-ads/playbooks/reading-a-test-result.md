# Playbook: Read a finished test and decide from it

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-14.

The job: say what a test found, how far to trust it, and what the person should do. It reads the summary `scripts/readout.py` prints for an experiment, a geo test or an on and off test. The trust rules behind the verdicts are in `references/reading-a-result.md`; this playbook turns each verdict into a decision.

## When to use it

- A custom experiment, geo test or on and off test has run.
- The person does not remember the test regions or dates: run `find` first, and confirm its candidate.
- Planning a test: `choosing-and-sizing-a-test.md`.

## What to read in the output

- **Experiment:** "The answer": the outcome asked about, its difference, range, verdict and "Figure: Google" or "ours"; "Clearly different" and "No clear difference". In "Every metric", the Verdict and Whose figure columns. Under it, "Days read" and the trial's share of impressions against the split.
- **Geo test:** the "found from the data" line if present; "Verdict" with "Why that verdict" (placebo share, R squared); "The ads caused about"; "Spend removed"; "Cost per incremental lead"; the share of the attributed figure; "Profit" with its range and "The ads make money", "lose money" or "not settled"; "The stated test and the data differ"; "Control regions that moved on their own" and the result without them; "To confirm with the person".
- **On and off:** the change per off day, its range, and "Read with care" when the outcome is Google Ads' own Conversions.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| A figure marked "Google" | Google's report gave the significance | Show it as given; never replace it with ours | Official (references/experiments-and-planning.md) |
| Outcome asked about: "No clear difference" | No lift of the size the test could detect | Keep the original, as the plan's rule says. A positive point estimate is not a win | Practitioner rule |
| Outcome asked about: "Higher, better" (or "Lower, better" for a cost) | The trial won on the outcome | Apply the trial | Practitioner rule |
| Outcome unclear, another metric "Clearly different" | A side effect, not the answer | Report it as a movement. Never decide on it | Practitioner rule |
| "Higher, worse" on a cost metric | The trial pays more for what it gets | Weigh it beside the outcome before applying | Practitioner rule |
| Trial share of impressions away from the split | The split sets auction eligibility, not equal impressions | Normal. Only a collapse in one arm is a problem | Official (references/experiments-and-planning.md) |
| Geo "Strong" | The effect is real at about this size | Use the range, not only the middle, in any budget decision | Practitioner rule (references/reading-a-result.md) |
| Geo "Directional only" | The direction is likely, the size is not settled | No budget decision on the number alone. Repeat longer or with more regions | Practitioner rule (references/reading-a-result.md) |
| Geo "Not readable" | No conclusion | Say so. Name what would help: a longer pre-period, a longer test, controls that track better | Practitioner rule (references/reading-a-result.md) |
| "found from the data, not given by the person" | Regions and dates are a candidate | Confirm before anyone acts | Practitioner rule (references/reading-a-result.md) |
| "The stated test and the data differ" | Memory and cost data disagree | Give both readings. Use the full off period unless the person says the extra days were something else | Practitioner rule (references/reading-a-result.md) |
| A control region "moved" | Its own event shifts the prediction | Ask what happened there. If they confirm an event, lead with the result without it | Practitioner rule (references/reading-a-result.md) |
| Share of the attributed figure below 100% | Google Ads credits the ads with some conversions that would have come anyway, in these regions and weeks | Say so for this test. Never apply the share to other campaigns or periods | Practitioner rule |
| Profit "not settled" | The range crosses zero | No budget move on this test | Practitioner rule |
| "Read with care": the outcome is Google Ads' Conversions | It stops when the ads stop | Treat the drop as an upper bound, and ask for the business's own count | Practitioner rule |
| The person asks which campaign worked | A geo test reads every campaign in the regions together | Say it cannot be split | Practitioner rule (references/reading-a-result.md) |

## How big a change

- **A test read early is an early warning, never a result.** Before the plan's reading dates end, inside the settling days, or before the conversion lag has passed, say what it shows so far and when the real read is. **Practitioner rule.**
- **Applying an experiment's trial** is the whole change the test measured. Nothing larger.
- **A geo result** says what the ads in those regions return, not how big a budget step should be. Size a budget move with the budgets skill; for a large rise, run a heavy up test first. No source here gives a step size.

## Failure modes

- **Our figure shown over Google's.** Check: Whose figure.
- **A secondary metric called the result.** Conv. rate clear while conversions are not. Check: the outcome asked about leads.
- **A candidate test read as fact.** Check: the person confirmed regions and dates.
- **Only the stated window given** when cost stayed off longer. Check: both readings appear.
- **Attributed and incremental merged.** Check: the share of the attributed figure is stated as a share, for these regions only.

## Worked example

Northside Plumbing (`examples/output/experiments/`).

- **Geo, found from the data:** Evanston, Skokie and Oak Park, ads off from October 22. Verdict Strong: 128.1 fewer leads than predicted (-29.2%), range -189.4 to -66.7; a gap this large appeared in 0% of 69 placebo windows. Cost per incremental lead 15.11. The ads caused 66% of what Google Ads attributed. Profit 5.33 per unit of spend (range 2.18 to 8.48): the ads make money at a 40% margin.
- Cost stayed off until November 11, not November 4: over 21 days, still Strong. Niles moved +37.3% on its own; without it the ads caused 51% of the attributed figure and profit is 4.03 (range 1.29 to 6.77), still positive. Ask about Niles; the cautious reading is without it.
- **Experiment:** conversions +17.0%, range -9.5% to +51.3%, Google's figure: no clear difference, so keep the original. Conv. rate +29.6% is clear, but it is not the outcome asked about.

## What to tell the client

"With the ads off in three cities, those cities got 29.2% fewer leads than the other cities predicted. Each lead the ads brought cost 15.11. Google Ads gives the ads credit for more leads than they caused, so we judge budget on this test, not on the dashboard." Use the readout's own figures, and the ones without a flagged region once the person confirms its event.
