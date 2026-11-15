# Playbook: Return on investment, and whether the next dollar pays

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-14.

The job: say which campaigns make money after ad cost at the business's margin, which do not, which are too small to call, and whether more spend would pay. It reads the summary `scripts/roi.py` prints. Every figure is attributed value; only a test says what the ads caused.

## When to use it

- "Is Google Ads making money?", "which campaigns lose money?", "should we spend more on X?"
- Whether the ads cause the value at all: `choosing-and-sizing-a-test.md`.

## What to ask first

The gross margin, whether Conv. value is revenue or already profit (`--value-is-profit`), and for lead generation without values, what a lead is worth (`--value-per-conversion`). The script stops without a margin. Never assume one.

## What to read in the output

- The header: "Margin", "Value" and "Break even Conv. value / cost".
- "The answer": Account, Without brand, "Loses money", "Profitable" (or "Profitable by attributed value" when brand is among them), "Too few conversions to call", each "Next dollar in" line, and "Next dollar not answered" with its reasons.
- "Campaigns": Status, Profit, Break even cost / conv., Share of cost, Call.
- "Where the next dollar goes (estimate)": Read from, Value growth per 1% more spend, Shape, Recent value / cost, Next dollar value / cost, Next dollar, "Why not answered, and what would allow it", Recent Search lost IS (budget).

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Call "Loses money" or "No conversions" | Its whole range of Conv. value / cost sits below break even | First check its value per conversion and that its conversions are real. Then cut its budget or bids, or fix it. Largest loss first | Practitioner rule |
| Call "Profitable" | Its whole range sits above break even | Keep it. More budget only if its Next dollar is "Pays" | Practitioner rule |
| Call "Too few conversions to call" | Its range crosses break even | No cut and no raise on this. Read again over a longer range | Practitioner rule |
| "Profitable by attributed value" on brand | Brand searches are the most likely to convert without ads | Report it apart. Test brand before moving its budget | Official (references/incrementality.md) |
| Next dollar "Pays" | The whole range for the next dollar clears break even | More budget pays at this margin, as an estimate. Raise in steps sized by the budgets skill; for a large rise, run a heavy up test | Practitioner rule |
| Next dollar "Does not pay" | Extra spend returns less than break even, even if the average pays | Hold the budget. Do not raise it on the average | Practitioner rule |
| Next dollar "Unclear", range crosses break even | Not settled | No budget move on this estimate | Practitioner rule |
| Shape "Returns rose with spend" | Often demand that rose with spend, not the spend itself | Treat it with care; confirm with a heavy up test before a large rise | Practitioner rule (references/test-math.md) |
| A paused campaign | Counted in totals for what it spent | "Not asked": no next dollar question | Practitioner rule |

## When the next dollar cannot be fitted

The average return says whether a campaign pays now. It never says whether more spend pays: never use it in place of the next dollar. **Practitioner rule.** What to do depends on the printed reason:

| Reason printed | What would answer it | What to do now |
|---|---|---|
| "Spend hardly varied: a typical day's (or week's) spend sat within about N% of the average" (the line is 10%) | Some weeks at a clearly different budget | Ask whether the budget changed in the past and widen the date range to include it. If it never did, a planned step up for a few weeks, or a heavy up geo test, creates the evidence. Hold until then |
| "Only N days had both spend and value (a daily fit needs 21) and only N full weeks did (a weekly fit needs 12)" | A longer date range: 12 full weeks or more with value | Download a longer range and run again |
| "N of N days with spend had no value, too many for a daily fit" (more than 25%) | 12 full weeks with value | Download a longer range. If value is rare by nature, set a value per lead |
| "The range for how value grows with spend is too wide" | More days, or a longer stretch at a different budget | Widen the range; hold meanwhile |
| "The range for the next dollar's return crosses break even" | More days at different spend levels | Hold; read again later |

Recent Search lost IS (budget) above zero says the campaign could spend more. It never says the extra spend would pay. For a campaign that loses money on average, the next dollar is not the question: fix it first.

## How big a change

This skill sizes no budget step. Name the call and hand the size to the budgets skill. The curve is an estimate from observed days: days with more spend often had more demand too, which pulls value growth toward 1.00 and flatters the next dollar (`references/test-math.md`). That is why a large rise is tested first.

## Failure modes

- **Average return used as marginal.** "3.97 against 2.50, so spend more" while the next dollar brings 1.38. Check: the Next dollar column.
- **Brand counted as proof.** Check: brand reported apart, with the without brand figures.
- **A small pocket scaled.** A campaign or ad group with a fine Conv. value / cost on few conversions. Check: its Call.
- **A loss cut before its value is checked.** Check: value per conversion and conversion actions first.
- **A margin assumed.** Check: the person gave it.

## Worked example

Northside Plumbing, 40% margin, break even 2.50 (`examples/output/experiments/roi/`).

- Account profit after ad cost 38,022.05 on 38,947.52; without Brand, 9,377.27 at 3.14.
- Plumbing | Water Heaters loses money: 1.77, profit -2,899.69, 25.5% of cost. First in line. Its 13% Recent Search lost IS (budget) is beside the point.
- Plumbing | Emergency is profitable at 3.97, but the next dollar brings 1.38 (range 0.49 to 2.28): does not pay. Hold its budget.
- Drain Cleaning | Search is too few to call (range 2.35 to 3.95), and its spend hardly varied (within about 2% a week): hold, and ask about past budget changes.
- Brand: 36.03 attributed; its next dollar is unclear. Test before moving it.

## What to tell the client

"Google Ads makes money overall at your margin, mostly from Emergency and Brand. Water Heaters loses money, so we fix or cut it first. Emergency pays on average, but more budget there would not, so we keep it where it is."
