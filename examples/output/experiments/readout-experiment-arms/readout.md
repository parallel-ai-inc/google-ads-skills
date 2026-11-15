# Experiment readout

Experiment report.
September 24, 2026 - November 11, 2026.

## The answer

- **Conversions, the outcome asked about:** +17.0%, range -9.5% to +51.3% at 95% confidence. No clear difference. Figure: ours.
- Clearly different: Avg. CPC +14.8% (higher, worse, figure: ours); Conv. rate +29.6% (higher, better, figure: ours).
- No clear difference: Impr., Clicks, Cost, Conv. value, CTR, Cost / conv., Conv. value / cost.

## Every metric

| Metric | Control | Trial | Difference | Range low | Range high | Significant | Verdict | Whose figure |
|---|---|---|---|---|---|---|---|---|
| Impr. | 11,561 | 10,523 | -9.0% | -20.3% | +4.0% | No | No clear difference | ours |
| Clicks | 793 | 716 | -9.7% | -20.1% | +2.1% | No | No clear difference | ours |
| Cost | 5,989.51 | 6,210.05 | +3.7% | -8.5% | +17.5% | No | No clear difference | ours |
| Conversions | 94.00 | 110.00 | +17.0% | -9.5% | +51.3% | No | No clear difference | ours |
| Conv. value | 19,820.11 | 22,986.92 | +16.0% | -10.6% | +50.5% | No | No clear difference | ours |
| CTR | 6.86% | 6.80% | -0.8% | -4.3% | +2.8% | No | No clear difference | ours |
| Avg. CPC | 7.55 | 8.67 | +14.8% | +13.4% | +16.3% | Yes | Higher, worse | ours |
| Conv. rate | 11.85% | 15.36% | +29.6% | +4.0% | +61.5% | Yes | Higher, better | ours |
| Cost / conv. | 63.72 | 56.45 | -11.4% | -29.1% | +10.7% | No | No clear difference | ours |
| Conv. value / cost | 3.31 | 3.70 | +11.9% | -10.7% | +40.1% | No | No clear difference | ours |

- Days read: 42, 2026-10-01 to 2026-11-11. 14 rows outside the dates asked for were left out (`--from` and `--to`).
- The trial took 47.6% of impressions with a 50% split. **Official** (`references/experiments-and-planning.md`): the split sets which auctions each arm can enter, not equal impressions or spend.
- Totals (Impr., Clicks, Cost, Conversions, Conv. value) are compared after scaling each arm to its share of the split. Rates and ratios are compared as they are.

## How the numbers were made

- The file has no account total row, so the rows could not be checked against one.
- Our range: each day is one observation of both arms; the log of the trial over control ratio gets its spread from how the days vary (delta method), with a t value for the number of days. Days both arms shared cancel out. See `references/test-math.md`.
- Confidence: 95%, two sided. A metric is called different only when its whole range sits on one side of zero.

## What this did not cover

- An experiment compares two setups of the same campaign. It says which one Google Ads attributes more to, not how much the ads cause in total.
- Conversions still to come in from late reporting. Read again after the conversion lag has passed.
