<!-- Generated 2026-11-13 from the knowledge base that runs Parallel AI's own agent. Do not edit by hand. -->

## REVENUE & CONVERSION TROUBLESHOOTING

Use official conversion-goal, value-based bidding, and conversion-delay guidance first. When spend is present but value is weak, assume a measurement or traffic-quality problem before assuming the algorithm is irrational.

### Problem: Low Conversions Or Revenue Despite Spend

### Step 1: Conversion And Value Integrity
- Verify the primary conversion action, attribution model, and conversion values are still correct.
- Separate proxy events from true revenue or qualified pipeline outcomes.
- Check for duplicated values, stale offline imports, or recent goal-setting changes.

### Step 2: Traffic Quality
- Review search terms, match type expansion, geo coverage, and brand vs non-brand mix.
- Check whether the campaign is buying low-intent traffic because the target is too loose or the coverage is too broad.

### Step 3: Creative And Landing Page Fit
- Verify that the ad promise matches the landing-page headline, offer, proof, and CTA.
- Look for form friction, checkout failure, slow pages, or off-message destinations.
- Use asset-combination and landing-page reports before rewriting bid strategy recommendations.

### Step 4: Business Context
- Check pricing, promo status, inventory, sales capacity, and competitive pressure.
- Compare recent market or offer changes against the timing of the conversion decline.

### Step 5: Strategy Choice
| Situation | Better next move |
|-----------|------------------|
| Thin conversion signal | Prefer Maximize conversions or Maximize conversion value while measurement stabilizes |
| Value tracking is noisy | Fix value quality before leaning harder on tROAS |
| Good traffic, weak conversion rate | Prioritize landing-page and offer work before repeated target tightening |

### Current tROAS Caveats
- Google’s June 2026 label change from "Maximize conversion value with Target ROAS" to "Target ROAS" does not change the underlying bidding behavior.
- Since August 17, 2026 (rollout completed August 27), Target CPA and Target ROAS campaigns (and Target CPC on Demand Gen) that are Limited by budget deliver toward the stated target instead of beating it, and Google doesn't adjust targets or budgets for the advertiser. If a budget-limited campaign's ROAS fell toward its target since mid-August, set the target to the return the business actually wants, keep budget headroom, and judge after 1-2 conversion cycles. Google says not to add data exclusions or bid limits only because of this change.
- Before blaming bidding for weak value, check conversion adjustments (Smart Bidding ignores adjustments made more than 7 days after the conversion) and conversion value rules (see the "Signal Injection & Tracking" reference).

### Step 6: Guardrail
- Do not recommend eCPC as a default recovery path for modern Search or Display workflows.

## How to read this reference
- Sections titled "What Google documents" or "What Google-owned sources support" are **Official**: they restate Google pages listed below.
- Sections titled "Practical", "Discipline", "Operator" or "Workflow" are **Practitioner rules**: experience, not Google policy.
- "What Not To Present As Fact" lists claims to avoid stating as settled.
- Sources for this topic were last reviewed on 2026-10-14.

## Google pages behind this reference


| Page | Google updated | We verified |
|---|---|---|
| [Google Ads Help - About target ROAS bidding](https://support.google.com/google-ads/answer/6268637) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - How to find your bid strategy reports](https://support.google.com/google-ads/answer/7074568) | 2026-03-18 | 2026-10-14 |
| [Google Ads Help - Frequently asked questions about changes to Target-based bid strategies](https://support.google.com/google-ads/answer/17125145) | 2026-10-14 | 2026-10-14 |
| [Google Ads Help - About Smart Bidding using value-based bidding for Search and Shopping](https://support.google.com/google-ads/answer/15099424) | 2026-10-14 | 2026-10-14 |
