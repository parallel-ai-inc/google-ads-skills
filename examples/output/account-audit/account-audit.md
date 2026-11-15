# Google Ads account audit

## The answer

The account converts, but two primary actions count the same lead form, so the campaigns that bid on conversions steer by inflated numbers. Fix that first. After it, the Emergency campaign is the clearest place for more budget, and the Hydro Jetting ad group needs a working ad.

## What I read

- Google Ads exports: campaign report, ad group report, keyword report, ads report, search terms report, conversions summary, campaign report segmented by network, for October 14, 2026 - November 12, 2026.
- Amounts are in USD.
- No target cost per conversion was given. BB-06 did not run, and BB-03, BB-04, KW-05, SQ-01 used the account's own cost per conversion as the line instead.
- Brand terms used: northside. Brand campaigns: Brand. Brand rows were kept out of the lines in BB-03, BB-04, KW-05, SQ-01.
- The account spent 12,578.35 across 5 campaigns, 12,268.10 of it in the 4 enabled campaigns. Paused and removed campaigns, ad groups, keywords and ads were not judged as if serving.

## Result

- 23 checks ran: 7 passed and 16 failed. Of the failed checks, 15 matter for this account and 1 was judged not to apply.
- 2 checks could not run with these files, and 4 settings can only be checked in Google Ads. Both are listed below with what would unlock them.
- There is no single score. Money is of three kinds, wasted, exposed and held back, ranked within each kind and never added together.

## Where money is wasted

**Clear waste, counted once: 2,389.00**, 19.0% of the account's cost.

- Includes: Spend with no conversions on non brand search terms that spent at least the search term line (SQ-01), and on enabled keywords that spent at least the keyword line (KW-05).
- Leaves out: Brand searches, searches and keywords below those lines, searches Google does not list, paused campaigns, and every exposed or held back amount. Campaign level spend with no conversions (BB-04) is left out because it holds the same spend.
- A search served by a flagged keyword is inside that keyword's cost, so it is counted once, as part of the keyword. 1,432.80 was removed this way.

| Campaign | Clear waste |
|---|---|
| Plumbing \| Emergency | 1,763.20 |
| Plumbing \| Water Heaters | 436.50 |
| Drain Cleaning \| Search | 189.30 |

## Findings by money

Each table is ranked by money within its kind. The kinds are never added together, and money under one check can also sit under another.

### Wasted

Spend with no result.

| Check | Money | Share of account cost | What the money is |
|---|---|---|---|
| SQ-01 Search terms that spent a conversion's cost converted | 2,301.80 | 18.3% | the cost of those search terms, with no conversions |
| KW-05 Keywords that spent a conversion's cost converted | 1,520.00 | 12.1% | the cost of those keywords, with no conversions |

### Exposed

Spend that depends on a problem. It was not lost, but it rests on something that needs fixing.

| Check | Money | Share of account cost | What the money is |
|---|---|---|---|
| CT-03 Lead actions count one conversion per click | 4,413.70 | 35.1% | the cost of the enabled campaigns that bid on conversions, because their bidding steers by these actions |
| CT-04 One primary action per kind of conversion | 4,413.70 | 35.1% | the cost of the enabled campaigns that bid on conversions, because their bidding steers by these actions |
| KW-04 Broad match keywords without conversion based bidding | 2,209.30 | 17.6% | the cost of broad match keywords in campaigns that do not bid on conversions |
| AD-04 Two responsive search ads rated Good or Excellent per ad group | 2,024.40 | 16.1% | the cost of those ad groups in the period |
| KW-01 Keywords with a Below average Quality Score component | 1,068.80 | 8.5% | the cost of the keywords with a Below average component |
| SE-02 Search partners and the Display Network earn their cost in Search campaigns | 672.22 | 5.3% | the cost on those networks |
| AD-01 Every live ad group has an active ad | 357.00 | 2.8% | the cost of those ad groups in the period. They cannot show an ad now |
| AD-03 No ads limited by policy | 306.00 | 2.4% | the cost of those ads. They can show only in some places, to some ages or on some devices |
| AD-02 No disapproved ads | 303.45 | 2.4% | the cost those ads carried in the period before they stopped |
| KW-02 No duplicate keywords | 180.60 | 1.4% | the cost of every copy except the costliest one |
| SQ-02 Brand searches are served by the brand campaigns | 99.70 | 0.8% | the cost of brand searches served outside the brand campaigns |
| KW-03 Enabled keywords get impressions | 0.00 | 0.0% | zero, because these keywords spent nothing. They are clutter that hides what serves |

### Held back (estimate, upper bound)

An estimate of spend the budget kept out. It is an upper bound, because the searches the ads missed usually convert worse than the ones they won, so it is not shown as a share of the account's cost.

| Check | Money | What the money is |
|---|---|---|
| BB-03 Budget does not hold back campaigns that convert well | 5,115.87 | an estimate of the spend the budget held back from campaigns that convert at or below the account's own cost per conversion: cost times Search lost IS (budget), divided by Search impr. share. It assumes the missed impressions would cost what the shown ones did. It is an upper bound, because the searches the ads missed usually convert worse than the ones they won. Where Search impr. share is missing, the campaign's whole cost is used |

