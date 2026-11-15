# Return on investment

Campaign report.
August 15, 2026 - November 12, 2026.

Period read: 2026-08-15 to 2026-11-12.
Amounts are in USD.
Margin: 40%. Value: Conv. value. Break even Conv. value / cost: 2.50 (1 / margin).

## The answer

- **Account:** profit after ad cost 38,022.05 on 38,947.52 of cost. Conv. value / cost 4.94 against a break even of 2.50.
- **Without brand** (campaigns with "brand" in the name: Brand): profit 9,377.27 on 36,811.73 of cost, Conv. value / cost 3.14. Brand's return is attributed, and brand searches are the ones most likely to convert without the ads.
- **Loses money:** Plumbing | Water Heaters (profit -2,899.69, Conv. value / cost 1.77).
- **Profitable by attributed value:** Brand (profit 28,644.78, Conv. value / cost 36.03); Plumbing | Emergency (profit 10,958.07, Conv. value / cost 3.97).
- **Too few conversions to call:** Drain Cleaning | Search (profit 1,461.86, Conv. value / cost 3.15); Sewer Line | Search (profit -142.97, Conv. value / cost 2.36, Paused).
- **Next dollar in Plumbing | Emergency:** does not pay (estimate). Recent Conv. value / cost is 3.23; each extra dollar brings about 1.38 (range 0.49 to 2.28) against a break even of 2.50.
- **Next dollar not answered:**
  - Brand: spend hardly varied: a typical day's spend sat within about 6% of the average. It needs some weeks at a clearly different budget, such as before and after a budget change.
  - Drain Cleaning | Search: spend hardly varied: a typical week's spend sat within about 2% of the average. It needs some weeks at a clearly different budget, such as before and after a budget change.
  - Sewer Line | Search: the campaign is Paused, not serving. Not asked.
  - Plumbing | Water Heaters: spend hardly varied: a typical week's spend sat within about 2% of the average. It needs some weeks at a clearly different budget, such as before and after a budget change.

## Campaigns

Ranked by profit after ad cost. Share of cost is the share of the whole account's cost (38,947.52).

| Campaign | Status | Cost | Conv. | Value | Value / cost | Profit | Cost / conv. | Break even cost / conv. | Share of cost | Call |
|---|---|---|---|---|---|---|---|---|---|---|
| Brand | Enabled | 2,135.79 | 256.00 | 76,951.42 | 36.03 | 28,644.78 | 8.34 | 120.24 | 5.5% | Profitable |
| Plumbing \| Emergency | Enabled | 18,682.30 | 355.00 | 74,100.92 | 3.97 | 10,958.07 | 52.63 | 83.49 | 48.0% | Profitable |
| Drain Cleaning \| Search | Enabled | 5,653.45 | 42.00 | 17,788.28 | 3.15 | 1,461.86 | 134.61 | 169.41 | 14.5% | Too few conversions to call (range 2.35 to 3.95) |
| Sewer Line \| Search | Paused | 2,556.71 | 15.00 | 6,034.35 | 2.36 | -142.97 | 170.45 | 160.92 | 6.6% | Too few conversions to call (range 1.36 to 3.36) |
| Plumbing \| Water Heaters | Enabled | 9,919.27 | 92.00 | 17,548.95 | 1.77 | -2,899.69 | 107.82 | 76.30 | 25.5% | Loses money |

## Where the next dollar goes (estimate)

How much Conv. value grows when daily spend is higher, from the campaign's own days, then the Conv. value the next dollar brings at the last 28 days' return.

| Campaign | Read from | Value growth per 1% more spend | Shape | Recent value / cost | Next dollar value / cost | Next dollar | Why not answered, and what would allow it | Recent Search lost IS (budget) |
|---|---|---|---|---|---|---|---|---|
| Brand | 79 days | 0.29 (-1.53 to 2.11) | Can't tell from this data | 26.96 | 7.81 (-41.31 to 56.94) | Unclear | Spend hardly varied: a typical day's spend sat within about 6% of the average. Needs some weeks at a clearly different budget, such as before and after a budget change. | n/a |
| Plumbing \| Emergency | 88 days | 0.43 (0.15 to 0.71) | Returns fall as spend rises | 3.23 | 1.38 (0.49 to 2.28) | Does not pay |  | n/a |
| Drain Cleaning \| Search | 12 weeks | -3.92 (-19.71 to 11.88) | Can't tell from this data | 3.69 | -14.44 (-72.65 to 43.76) | Unclear | Spend hardly varied: a typical week's spend sat within about 2% of the average. Needs some weeks at a clearly different budget, such as before and after a budget change. | n/a |
| Sewer Line \| Search | 0 days | not fitted |  | n/a |  | Not answered | The campaign is paused, not serving. Not asked. |  |
| Plumbing \| Water Heaters | 12 weeks | -2.04 (-13.60 to 9.53) | Can't tell from this data | 2.05 | -4.18 (-27.91 to 19.55) | Unclear | Spend hardly varied: a typical week's spend sat within about 2% of the average. Needs some weeks at a clearly different budget, such as before and after a budget change. | 13% |

A value growth of 1.00 means value rises in step with spend. Below 1.00, each extra dollar returns less than the average dollar.

## How the numbers were made

- The rows add up to the file's own total (Total: Account (added up over 90 days)): Cost 38,947.52, Conversions 760.00, Conv. value 192,423.92.
- Profit after ad cost = value x margin, minus Cost. Break even Conv. value / cost = 1 / margin; break even cost / conv. = value per conversion x margin. This is business arithmetic, not a Google Ads rule (`references/test-math.md`).
- A campaign's call uses a 90% range on its conversion count (Poisson), holding value per conversion fixed. When that range crosses break even, it is too few conversions to call.
- Paused campaigns are counted in the totals for the cost they spent, and left out of the next dollar question.
- Next dollar: log(daily value) = a + b log(daily cost) + a weekday term (when there are 28 days or more), by least squares, on days with both spend and value. It needs at least 21 such days. When more than 25% of days with spend had no value, or there are too few days, it uses full Monday to Sunday weeks instead and needs 12 of them. b times the last 28 days' Conv. value / cost is the next dollar's return. It is an **estimate**: days with more spend often also had more demand, which pulls b toward 1.
- The curve can't be read when spend hardly varied: a typical day (or week) within about 10% of the average. That case says so, and what data would let it answer.

## What this did not cover

- Conv. value is what Google Ads attributed, not what the ads caused. A campaign can look profitable and still add little: only a test shows the difference.
- **Official** (`references/incrementality.md`): a 2012 Google meta-analysis found ad clicks less incremental when the advertiser already ranked first organically. That is a historical average, not a current rate. Test brand with an experiment before moving its budget.
- Costs other than ad cost and the margin (fees, labour, returns), and value that arrives after the report's last day.
