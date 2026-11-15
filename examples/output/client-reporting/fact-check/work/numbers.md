# Numbers for the report

Campaign report.
July 1, 2025 - November 12, 2026.

- Report type: Fact check. Sections the playbook asks for: none.
- Current period: 2026-10-01 to 2026-10-31 (31 days). Previous period: 2026-09-01 to 2026-09-30 (30 days).
- Same period last year: 2025-10-01 to 2025-10-31 (31 days).
- The periods differ in length. Compare per day figures (cost_per_day, conv_per_day) as well as totals.
- Amounts are in USD.
- The rows add up to 233,583.77 of cost. The file's own Total: Filtered campaigns is 233,583.77.
- NOTE: The report runs to 2026-11-12. Days after 2026-10-31 are not part of this report.
- NOTE: Drain Cleaning | Search (c3) is paused on the day of download, and its last day with cost is 2026-10-19. Report it as paused, not as a decline.
- NOTE: Brand is an outlier: 4.13 per conversion against 50.24 for the rest of the account, and 72.29 Conv. value / cost against 6.49. Brand searches convert cheaply by nature, so give the figures without brand first (nb ids) and say why the blended figure flatters. Outlier means under half the rest's cost per conversion, or over twice its Conv. value / cost. Practitioner rule.

## How to cite a number

Write every number in the narrative as its id in braces, for example {acct.cost.chg_prev}. The id is SCOPE.MEASURE.COMPARISON.