## Fix plan

Fixes run in this order, whatever the money: measurement first, then what stops ads serving, then waste, then structure and ads, then bidding, then budget. Bidding learns from conversions, so it is changed once they are counted right, and more budget is added last so it does not scale a problem.

1. **Lead actions count one conversion per click** (CT-03, Measurement). Money: exposed 4,413.70, which is the cost of the enabled campaigns that bid on conversions, because their bidding steers by these actions.
   - Found: Primary lead actions: 3. Counting Every: 1.
   - Where: GA4 generate_lead.
   - Fix: Set the Count of GA4 generate_lead to One, so one ad click counts one lead. The change applies to future conversions only.
   - Basis: Official. Google Ads Help: About conversion counting options.
2. **One primary action per kind of conversion** (CT-04, Measurement). Money: exposed 4,413.70, which is the cost of the enabled campaigns that bid on conversions, because their bidding steers by these actions.
   - Found: Categories with a recording primary action: 2. With two or more: 1.
   - Where: Contact form submit; GA4 generate_lead.
   - Fix: Keep Contact form submit as the primary action for the lead form and set GA4 generate_lead to secondary, so each form fill is counted once for bidding. Then watch the two Maximize Conversions campaigns, as their bidding will see fewer conversions.
   - Basis: Practitioner rule.
3. **Every live ad group has an active ad** (AD-01, Serving and policy). Money: exposed 357.00, which is the cost of those ad groups in the period. They cannot show an ad now.
   - Found: Live Search ad groups: 7. With no enabled, approved ad: 1.
   - Where: Drain Cleaning | Search > Hydro Jetting.
   - Fix: Fix the landing page behind the disapproved Hydro Jetting ad, then ask for a review, or enable the paused ad, so the ad group can show ads again.
   - Basis: Practitioner rule.
4. **No disapproved ads** (AD-02, Serving and policy). Money: exposed 303.45, which is the cost those ads carried in the period before they stopped.
   - Found: Enabled ads in live ad groups: 14. Disapproved: 1.
   - Where: Drain Cleaning | Search > Hydro Jetting > Hydro Jetting Specialists.
   - Fix: Same fix as AD-01: repair the destination, then request a review of the Hydro Jetting Specialists ad.
   - Basis: Official. Google Ads Help: Disapproved: Definition.
5. **No ads limited by policy** (AD-03, Serving and policy). Money: exposed 306.00, which is the cost of those ads. They can show only in some places, to some ages or on some devices.
   - Found: Enabled ads in live ad groups: 14. Limited by policy: 1.
   - Where: Drain Cleaning | Search > Drains > Roto Style Drain Service.
   - Fix: Remove the trademarked term from the Roto Style Drain Service ad, or replace that ad.
   - Basis: Official. Google Ads Help: Eligible (limited): Definition.

Then, in order:

6. **Keywords that spent a conversion's cost converted** (KW-05, Waste; wasted 1,520.00). Pause the broad match keyword plumber near me, or change it to phrase match, and let the search term review decide which of its searches to keep.
7. **Search partners and the Display Network earn their cost in Search campaigns** (SE-02, Waste; exposed 672.22). Turn off Search partners in Plumbing | Emergency. The cost per conversion there is several times the cost on Google search.
8. **Search terms that spent a conversion's cost converted** (SQ-01, Waste; wasted 2,301.80). Add negatives for job seekers (jobs, hiring, salary) and do it yourself searches (diy, how to) at account level, after testing them against the converting searches. Keep plumber near me on Watch, as it is a core service search.
9. **Brand searches are served by the brand campaigns** (SQ-02, Waste; exposed 99.70). Add northside as a negative in the non brand campaigns, so brand searches go to the Brand campaign.
10. **Two responsive search ads rated Good or Excellent per ad group** (AD-04, Structure, keywords and ads; exposed 2,024.40). Write a second strong responsive search ad in Repair and in Burst Pipes, with more distinct headlines, until two ads in each are rated Good or Excellent.
11. **Keywords with a Below average Quality Score component** (KW-01, Structure, keywords and ads; exposed 1,068.80). Send plumber free estimate to a page about free estimates, and move water heater not heating to an ad group with ads about no hot water.
12. **No duplicate keywords** (KW-02, Structure, keywords and ads; exposed 180.60). Remove the copy of "emergency plumber" from Burst Pipes, so the Emergency ad group owns that search.
13. **Enabled keywords get impressions** (KW-03, Structure, keywords and ads; exposed 0.00). Remove frozen pipe repair, or leave it until winter if frozen pipes are a seasonal service.
14. **Broad match keywords without conversion based bidding** (KW-04, Bidding; exposed 2,209.30). Move Plumbing | Emergency to a conversion based bid strategy once its conversions are clean, or change its broad match keywords to phrase match while it stays on Manual CPC.
15. **Budget does not hold back campaigns that convert well** (BB-03, Budget; held back (estimate, upper bound) 5,115.87). Raise the Plumbing | Emergency budget in steps, and only after the conversion fix in CT-04, so its cost per conversion is read on clean numbers. Watch Search lost IS (budget) and cost per conversion for two weeks after each step.

