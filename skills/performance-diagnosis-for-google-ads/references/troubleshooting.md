<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## TROUBLESHOOTING FRAMEWORK

### Official-First Triage
Start with Google Ads status and diagnostic surfaces before inventing a theory:
1. Serving eligibility: billing, policy, campaign/ad status, budget exhaustion, geo/language/schedule
2. Bid strategy status: Learning (a new strategy, or a change to its settings, budget, composition or conversion setup; on Shopping, sometimes an ad group target change; a Target CPA or Target ROAS edit is not a reason), Limited (bid limits, budget, data, low priority spend, low quality or inventory; in the interface also "bidding strategy" when a campaign would do better on a fully automated strategy), Misconfigured, Paused (no active campaigns, ad groups, keywords or budget attached) or Unavailable (Google doesn't report a status for it). For a Search campaign on Target CPA or Target ROAS, Google may also publish its own recommendation to raise a Target CPA set too low or lower a Target ROAS set too high. Read those, along with search impression share lost to rank (which reflects both bids and ad quality), before judging a target too strict; a missing recommendation doesn't show the target isn't holding the campaign back.
3. Change History and recent business/context changes
4. Conversion tracking, conversion goals, and value integrity
5. Bid strategy report, conversion delay, and recent performance outside the lag window
6. Auction or market pressure only after the account mechanics above are checked

### What Official Google Guidance Supports
- After a new strategy, a strategy setting change or a composition change, campaigns may show a Learning status while the system calibrates; Google's status codes also report Learning after budget or conversion-setting changes. On Search and Shopping, Target CPA or Target ROAS edits don't start Learning.
- Learning typically lasts a few conversion cycles (1-2 typically), faster with more conversion data; it doesn't apply to Manual CPC, and Hotel campaigns don't show bid strategy statuses.
- Seasonality adjustments are an advanced tool for expected short-lived conversion-rate swings; they are best for 1-7 day events and are less suitable for extended periods above 14 days. They are available on Search, Shopping, Demand Gen and Display with Target CPA or Target ROAS and on Performance Max and App (beta) with any strategy, not on Travel.
- Conversions can be reported up to 90 days after the click depending on the conversion window; the bid strategy report marks the days where more conversions are still expected.
- Use bid strategy reports, average target metrics, and conversion delay estimates before declaring Smart Bidding broken.
- Since March 9, 2026, Performance Planner no longer supports Display and Video campaigns or plans that use impression-share metrics, so do not use it as the current diagnostic surface for those cases.

### Safe Debugging Rules
- Do not diagnose the last few days as failure if those days sit inside the account's conversion-delay window.
- Do not jump straight to fixed percentage target edits as if they are universal Google rules.
- Do not treat attribution-model changes, tracking breaks, or value-setting changes as pure bidding problems.
- If a conversion outage polluted recent training data, use the official data-exclusion path rather than inventing a home-grown workaround: apply it as soon as the outage is found, cover the affected click dates plus the conversion delay, don't remove it once applied, and wait at least 5 days before backfilling conversions for reporting.

### Practical Debugging Tree
| IF... | THEN likely cause... | Better next move |
|-------|---------------------|------------------|
| "Learning" after a recent strategy, setting, composition, budget or conversion-setting change | System recalibration | Read the status reason and judge after 1-2 conversion cycles |
| Suddenly low spend with normal demand | Eligibility, budget, targeting, or status issue | Check serving, budget, bid status, and targeting breadth first |
| Spend present but conversions weak | Tracking, conversion goal, value quality, or landing-page issue | Validate measurement and conversion lag before changing targets |
| Short promo or sale caused a real conversion-rate jump | Forecast mismatch | Consider a short seasonality adjustment if the event fits Google's guidance |
| Major performance change after value or goal edits | Reporting / strategy input changed | Compare outside the conversion-delay window and verify included conversions |

### Ads Not Showing
- Check suspension, billing, approval, targeting, and budget eligibility first.
- Use the Ad Preview and Diagnosis workflow only after the basic serving prerequisites are confirmed.

### Performance Drop Checklist
1. Pin the exact date and scope of the drop.
2. Check Change History, conversion actions, and values.
3. Review bid strategy status and conversion delay.
4. Compare actual performance against target metrics and report surfaces.
5. Only then escalate into competitor or market explanations.

### Additional Recovery Tools
- Use seasonality adjustments only for short, major, expected conversion-rate changes that fit Google's published guidance.
- Use data exclusions when bad or missing conversion data would otherwise contaminate Smart Bidding.
- Validate conversion status, tag firing, source-of-truth counts, and click-id capture before diagnosing bidding.

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
| [Google Ads Help - About Performance Planner](https://support.google.com/google-ads/answer/9230124) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - How to find your bid strategy reports](https://support.google.com/google-ads/answer/7074568) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - About bid strategy statuses](https://support.google.com/google-ads/answer/6263057) | 2026-10-14 | 2026-10-14 |
| [Google Ads API Docs - BiddingStrategySystemStatus (v25)](https://developers.google.com/google-ads/api/reference/rpc/v25/BiddingStrategySystemStatusEnum.BiddingStrategySystemStatus) | 2026-07-22 | 2026-10-14 |
| [Google Ads Help - Use data exclusions for conversion data outages](https://support.google.com/google-ads/answer/10276486) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Find out how long it takes for your customers to convert](https://support.google.com/google-ads/answer/6239119) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Bid strategy report for automated bidding strategies](https://support.google.com/google-ads/answer/7074566) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - Search campaign performance fluctuations: Changes to account or campaign settings](https://support.google.com/google-ads/answer/12265619) | 2026-10-14 | 2026-10-14 |