- Scopes: acct = Account; nb = Account without brand; c1 = Plumbing | Emergency; c2 = Plumbing | Water Heaters; c3 = Drain Cleaning | Search (paused); c4 = Brand.
- Measures: cost, impr, clicks, ctr, cpc, conv, cvr, cpa, value, roas, cost_per_day, conv_per_day.
- Comparisons: cur, prev, ly; chg_prev, chg_ly (relative change); delta_prev, delta_ly (difference); pp_prev, pp_ly (ctr and cvr, in percentage points); share_cur and share_chg_prev (campaigns only: share of the account total, and of the account's change).
- Dates: period.cur.start, period.cur.end, period.prev.start, period.prev.end, period.ly.start, period.ly.end, and days: period.cur.days, period.prev.days.
- A change id is written without its sign when your sentence says which way it went (rose, fell), and with its sign when it does not. Add .abs to any id to always drop the sign: {c3.cost.delta_prev.abs}.
- Other ids: target.cpa, target.roas, target.cost, target.conv (the targets given); score.cpa.diff, score.cpa.diff_pct (and score.cpa_nb.* without brand); count.campaigns, count.changes.cur; cN.last_cost_day; report.prepared; given1, given2.

## Account (acct)

| Measure | Now | Previous | Change | Difference | Last year | Change vs last year |
|---|---|---|---|---|---|---|
| Cost (acct.cost) | 14,423.32 | 14,985.34 | -3.8% | -562.02 | 13,176.20 | +9.5% |
| Impr. (acct.impr) | 28,548 | 31,146 | -8.3% | -2,598 | 27,371 | +4.3% |
| Clicks (acct.clicks) | 2,117 | 2,208 | -4.1% | -91 | 1,956 | +8.2% |
| CTR (acct.ctr) | 7.42% | 7.09% | +4.6% | +0.33 percentage points | 7.15% | +3.8% |
| Avg. CPC (acct.cpc) | 6.81 | 6.79 | +0.4% | +0.03 | 6.74 | +1.1% |
| Conversions (acct.conv) | 413.49 | 407.22 | +1.5% | +6.27 | 352.04 | +17.5% |
| Conv. rate (acct.cvr) | 19.53% | 18.44% | +5.9% | +1.09 percentage points | 18.00% | +8.5% |
| Cost / conv. (acct.cpa) | 34.88 | 36.80 | -5.2% | -1.92 | 37.43 | -6.8% |
| Conv. value (acct.value) | 131,045.84 | 133,251.48 | -1.7% | -2,205.64 | 114,681.28 | +14.3% |
| Conv. value / cost (acct.roas) | 9.09 | 8.89 | +2.2% | +0.19 | 8.70 | +4.4% |
| Cost per day (acct.cost_per_day) | 465.27 | 499.51 | -6.9% | n/a | 425.04 | +9.5% |
| Conversions per day (acct.conv_per_day) | 13.34 | 13.57 | -1.7% | n/a | 11.36 | +17.5% |

## Account without brand (nb)

| Measure | Now | Previous | Change | Difference | Last year | Change vs last year |
|---|---|---|---|---|---|---|
| Cost (nb.cost) | 13,855.33 | 14,438.08 | -4.0% | -582.75 | 12,687.14 | +9.2% |
| Impr. (nb.impr) | 27,212 | 29,871 | -8.9% | -2,659 | 26,254 | +3.6% |
| Clicks (nb.clicks) | 1,719 | 1,826 | -5.9% | -107 | 1,617 | +6.3% |
| CTR (nb.ctr) | 6.32% | 6.11% | +3.3% | +0.20 percentage points | 6.16% | +2.6% |
| Avg. CPC (nb.cpc) | 8.06 | 7.91 | +1.9% | +0.15 | 7.85 | +2.7% |
| Conversions (nb.conv) | 275.81 | 278.96 | -1.1% | -3.15 | 242.16 | +13.9% |
| Conv. rate (nb.cvr) | 16.04% | 15.28% | +5.0% | +0.77 percentage points | 14.98% | +7.1% |
| Cost / conv. (nb.cpa) | 50.24 | 51.76 | -2.9% | -1.52 | 52.39 | -4.1% |
| Conv. value (nb.value) | 89,985.19 | 94,405.47 | -4.7% | -4,420.28 | 82,313.38 | +9.3% |
| Conv. value / cost (nb.roas) | 6.49 | 6.54 | -0.7% | -0.04 | 6.49 | +0.1% |
| Cost per day (nb.cost_per_day) | 446.95 | 481.27 | -7.1% | n/a | 409.26 | +9.2% |
| Conversions per day (nb.conv_per_day) | 8.90 | 9.30 | -4.3% | n/a | 7.81 | +13.9% |

## Campaigns, current period and change vs previous

| id | Campaign | Status | Cost | Cost chg | Conv. | Conv. chg | Cost / conv. | Cost / conv. chg | Share of cost | Share of conv. | Conv. value / cost | Conv. value / cost chg | Cost chg vs LY | Conv. chg vs LY |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c1 | Plumbing \| Emergency | Enabled | 8,378.50 | +15.7% | 207.68 | +19.3% | 40.34 | -3.0% | 58.1% | 50.2% | 7.46 | +2.8% | +32.7% | +40.4% |
| c2 | Plumbing \| Water Heaters | Enabled | 3,157.08 | -8.9% | 42.55 | -34.1% | 74.20 | +38.3% | 21.9% | 10.3% | 7.02 | -27.4% | +3.8% | -26.4% |
| c3 | Drain Cleaning \| Search | Paused | 2,319.75 | -37.8% | 25.58 | -36.5% | 90.69 | -2.1% | 16.1% | 6.2% | 2.31 | +2.6% | -30.4% | -29.7% |
| c4 | Brand (brand) | Enabled | 567.99 | +3.8% | 137.68 | +7.3% | 4.13 | -3.3% | 3.9% | 33.3% | 72.29 | +1.8% | +16.1% | +25.3% |

Every other measure of a campaign follows the same ids, for example c1.ctr.cur. All ids are in numbers.json.

## Biggest movers vs previous period

- Conversions: c1 Plumbing | Emergency +33.55 (+19.3%); c2 Plumbing | Water Heaters -22.02 (-34.1%); c3 Drain Cleaning | Search -14.68 (-36.5%); c4 Brand +9.42 (+7.3%).
- Cost: c3 Drain Cleaning | Search -1,410.48 (-37.8%); c1 Plumbing | Emergency +1,134.43 (+15.7%); c2 Plumbing | Water Heaters -306.70 (-8.9%); c4 Brand +20.73 (+3.8%).
- Conv. value: c2 Plumbing | Water Heaters -11,328.36 (-33.8%); c1 Plumbing | Emergency +9,952.67 (+19.0%); c3 Drain Cleaning | Search -3,044.59 (-36.2%); c4 Brand +2,214.64 (+5.7%).

## Changes made in the current period

- 5 changes in all (count.changes.cur): 4 by people, 1 by Google's systems.
- chg1 (2026-10-01), by sam@northside.example, in Plumbing | Emergency: Budget changed from 200.00 to 240.00. Numbers in it: chg1.n1 = 200.00, chg1.n2 = 240.00
- chg2 (2026-10-06), by sam@northside.example, in Plumbing | Water Heaters: Bid strategy changed from Maximize conversions to Target CPA; Target CPA set to 45.00. Numbers in it: chg2.n1 = 45.00
- chg3 (2026-10-14), by Google's systems (Google Ads system), in Plumbing | Emergency, ad group Emergency: 6 keywords added (broad match). Numbers in it: chg3.n1 = 6
- chg4 (2026-10-20), by lee@northside.example, in Drain Cleaning | Search: Campaign status changed from Enabled to Paused
- chg5 (2026-10-27), by lee@northside.example, in Brand: Sitelink asset added
- Cite a change's date as chgN.date and a number inside it as chgN.n1, chgN.n2, as listed.

## Next

Copy narrative.template.json to narrative.json in the work folder and write each section. Then run:

    python3 scripts/fact_check.py --work WORK

## How the numbers were made

- Every total is the sum of the report's daily rows over the dates of each period. Ratios are computed from those totals, never averaged.
- Change is (now minus before) divided by before. Difference is now minus before. CTR and Conv. rate differences are in percentage points.
- Per day figures divide by the calendar days in the period.
- Campaign status is the status on the day of download, not on each day of the period.
- Changes made in the period are leads to explain a movement, not proof of its cause.

## What this did not cover

- Conversions for the last days of a period can still rise as late conversions are reported. Practitioner rule.
- Conversions are counted as Google Ads reports them under the account's attribution settings. **Official:** the attribution model affects the Conversions column (references/attribution.md).
- Nothing outside Google Ads: the website, the CRM, other channels or sales.
- The change history can miss some changes. **Official:** some account level and Google representative changes may be missing (references/reporting-and-diagnostics.md).