## Limited by budget by design

- Plumbing | Water Heaters uses Maximize Conversions, which Google builds to spend the full daily budget, so Search lost IS (budget) of 21.1% does not mean it is starved, and it was left out of the budget check. Judge its headroom with the budget simulator in Google Ads, and by whether its cost per conversion holds as the budget rises.

## Failed, but judged not to apply

| Check | Money | Why it does not apply |
|---|---|---|
| ST-01 No single keyword ad groups under Smart Bidding | exposed 357.00 | Hydro Jetting is a distinct service with its own page. One keyword is fine while the ad group has no working ad, and AD-01 covers the real problem there. |

## What passed

| Check | What was found |
|---|---|
| CT-01 Conversions are recorded | Enabled campaigns: 4. Cost 12,268.10. Conversions 167.00. |
| CT-02 Primary conversion actions are recording | Conversion actions in use: 4. Primary: 3. Primary that recorded nothing in the period: 0. |
| ST-02 Brand and non brand keywords sit in separate campaigns | Campaigns with enabled keywords: 4. Holding both brand and non brand keywords: 0. |
| BB-01 No Enhanced CPC left on Search or Display | Enabled campaigns: 4. Using Enhanced CPC: 0. |
| BB-02 A shared budget is not split across different bid strategies | Budgets shared by two or more enabled campaigns: 0. Shared by a Maximize strategy and a different strategy: 0. |
| BB-04 Campaigns that spent a conversion's cost converted | Enabled campaigns: 4. With no conversions and cost of 88.88 or more: 0. |
| SE-01 Enabled campaigns are eligible to serve | Enabled campaigns: 4. Not plainly eligible: 0. Learning: 1 (Drain Cleaning \| Search). |

## Checks not run

| Check | Why | What would unlock it |
|---|---|---|
| BB-05 Value based bidding has conversion value to bid on | The campaign report has no Conv. value column. | The campaign report with the column Conv. value added. In Google Ads: Campaigns menu, Campaigns, Campaigns, then the columns icon. |
| BB-06 Campaigns stay within the target cost per conversion | The target cost per conversion was not given. | The target cost per conversion. |
| SE-M1 Auto-applied recommendations | Auto-applied recommendations are set per account and per type and apply daily. No report download shows which are on. | Check by hand in Google Ads: Recommendations, Auto-apply. |
| SE-M2 AI Max and asset optimization settings in each Search campaign | Search term matching, text customization and Final URL expansion are campaign settings. Campaigns migrated in September 2026 kept their own settings, so each campaign has to be read. | Check by hand in Google Ads: each Search campaign, Settings, AI Max. |
| SE-M3 Conversion tag and enhanced conversions diagnostics | Whether tags fire, and what the diagnostics reports say, is not in any performance export. | Check by hand in Google Ads: Goals, Conversions, open each primary action and its diagnostics. |
| SE-M4 Landing pages load and match the ad | An export lists Final URLs but cannot open them. | Check by hand: open the Final URL of each ad group that spends, on a phone and a computer. |

## How the numbers were made

- Campaign report: 5 rows. The rows add up to 12,578.35 and the file's own total (Total: Filtered campaigns) is 12,578.35.
- Ad group report: 8 rows. The rows add up to 12,578.35 and the file's own total (Total: Account) is 12,578.35.
- Keyword report: 18 rows. The rows add up to 12,578.35 and the file's own total (Total: All but removed keywords) is 12,578.35.
- Ads report: 16 rows. The rows add up to 12,578.35 and the file's own total (Total: Account) is 12,578.35.
- Search terms report: 25 rows. The rows add up to 9,809.40 and the file's own total (Total: Search terms) is 9,809.40.
- Conversions summary: 5 rows.
- Campaign report segmented by network: 7 rows. The rows add up to 12,578.35 and the file's own total (Total: Account) is 12,578.35.
- A campaign with no conversions has spent enough to judge at 88.88. That is the cost per conversion of the non brand enabled campaigns in the campaign report, judged in this audit.
- A keyword with no conversions has spent enough to judge at 88.24. That is the cost per conversion of the non brand enabled keywords in the keyword report, judged in this audit.
- A search term with no conversions has spent enough to judge at 90.56. That is the cost per conversion of the non brand search terms in the search terms report, judged in this audit.
- Each check's threshold is in the workbook. Shares are of the cost of every campaign in the campaign report.
- Quality Score is never averaged. Google says it is a diagnostic and should not be aggregated.
- Each check is labeled Official, when a Google Ads Help page supports it, or Practitioner rule, when it is experience.

## What this did not cover

- Settings no export shows, and the checks listed as not run above.
- The website, the tracking code and anything outside Google Ads.
- Searches Google leaves out of the search terms report for low volume.
- Performance Max asset groups, Shopping product groups, audiences, locations and ad schedules.
- Results after the period of the files. Recent days can still gain conversions reported late.
