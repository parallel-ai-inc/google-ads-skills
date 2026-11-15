<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## LEARNING PHASE MANAGEMENT

### What Google Documents
- A Learning status can appear after you create or reactivate an automated bid strategy, change one of its settings, add or remove campaigns, ad groups or keywords in it, or (on Shopping, in some cases) change ad group targets. Google's status codes also report Learning after a recent budget change or a change to conversion settings or conversion types, so read the campaign's actual status reason.
- On Search and Shopping, changing a Target CPA or Target ROAS doesn't trigger Learning and doesn't reset what Smart Bidding has learned (Google's Search bidding guide). Bids react immediately; a large change can bring short volatility if the campaign enters a new set of auctions, and Google suggests judging the new target after 1-2 conversion cycles.
- Calibration typically takes a few conversion cycles (1-2 typically), faster with more conversion data; duration depends on conversion volume, conversion-cycle length and bid strategy. Learning doesn't apply to Manual CPC, and bid strategy statuses aren't shown for Hotel campaigns.
- After changes to conversion goals or actions (goal swap, primary or secondary setting, source, category or value scale), Smart Bidding needs 1-2 conversion cycles in most cases; Performance Max can take longer.
- Bid strategies continue learning after the visible Learning status clears. Short-window volatility during learning is not enough, by itself, to prove the strategy is broken.

### What Starts Learning, And What Doesn't
| Change | Learning status? |
|--------|------------------|
| New or reactivated bid strategy, or switching strategy | Yes |
| Other bid strategy setting change | Yes |
| Campaigns, ad groups or keywords added to or removed from the strategy | Yes |
| Budget change | Can show in Google's status codes; check the reason |
| Conversion goal, action, setting or value change | Can show; expect 1-2 conversion cycles |
| Target CPA or Target ROAS change (Search, Shopping) | No; bids move at once, judge after 1-2 cycles |
| Bid or other setting change on Demand Gen | Google's Demand Gen guide: some or all learning restarts; a large change can be a total reset |
| Shopping ad group target change | In some cases |

### How To Evaluate Learning Safely
1. Check Change History first so you know what changed and when, then read the bid strategy status and its reason.
2. Compare performance outside the most recent conversion-delay window before declaring failure.
3. Compare actual results with the average target in the bid strategy report before another major edit.
4. Avoid stacking several target edits inside one conversion cycle, or mixing a target edit with a goal, value or budget change, when you need a clean read. This is about readable evidence, not about a reset.

### Advanced Intervention Rules
- Use seasonality adjustments only for short events with a major expected conversion-rate change (ideally 1-7 days); Smart Bidding already handles normal seasonality, and no reverse adjustment is needed after the event.
- Use data exclusions when a tracking or upload outage corrupted conversion data; cover the conversion delay and at least 90% of affected clicks, don't remove an applied exclusion, and avoid backfilling.
- If signal volume is thin, consolidate only when the campaigns truly share the same business goal, conversion semantics, and economics.

### Where Google's Pages Disagree
- Some Help pages (conversion-tracking pages and older Search troubleshooting pages) still describe a fixed 2-week or "7-14 day" learning phase that target, budget or goal edits reset, or recommend only small target changes. Google's Search bidding guide says target changes don't trigger Learning or reset what was learned, the learning-period page doesn't list target edits among Learning reasons and says calibration typically takes 1-2 conversion cycles, and the 2026 target-strategy FAQ says Smart Bidding reacts to large or small target changes in real time. Say the guidance conflicts and rely on the campaign's status reason and evidence.
- Google's Demand Gen performance guide says changing settings forces the campaign to redo some or all learning and that large changes can amount to a total reset; it asks for bid changes of 5-10% a week (no more than 15%), no changes during the initial learning period, and a new campaign rather than a new conversion goal on a live one. That conflicts with the 2026 target-strategy FAQ, which covers Demand Gen too; for Demand Gen, name the conflict and lean on the Demand Gen guide.
- Campaign-type pages differ: Google's Demand Gen learning page still says up to around 50 conversion events or 3 conversion cycles, and Performance Max guidance asks for at least 6 weeks on a new campaign and 1-2 weeks or one conversion cycle after a significant change. Use the page for the campaign type in question.

### What Not To Present As Fact
- Do not describe learning with a closed-form control-theory model unless a live Google-owned primary source publishes that model.
- Do not treat "7-14 days", "20% budget change", or "30-50 conversions" as universal platform rules; Google prints some of these on specific pages (conversion-tracking caution boxes, geo-experiment design guidance), but the bid strategy status reasons don't include target edits.
- For Search and Shopping, do not say a Target CPA or Target ROAS change resets learning. Do not extend that to Demand Gen, where Google's own guide says setting changes restart some or all learning.
- Do not recommend micro-conversion padding as a default answer unless the business actually wants that signal used for optimization.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads Help - Duration of the learning period for campaigns and what affects it](https://support.google.com/google-ads/answer/13020501) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Create a seasonality adjustment](https://support.google.com/google-ads/answer/9352512) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - How to find your bid strategy reports](https://support.google.com/google-ads/answer/7074568) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - How our bidding algorithms learn](https://support.google.com/google-ads/answer/10970825) | 2026-10-14 | 2026-10-15 |
| [Google Ads Help - About bid strategy statuses](https://support.google.com/google-ads/answer/6263057) | 2026-10-14 | 2026-10-14 |
| [Google Ads API Docs - BiddingStrategySystemStatus (v25)](https://developers.google.com/google-ads/api/reference/rpc/v25/BiddingStrategySystemStatusEnum.BiddingStrategySystemStatus) | 2026-07-22 | 2026-10-14 |
| [Google Ads Help - Changing conversion goals and actions used for Smart Bidding](https://support.google.com/google-ads/answer/14571185) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About data exclusions](https://support.google.com/google-ads/answer/10370710) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About seasonality adjustments](https://support.google.com/google-ads/answer/10369906) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Search campaign performance fluctuations: Changes to account or campaign settings](https://support.google.com/google-ads/answer/12265619) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Tips on measuring Smart Bidding performance](https://support.google.com/google-ads/answer/6268633) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Demand Gen performance during the learning phase](https://support.google.com/google-ads/answer/15642526) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Optimization tips for Performance Max campaign for all business types](https://support.google.com/google-ads/answer/11385582) | 2026-10-14 | 2026-10-14 |
